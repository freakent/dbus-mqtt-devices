"""
Device Manager ---> Device ---> Device Service
                                      |
                                      v
                             DEVICE SERVICE CONFIG

The Device Service Config wraps the services.yml config file and provides the 
required dbus paths and settings to the Device Service. The services.yml file enables
the driver to support all dbus-mqtt service types.
"""
import configparser
import logging
import os
import sys
from glob import glob
from pathlib import Path 

AppDir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(AppDir, 'ext', 'velib_python'))

from settingsdevice import PATH, VALUE, MINIMUM, MAXIMUM, SILENT

class MQTTDeviceServiceConfig(object):

    def __init__(self, serviceName, serviceType):
        self._serviceType = serviceType 
        self._serviceName = serviceName
        self._config = configparser.ConfigParser()
        logging.info("About to open config file")               
        try:                                
            base = os.path.dirname(os.path.realpath(__file__))  
            self._config.read(os.path.join(base, "services", serviceType + ".ini"))
            if self._config == []:                                            
                logging.info("No configuration for Service %s, please check service configurations in ./services", serviceType)
                self._config = None
        except IOError as e:                                                                            
            logging.error("I/O error(%s): %s", e.errno, e.strerror)
        except: #handle other exceptions such as attribute errors                                       
            logging.error("Unexpected error: %s", sys.exc_info()[0])

    def value(self, key):
        if self._config and self._config.get(key, None) != None:
            return self._config[key].get("default", None)
        else:
            return None

    def local_settings(self):
        #local_settings = {
        #    'CustomName': ["/Settings/MqttDevices/{}/CustomName".format(self.serviceName()), 'My {} Sensor'.format(self.serviceType.capitalize()), 0, 0],
        #    'TemperatureType': ["/Settings/MqttDevices/{}/TemperatureType".format(self.serviceName()), 2, 0, 2],
        if self._config != None:
            print("this is what we found", self._config)
            persist = filter(lambda s: self._config[s].getboolean("persist", False), self._config.sections())
            settings = {k: self._config_to_setting(k, self._config[k]) for k in persist}
            return settings
        else:
            return None
        

    def _config_to_setting(self, key, values):
        setting = [None, None, None, None]
        setting[PATH] = "/Settings/MqttDevices/{}/{}".format(self._serviceName, key)
        default = values.get('default', None) 
        setting[VALUE] = values.getint('default', None) if default.isnumeric() else default  
        setting[MINIMUM] = values.getint('min',0)  
        setting[MAXIMUM] = values.getint('max', 0)
        return(setting)


    def dbus_paths(self):
        # tt = {'path': '/TemperatureType', 'value': self._settings['TemperatureType'], 'writeable': True, 'onchangecallback': self._handle_changed_value}
        if self._config != None:
            #paths = {k: self._config_to_path(k, v, settings, callback) for k, v in self._config.items()}
            return filter(lambda c: c[0] not in ("DEFAULT", "Service"), self._config.items())   
        else:
            return None


    def _config_to_path(self, key, values, settings, callback):
        p = {}
        p["path"] = "/" + key
        p["writable"] = True
        if values.getboolean("persist", False) == True:
            p["value"] = settings[key]
        else:
            p["value"] = None 
        p["description"] = values.get("description", None)
        p["onchangecallback"] = callback
        return p
    
    @staticmethod
    def serviceTypes():
        base_path=os.path.dirname(os.path.realpath(__file__)) 
        return list(map(lambda f: Path(f).stem, glob(os.path.join(base_path, "services/*.ini"))))
