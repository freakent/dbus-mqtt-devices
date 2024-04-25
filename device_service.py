"""
Device Manager ---> Device ---> DEVICE SERVICE
                                      |
                                      v
                             Device Service Config

The Device Service represents each service on the dbus that the device will be 
publishing data to. Each device service needs a unique DeviceInstance allocated 
to it by the dbus in order to publish data. A new device service is allocated a 
default name which can be customised from the GX device interface. This name will
be visible in VRM and is saved in device settings to preserve its value over 
restarts.
"""
import logging
import os
import sys
import re
import json
import dbus
from device_service_config import MQTTDeviceServiceConfig
from version import VERSION 

AppDir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(AppDir, 'ext', 'velib_python'))
from vedbus import VeDbusService
from settingsdevice import SettingsDevice

class MQTTDeviceService(object):

    def __init__(self, device, serviceId, serviceType):
        self.device = device
        self.serviceId = serviceId # e.g. t1
        self.serviceType = serviceType # e.g. temperature
        self._config = MQTTDeviceServiceConfig(self.serviceName(), serviceType) #onchangecallback=self._handle_changed_value)
        self._dbus_conn = (dbus.SessionBus(private=True) if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus(private=True)) \
			if device.device_mgr.dbus_address is None \
			else dbus.bus.BusConnection(device.device_mgr.dbus_address)


        logging.info("Registering service %s for client %s at path %s", serviceType, device.clientId, self.serviceDbusPath())

        self._set_up_local_settings()
        
        self.device_instance = self._set_up_device_instance()

        self._set_up_dbus_paths()
            
        logging.info("Registered Service %s under DeviceInstance %s", self.serviceDbusPath(), self.device_instance)

    def __del__(self):
        #logging.info("About to unregister %s from dbus", self.serviceName())     
        if hasattr(self, '_dbus_service'):   
            self._dbus_service.__del__()  # Very important!
            del self._dbus_service
        if hasattr(self, '_settings'):   
            del self._settings 
        if hasattr(self, '_dbus_conn'):   
            del self._dbus_conn
        logging.info("Unregistered %s from dbus", self.serviceName())


    def _set_up_local_settings(self):
        #local_settings = {
         #   'CustomName': ["/Settings/MqttDevices/{}/CustomName".format(self.serviceName()), 'My {} Sensor'.format(self.serviceType.capitalize()), 0, 0],
         #   'TemperatureType': ["/Settings/MqttDevices/{}/TemperatureType".format(self.serviceName()), 2, 0, 2],
        #}
        local_settings = self._config.local_settings()
        logging.debug("Local settings for device service %s are %s", self.serviceName(), local_settings)
        self._settings = SettingsDevice(bus=self._dbus_conn, supportedSettings=local_settings, eventCallback=self._handle_changed_setting)

    def _set_up_device_instance(self):
        settings_device_path = "/Settings/Devices/{}/ClassAndVrmInstance".format(self.serviceName())
        requested_device_instance = "{}:1".format(self.serviceType) # Append the ID requested by the MQTT client
        r = self._settings.addSetting(settings_device_path, requested_device_instance, "", "")
        _s, _di = r.get_value().split(':') # Return the allocated ID provided from dbus SettingDevices
        return int(_di)

    def _set_up_dbus_paths(self):
        self._dbus_service = dbus_service = VeDbusService(self.serviceDbusPath(), bus=self._dbus_conn)
        # Add objects required by ve-api
        dbus_service.add_path('/Mgmt/ProcessName', 'dbus-mqtt-devices')
        dbus_service.add_path('/Mgmt/ProcessVersion', VERSION())
        dbus_service.add_path('/Mgmt/Connection', 'MQTT:{}'.format(self.device.clientId))
        dbus_service.add_path('/DeviceInstance', int(self.device_instance))
        dbus_service.add_path('/DeviceName', "{}:{}".format(self.device.clientId, self.serviceId))
        #dbus_service.add_path('/ProductId', 0xFFFF) # ???
        dbus_service.add_path('/ProductName', "dbus-mqtt-devices-{}:{}".format(VERSION(), self.serviceType.capitalize()))
        dbus_service.add_path('/FirmwareVersion', self.device.version)
        dbus_service.add_path('/Connected', 1)
        
        for k, v in self._config.dbus_paths():
            if v.get('format'):
                formattedText = TextFormatter(v.get('format')) # str(vv) # v.get('format').format(vv)
                textformatcallback = formattedText.format
            else:
                textformatcallback = None

            if v.get('persist', False) == True or v.get('setting', False) == True:
                changecallback = self._handle_changed_value
                value = self._settings[k]
            else:
                changecallback = None
                value = v.get('default')
            
            #if v.get('description', None) == None:
            #    logging.warn("Description for " + k + " is missing, please update services.yml")
                
            dbus_service.add_path("/"+k, value=value, description=v.get('description', None), writeable=True, gettextcallback=textformatcallback, onchangecallback=changecallback)
                
        #dbus_service.add_path('/TemperatureType', value=self._settings['TemperatureType'], writeable=True, onchangecallback=self._handle_changed_value)
        #dbus_service.add_path('/Temperature', value=None, description="Temperature C", writeable=True)
        #dbus_service.add_path('/Humidity', value=None, description="Humidity %", writeable=True)
        #dbus_service.add_path('/Pressure', value=None, description="Pressure hPa", writeable=True)


    def _getTextFormatedValue(self, value, format):
        return format.format(value)

    def _handle_changed_setting(self, setting, oldvalue, newvalue):
        logging.info("Setting changed, setting: %s, old: %s, new: %s", setting, oldvalue, newvalue)
        return True

    def _handle_changed_value(self, path, value):
        setting = re.sub("^\\/", "", path) # A regex to replace initial / for looking up settings
        logging.info("Value changed, path: %s, value: %s, setting: %s", path, value, setting)
        logging.debug("Settings: %s, %s", setting, str(self._settings._settings))
        if setting in self._settings._settings: # need to access the dict inside settings_device directly to see if it exists
                logging.debug("value changed and updating setting %s", setting)
                self._settings[setting] = value
        return True

    def serviceName(self):
        return 'mqtt_{}_{}'.format(self.device.clientId, self.serviceId)
    
    def serviceDbusPath(self): # Full path used on the dbus
        return 'com.victronenergy.{}.mqtt_{}_{}'.format(self.serviceType, self.device.clientId, self.serviceId)

class TextFormatter(object):

    def __init__(self, format):
        if format:
            self._format = format
        else:
            self._format = "{}"

    def format(self, path, value):
        #logging.info("Text format: %s, path %s, value: %s, ", self._format, path, value)
        return self._format.format(value) 
        