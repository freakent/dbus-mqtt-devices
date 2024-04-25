"""
Device Manager ---> Device ---> Device Service
                                      |
                                      v
                             DEVICE SERVICE CONFIG

The Device Service Config wraps the services.yml config file and provides the 
required dbus paths and settings to the Device Service. The services.yml file enables
the driver to support all dbus-mqtt service types.
"""
import logging
import yaml
import os
import sys
AppDir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(AppDir, 'ext', 'velib_python'))

from settingsdevice import PATH, VALUE, MINIMUM, MAXIMUM, SILENT

class MQTTDeviceServiceConfig(object):

    def __init__(self, serviceName, serviceType):
        self._serviceType = serviceType 
        self._serviceName = serviceName
        logging.info("About to open config file")               
        try:                                                    
            base = os.path.dirname(os.path.realpath(__file__))  
            with open(os.path.join(base, 'services.yml'), 'r') as services_file:
                configs = yaml.safe_load(services_file)                         
            self._config = configs.get(serviceType)                             
            if self._config == None:                                            
                logging.info("No configuration for Service %s, please update services.yml", serviceType)
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
            # filtering out any attributes in the service definition that are not settings ("persist" is deprecated in favour of "setting")  
            persist = dict( filter(lambda e: e[1].get('persist', False) == True or e[1].get('setting', False) == True, self._config.items()  ) )
            settings = {k: self._config_to_setting(k, v) for k, v in persist.items()}
            return settings
        else:
            return None
        

    def _config_to_setting(self, key, values):
        setting = [None, None, None, None]
        setting[PATH] = "/Settings/MqttDevices/{}/{}".format(self._serviceName, key)
        setting[VALUE] = values.get('default', None) 
        setting[MINIMUM] = values.get('min',0)  
        setting[MAXIMUM] = values.get('max', 0)
        return(setting)


    def dbus_paths(self):
        # tt = {'path': '/TemperatureType', 'value': self._settings['TemperatureType'], 'writeable': True, 'onchangecallback': self._handle_changed_value}
        if self._config != None:
            #paths = {k: self._config_to_path(k, v, settings, callback) for k, v in self._config.items()}
            return self._config.items()
        else:
            return None


    def _config_to_path(self, key, values, settings, callback):
        p = {}
        p["path"] = "/" + key
        p["writable"] = True
        if values.get("persist", False) == True or values.get("setting", False) == True:
            p["value"] = settings[key]
        else:
            p["value"] = None 

        p["description"] = values.get("description", None)
        p["onchangecallback"] = callback
        return p
