"""
Aplicacion que permite la descarga de servicios WMS de ArcGIS Server en un entorno de escritorio
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from MapScrapy.process import *
from datetime import datetime


_DATE = datetime.now()
_ID_TEXTINPUT_URL = 'ti_ulr'
_ID_MULTILINETEXTINPUT_METADATA = 'mti_metadata'

_TX_URL_PLACEHOLDER = 'Inserte url del servicio'
_TX_LOADURL_BUTTON = 'cargar'
_TC_DOWNLOAD_BUTTON = 'Descargar'
_TC_OUTPUT_BUTTON = 'Guardar'
_TC_OPENFOLDER_BUTTON = 'Abrir directorio de salida'
_TITLE_ERROR = 'MapScrapy {} - Error!'.format(_DATE.year)
_TITLE_SUCCESS = 'MapScrapy {} - Success!'.format(_DATE.year)
_MESSAGE_COMPLEMENT_ERROR = 'Ocurrio el siguiente error durante el proceso:\n'
_MESSAGE_COMPLEMENT_SUCCESS = 'El proceso se ejecuto satisfactoriamente!'


class Mapscrapy(toga.App):

    def startup(self):
# contenedor principal de la aplicacion
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        # contenedor primario para carga de url
        first_box = toga.Box(style=Pack(direction=ROW))
        second_box = toga.Box(style=Pack(direction=ROW))

        # Input text de la url del servicio
        self.url_input = toga.TextInput(id=_ID_TEXTINPUT_URL, placeholder=_TX_URL_PLACEHOLDER, style=Pack(flex=3))
        
        # Boton que permite cargar la url
        self.url_load = toga.Button(_TX_LOADURL_BUTTON, on_press=self.load_metadata, style=Pack(width=150, height=36))


        # Se agregan los elementos al contenedor primario
        first_box.add(self.url_input)
        first_box.add(self.url_load)

        # Contenedor de metadata
        self.metadata = toga.MultilineTextInput(id=_ID_MULTILINETEXTINPUT_METADATA)
        self.metadata.readonly = True

        # Contenedor para seleccionar el folder
        self.window = toga.Window()

        # Input text que almacenara el folder donde se almacenara el resultado
        self.output_folder = toga.TextInput(style=Pack(flex=1))
        self.output_folder.readonly = True

        # Abre ventana para seleccionar un folder de almacenamiento
        self.savefolder = toga.Button(_TC_OUTPUT_BUTTON, on_press=self.saveAs, style=Pack(width=150, height=36))

        second_box.add(self.output_folder)
        second_box.add(self.savefolder)

        # Boton de decarga
        self.download = toga.Button(_TC_DOWNLOAD_BUTTON, on_press=self.download)

        # Boton para abril la descarga
        self.openfolder = toga.Button(_TC_OPENFOLDER_BUTTON, on_press=self.openSaveAs)
        self.openfolder.enabled = False


        

        main_box.add(first_box)
        main_box.add(self.metadata)
        main_box.add(second_box)
        # main_box.add(self.savefolder)
        # main_box.add(self.output_folder)
        main_box.add(self.download)
        main_box.add(self.openfolder)


        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

    def load_metadata(self, widget):
        self.metadata.value = self.url_input.value

    def download(self, widget):
        self.url_input.enabled = False
        self.url_load.enabled = False
        self.savefolder.enabled = False
        self.download.enabled = False
        service = DownloadService(url=self.url_input.value, output=self.output_folder.value)
        response = service.downloadProcess()
        exec_datetime = '\n' + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        if not response['status']:
            message_error =  _MESSAGE_COMPLEMENT_ERROR + response['message'] + exec_datetime
            self.window.error_dialog(_TITLE_ERROR, message_error)
        else:
            message_success =  _MESSAGE_COMPLEMENT_SUCCESS + exec_datetime
            self.window.info_dialog(_TITLE_SUCCESS, message_success)
        self.url_input.enabled = True
        self.url_load.enabled = True
        self.savefolder.enabled = True
        self.download.enabled = True
        self.openfolder.enabled = True
        
        return response

    def saveAs(self, widget):
        folderOutput = self.window.select_folder_dialog('Seleccionar folderss')
        self.output_folder.value = folderOutput[0]

    def openSaveAs(self, widget):
        os.startfile(self.output_folder.value)




def main():
    return Mapscrapy()
