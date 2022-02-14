"""
Device Manager ---> Device ---> DEVICE SERVICE

The Device Service represents each service on the dbus that the device will be 
publishing data to. Each device service needs a unique DeviceInstance allocated 
to it by the dbus in order to publish data. A new device service is allocated a 
default name which can be customised from the GX device interface. This name will
be visible in VRM and is saved in device settings to preserve its value over 
restarts.
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
        with open('services.yml', 'r') as services_file:
            configs = yaml.safe_load(services_file)
        self._config = configs.get(serviceType)
        if self._config == None:
            logging.info("No configuration for Service %s, please update services.yml", serviceType)

    def local_settings(self):
        #local_settings = {
        #    'CustomName': ["/Settings/MqttDevices/{}/CustomName".format(self.serviceName()), 'My {} Sensor'.format(self.serviceType.capitalize()), 0, 0],
        #    'TemperatureType': ["/Settings/MqttDevices/{}/TemperatureType".format(self.serviceName()), 2, 0, 2],
        if self._config != None:
            persist = dict(filter(lambda e: e[1].get('persist', False), self._config.items()))
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
