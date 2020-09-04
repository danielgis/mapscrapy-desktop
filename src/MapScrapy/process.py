import requests
import validators
import os
import uuid
import geopandas as gpd
import pandas as pd
import json
import time
from MapScrapy import settings
from MapScrapy import packages
# import packages
from requests.exceptions import ConnectionError
# import settings
import urllib3
from osgeo import ogr, osr

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_ERROR_NOT_URL = 'No se ingreso la url del servicio'
_ERROR_NOT_URL_VALID = 'La url ingresada no es valida'
_ERROR_NOT_OUTPUT = 'El directorio especificado no existe'
_ERROR_NOT_PARAMETER_PATH = 'No se ingreso el parametro ruta (path)'
_ERROR_NOT_PARAMETER_URL = 'No se ingreso el parametro url'
_CONTROLLER = 0
_RANGE = int(packages.get_config_param_value(2)[0][0])
_WAIT = int(packages.get_config_param_value(3)[0][0])
_TRIED = int(packages.get_config_param_value(4)[0][0])


def manageResponse(func):
    def newfunction(*args, **kwargs):
        response = {'status': 1, 'value': None, 'message': None}
        try:
            result = func(*args, **kwargs)
            response['value'] = result
        except ConnectionError as e:
            response['status'] = 0
            response['message'] = str(e)
        except Exception as e:
            response['status'] = 0
            response['message'] = str(e)
        finally:
            err = kwargs.get('exeraise')
            if err and not response['status']:
                raise RuntimeError(response['message'])
            return response

    return newfunction


@manageResponse
def validateUrl(*args, **kwargs):
    url = kwargs.get('url')
    if not url:
        raise RuntimeError(_ERROR_NOT_PARAMETER_URL)
    if not url:
        raise RuntimeError(_ERROR_NOT_URL)
    if not validators.url(url):
        raise RuntimeError(_ERROR_NOT_URL_VALID)
    return True


@manageResponse
def validatePath(*args, **kwargs):
    path = kwargs.get('path')
    if not path:
        raise RuntimeError(_ERROR_NOT_PARAMETER_PATH)
    if not os.path.exists(path):
        raise RuntimeError(_ERROR_NOT_OUTPUT)
    return True


def create_spatial_reference_prj_file(epsg, output):
    print(epsg)
    sr = osr.SpatialReference()
    sr.ImportFromEPSG(epsg)
    sr.MorphToESRI()
    csr_string = sr.ExportToWkt()
    with open(output, 'w') as f:
        f.write(csr_string)
        f.close()
    del f


class DownloadService(object):
    def __init__(self, *args, **kwargs):
        global _CONTROLLER
        self.objectids = list()
        self.url = kwargs.get('url')
        self.output = kwargs.get('output')

        self.data = dict()
        self.data['where'] = "1=1"
        self.data['f'] = 'geojson'
        self.data['outfields'] = '*'
        self.data['returnIdsOnly'] = 'true'

        self.paramobjectIdFieldName = 'objectIdFieldName'
        self.paramsObjectids = 'objectIds'

        # self.epsg = int()
        # _RANGE = _RANGE

        self.obectids = list()
        self.responses = list()
        self.oidname = str()
        self.output_shp = str()
        self.output_prj = str()

        _CONTROLLER = 0

    @property
    def urlQuery(self):
        return '{}/query'.format(self.url)

    def set_epsg(self):
        url = '{}?f=pjson'.format(self.url)
        response = requests.get(url)
        response2json = response.json()
        if response2json.get('extent'):
            self.data['outSR'] = response2json['extent']['spatialReference']['wkid']
        else:
            pass

    def setObjectidsParams(self):
        response = requests.post(self.urlQuery, data=self.data, verify=False)

        if response.status_code == 400:
            self.data['f'] = 'pjson'
            response = requests.post(self.urlQuery, data=self.data, verify=False)

        if response.status_code == 200:
            response_as_json = response.json()
            if not response_as_json.get(self.paramobjectIdFieldName):
                response_as_json = response_as_json['properties']

            self.oidname = response_as_json[self.paramobjectIdFieldName]
            self.objectids = [response_as_json[self.paramsObjectids][i:i + _RANGE] for i in
                              range(0, len(response_as_json['objectIds']), _RANGE)]
        else:
            raise RuntimeError(response.status_code)

    def downloadOne(self, objectids):
        global _CONTROLLER
        try:
            objectIds = ', '.join(map(lambda i: str(i), objectids))
            self.data['where'] = "{} IN ({})".format(self.oidname, objectIds)

            response = requests.post(self.urlQuery, self.data, verify=False)
            response_as_json = json.loads(response.content.decode('utf-8'))

            if self.data['f'] == 'pjson':
                from arcgis2geojson import arcgis2geojson
                response_as_json = arcgis2geojson(response_as_json)

            gdf = gpd.GeoDataFrame().from_features(response_as_json)

            self.responses.append(gdf)
        except ConnectionError as e:
            print(str(e))
            _CONTROLLER = _CONTROLLER + 1
            if _CONTROLLER < _TRIED:
                print("Intento nro 1")
                time.sleep(_WAIT)
                self.downloadOne(objectids)
            else:
                print("Se supero la cantidad maxima de intentos")
        except Exception as e:
            raise RuntimeError(str(e))
        finally:
            _CONTROLLER = 0

    def download(self):
        del self.data['returnIdsOnly']

        self.set_epsg()

        for i, oid in enumerate(self.objectids):
            self.downloadOne(oid)

        _uuid_id = uuid.uuid4()
        name_shp = 'response_{}.shp'.format(_uuid_id)
        name_prj = 'response_{}.prj'.format(_uuid_id)
        self.output_shp = os.path.join(self.output, name_shp)
        self.output_prj = os.path.join(self.output, name_prj)

        gdf_final = gpd.GeoDataFrame(pd.concat(self.responses, ignore_index=True))

        # Eliminando campos no legibles desde ArcMap
        if 'Shape.STAr' in gdf_final.columns:
            gdf_final.drop('Shape.STAr', axis=1, inplace=True)
        if 'Shape.STLe' in gdf_final.columns:
            gdf_final.drop('Shape.STLe', axis=1, inplace=True)
        if 'SHAPE.LEN' in gdf_final.columns:
            gdf_final.drop('SHAPE.LEN', axis=1, inplace=True)
        if 'SHAPE.AREA' in gdf_final.columns:
            gdf_final.drop('SHAPE.AREA', axis=1, inplace=True)

        gdf_final.to_file(self.output_shp)

        if self.data.get('outSR'):
            sr = 3857 if self.data['outSR'] == 102100 else self.data['outSR']
            create_spatial_reference_prj_file(sr, self.output_prj)

    @manageResponse
    def downloadProcess(self):
        validateUrl(url=self.url, exeraise=True)
        validatePath(path=self.output, exeraise=True)
        self.setObjectidsParams()
        self.download()
        return self.output_shp

# if __name__ == '__main__':
#     url = ''
#     output = r''
#     poo = DownloadService(url=url, output=output)
#     response = poo.downloadProcess()
#     print(response)
