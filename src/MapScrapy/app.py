"""
Aplicacion que permite la descarga de servicios WMS de ArcGIS Server en un entorno de escritorio
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from MapScrapy.process import *
from datetime import datetime
import subprocess
import tempfile
# from MapScrapy import packages

_DATE = datetime.now()
# _ID_TEXTINPUT_URL = 'ti_ulr'
# _ID_MULTILINETEXTINPUT_METADATA = 'mti_metadata'

_TX_URL_PLACEHOLDER = 'Insert url of the service'
_TX_LOADURL_BUTTON = 'Load'
_TC_DOWNLOAD_BUTTON = 'Download'
_TC_OUTPUT_BUTTON = 'Save As'
_TC_OPENFOLDER_BUTTON = 'Open output directory'
_TITLE_ERROR = 'MapScrapy {} - Error!'.format(_DATE.year)
_TITLE_SUCCESS = 'MapScrapy {} - Success!'.format(_DATE.year)
_MESSAGE_COMPLEMENT_ERROR = 'Ocurrio el siguiente error durante el proceso:\n'
_MESSAGE_COMPLEMENT_SUCCESS = 'El proceso se ejecuto satisfactoriamente!'
_TC_CONFIG_BUTTON = 'Config'
# _TC_UPDATEURL_BUTTON = 'Obtener la URL actual'
_PID_EXE = None


class Mapscrapy(toga.App):

    def startup(self):

        outputFolder = packages.get_config_param_value(5)[0][0]
        if not outputFolder:
            outputFolder = tempfile.gettempdir()
            packages.set_config_param(5, outputFolder)


        self.pid = None
        # contenedor principal de la aplicacion
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        # contenedor primario para carga de url
        first_box = toga.Box(style=Pack(direction=ROW))
        second_box = toga.Box(style=Pack(direction=ROW))

        # Input text de la url del servicio
        self.url_input = toga.TextInput(placeholder=_TX_URL_PLACEHOLDER, style=Pack(flex=3))
        
        # Boton que permite cargar la url
        self.url_load = toga.Button(_TX_LOADURL_BUTTON, on_press=self.load_metadata, style=Pack(width=150, height=36, background_color='#fbceb5'))


        # Se agregan los elementos al contenedor primario
        first_box.add(self.url_input)
        first_box.add(self.url_load)

        # Contenedor de metadata
        # self.metadata = toga.MultilineTextInput(id=_ID_MULTILINETEXTINPUT_METADATA)
        # self.metadata.readonly = True

        self.web = toga.WebView(style=Pack(flex=1))

        # Contenedor para seleccionar el folder
        self.window = toga.Window()

        # Input text que almacenara el folder donde se almacenara el resultado
        self.output_folder = toga.TextInput(style=Pack(flex=1))
        self.output_folder.readonly = True
        self.output_folder.value = outputFolder

        # Abre ventana para seleccionar un folder de almacenamiento
        self.savefolder = toga.Button(_TC_OUTPUT_BUTTON, on_press=self.saveAs, style=Pack(width=150, height=36))
        self.config = toga.Button(_TC_CONFIG_BUTTON, on_press=self.openConfigWindow, style=Pack(width=150, height=36))

        second_box.add(self.output_folder)
        second_box.add(self.savefolder)
        second_box.add(self.config)

        # self.updateurl = toga.Button(_TC_UPDATEURL_BUTTON, on_press=self.updateUrl)

        # Boton de decarga
        self.download = toga.Button(_TC_DOWNLOAD_BUTTON, on_press=self.download, style=Pack(background_color='#52de97', height=36))

        # Boton para abril la descarga
        self.openfolder = toga.Button(_TC_OPENFOLDER_BUTTON, on_press=self.openSaveAs, style=Pack(height=36))
        # self.openfolder.enabled = False


        

        main_box.add(first_box)
        # main_box.add(self.metadata)
        main_box.add(self.web)
        main_box.add(second_box)
        # main_box.add(self.savefolder)
        # main_box.add(self.output_folder)
        # main_box.add(self.updateurl)
        main_box.add(self.download)
        main_box.add(self.openfolder)


        self.main_window = toga.MainWindow(title=self.formal_name, size=(640, 800))
        self.main_window.content = main_box
        self.main_window.show()

        self.response_pool = list()
        self.inputsConfig = dict()


        # Ventana de configuracion



    def load_metadata(self, widget):
        url = self.url_input.value
        validate = validateUrl(url=url)
        # print(validate)
        if validate['status']:
            self.web.url = url
            self.web.refresh()
        else:
            self.show_window_error(validate['message'])


    def run_loader(self, kill=False):
        global _PID_EXE
        if kill:
            if not _PID_EXE:
                return
            _PID_EXE.kill()
            _PID_EXE = None
            return
        _PID_EXE = subprocess.Popen([settings.EXE_LOADER])

    def show_window_error(self, message):
        exec_datetime = '\n' + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        msg = _MESSAGE_COMPLEMENT_ERROR + message + exec_datetime
        self.window.error_dialog(_TITLE_ERROR, msg)

    def show_window_success(self):
        exec_datetime = '\n' + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        msg = _MESSAGE_COMPLEMENT_SUCCESS + exec_datetime
        self.window.info_dialog(_TITLE_SUCCESS, msg)


    def download(self, widget):
        self.run_loader()
        self.url_input.enabled = False
        self.url_load.enabled = False
        self.savefolder.enabled = False
        self.download.enabled = False
        service = DownloadService(url=self.url_input.value, output=self.output_folder.value)
        response = service.downloadProcess()
        # print(response)
        # exec_datetime = '\n' + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        if not response['status']:
            self.run_loader(kill=True)
            # message_error =  _MESSAGE_COMPLEMENT_ERROR + response['message'] + exec_datetime
            self.show_window_error(response['message'])
            # self.window.error_dialog(_TITLE_ERROR, message_error)
        else:
            self.run_loader(kill=True)
            self.show_window_success()
            # self.openfolder.enabled = True
            # message_success =  _MESSAGE_COMPLEMENT_SUCCESS + exec_datetime
            # self.window.info_dialog(_TITLE_SUCCESS, message_success)
        packages.ins_log_data(self.url_input.value, response['status'], response['message'])
        self.url_input.enabled = True
        self.url_load.enabled = True
        self.savefolder.enabled = True
        self.download.enabled = True
        
        return response

    def saveAs(self, widget):
        try:
            folderOutput = self.window.select_folder_dialog('Select folders')
            self.output_folder.value = folderOutput[0]
            self.openfolder.enabled = True
        except Exception as e:
            print(e)

    def openSaveAs(self, widget):
        path = self.output_folder.value
        validate = validatePath(path=path)
        if validate['status']:
            os.startfile(self.output_folder.value)
        else:
            self.show_window_error(validate['message'])

    def openConfigWindow(self, widget):
        try:
            self.inputsConfig = dict()
            config_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
            for i in packages.get_config_param():
                lbl = toga.Label('{}: {}'.format(i[1].capitalize(), i[3]))
                ti = toga.TextInput(style=Pack(flex=1))
                ti.value = i[2]
                config_box.add(lbl)
                config_box.add(ti)
                self.inputsConfig[i[0]] = ti

            config_box_btn = toga.Box(style=Pack(direction=ROW))
            defaultbtn = toga.Button('Default parameters', on_press=self.defaultConfig, style=Pack(flex=1, height=36))
            logbtn = toga.Button('Registry', on_press=self.logReport, style=Pack(flex=1, height=36))
            savebtn = toga.Button('Save', on_press=self.saveConfig, style=Pack(flex=2, height=36))
            
            

            config_box_btn.add(logbtn)
            config_box_btn.add(defaultbtn)
            config_box_btn.add(savebtn)

            config_box.add(config_box_btn)

            config_window = toga.MainWindow(title='Config parameters', size=(900, 500))
            config_window.content = config_box
            config_window.show()
        except Exception as e:
            self.inputsConfig = dict()            
            self.show_window_error(str(e))


    def saveConfig(self, widget):
        try:
            for k, v in self.inputsConfig.items():
                packages.set_config_param(k, v.value)
                if k == 5:
                    self.output_folder.value = v.value
            self.show_window_success()
        except Exception as e:
            self.show_window_error(str(e))


    def defaultConfig(self, widget):
        try:
            for i in packages.get_config_default():
                self.inputsConfig[i[0]].value = i[2]
        except Exception as e:
            self.show_window_error(str(e))


    def logReport(self, widget):
        try:
            df = pd.read_sql(packages.get_log_data(getcursor=False, returnsql=True), packages.conn)
            csv = os.path.join(tempfile.gettempdir(), 'log.csv')
            df.to_csv(csv)
            os.startfile(csv)
        except Exception as e:
            self.show_window_error(str(e))





    # def updateUrl(self, widget):
    #     self.web.refresh()
    #     self.url_input.value = self.web.url
    #     print(self.web._impl._container.__dict__)


def main():
    return Mapscrapy(home_page='https://danielgis.github.io')
