import logging
import os
import sys
import dbus

#from dbus_mqtt_devices import VERSION
VERSION=0.1

AppDir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(AppDir, 'ext', 'velib-python'))
from vedbus import VeDbusService
from settingsdevice import SettingsDevice

class MQTTDeviceService(object):

    def __init__(self, device, service):
        self.service = service
        self.device = device
        
        logging.info("Registering service %s for client %s at path %s", service, device.clientId, self.servicePath(service))

        self._dbus_conn = (dbus.SessionBus(private=True) if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus(private=True)) \
			if device.device_mgr.dbus_address is None \
			else dbus.bus.BusConnection(device.device_mgr.dbus_address)

        self._set_up_local_settings()
        
        self._set_up_device_instance()

        self._set_up_dbus_paths()
            
        logging.info("Registered Service under %s (%s)", self.servicePath(service), self.device_instance)

    def _set_up_local_settings(self):
        local_settings = {
            'CustomName': ["/Settings/MqttDevices/{}/CustomName".format(self.serviceId(self.service)), 'My Temp Sensor', 0, 0],
            'TemperatureType': ["/Settings/MqttDevices/{}/TemperatureType".format(self.serviceId(self.service)), 2, 0, 2],
        }
        self._settings = SettingsDevice(bus=self._dbus_conn, supportedSettings=local_settings, eventCallback=self._handle_changed_setting)

    def _set_up_device_instance(self):
        settings_device_path = "/Settings/Devices/{}/ClassAndVrmInstance".format(self.serviceId(self.service))
        requested_device_instance = "{}:1".format(self.service) # Append the ID requested by the MQTT client
        r = self._settings.addSetting(settings_device_path, requested_device_instance, "", "")
        s, self.device_instance = r.get_value().split(':') # Return the allocated ID provided from dbus SettingDevices

    def _set_up_dbus_paths(self):
        self._dbus_service = dbus_service = VeDbusService(self.servicePath(self.service), bus=self._dbus_conn)
        # Add objects required by ve-api
        dbus_service.add_path('/Mgmt/ProcessName', 'dbus-mqtt-devices')
        dbus_service.add_path('/Mgmt/ProcessVersion', VERSION)
        dbus_service.add_path('/Mgmt/Connection', 'MQTT:{}'.format(self.device.clientId))
        dbus_service.add_path('/DeviceInstance', self.device_instance)
        dbus_service.add_path('/DeviceName', self.device.clientId)
        dbus_service.add_path('/ProductId', 0xFFFF) # ???
        dbus_service.add_path('/ProductName', "{} Sensor via MQTT".format(self.service.capitalize()))
        dbus_service.add_path('/FirmwareVersion', VERSION)
        dbus_service.add_path('/Connected', 1)
        dbus_service.add_path('/CustomName', value=self._settings['CustomName'], writeable=True, onchangecallback=self._handle_changed_value)
        
        dbus_service.add_path('/TemperatureType', value=self._settings['TemperatureType'], writeable=True, onchangecallback=self._handle_changed_value)
        dbus_service.add_path('/Temperature', description="Temperature C", writeable=True)
        dbus_service.add_path('/Humidity', description="Humidity m3", writeable=True)
        #dbus_service.add_path('/Pressure', value=None, description="Cabin pressure", writeable=True)


    def _handle_changed_setting(self, setting, oldvalue, newvalue):
        logging.info("setting changed, setting: %s, old: %s, new: %s", setting, oldvalue, newvalue)
        return True

    def _handle_changed_value(self, path, value):
        logging.info("value changed, path: %s, value: %s", path, value)
        setting = path.replace('/', '')
        if self._settings[setting]:
            self._settings[setting] = value
        return True

    def serviceId(self, service):
        return 'mqtt_{}_{}'.format(self.device.clientId, service)
    
    def servicePath(self, service): # Full path used on the dbus
        return 'com.victronenergy.{}.mqtt_{}'.format(service, self.device.clientId)
        