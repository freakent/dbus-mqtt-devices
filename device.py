import logging
import os
import sys
import json
import dbus

VERSION=0.1

AppDir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(AppDir, 'ext', 'velib-python'))

from vedbus import VeDbusService
from settingsdevice import SettingsDevice

class MQTTDevice(object):

    def __init__(self, device_status=None, dbus_address=None, debug=False):
        self._dbus_address = dbus_address
        self._dbus_conn = (dbus.SessionBus(private=True) if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus(private=True)) \
			if dbus_address is None \
			else dbus.bus.BusConnection(dbus_address)
        self._status = device_status
        self._clientId = device_status["clientId"]
        logging.info("*** New device: %s, services: %s", self._clientId, self._status['services'])
        self._settings = SettingsDevice(bus=self._dbus_conn, supportedSettings={}, eventCallback=self._handle_changed_setting)
        self._services = {}
        self._register_device_services()

    def _handle_changed_setting(self, setting, oldvalue, newvalue):
        logging.info("setting changed, setting: %s, old: %s, new: %s", setting, oldvalue, newvalue)
        return True

    def _handle_changed_value(self, path, value):
        logging.info("value changed, path: %s, value: %s", path, value)
        #settings_path = "/Settings/Devices/{}".format(self._serviceId('temperature'))
        #logging.info("Setting before, /CustomName: %s", self._settings[settings_path+"/CustomName"])
        #self._settings[settings_path+"/CustomName"] = value
        #logging.info("Setting after, /CustomName: %s", self._settings[settings_path+"/CustomName"])
        return True

    def _get_text_for_connection(path, value):
        logging.info("Getting Text for path %s and value %s", path, value)
        return('%d rotations per minute' % value)

    def _serviceId(self, service):
        return 'mqtt_{}_{}'.format(self._clientId, service)
    
    def _servicePath(self, service):
        return 'com.victronenergy.{}.mqtt_{}'.format(service, self._clientId)

    def _register_device_services(self):
        for service in self._status["services"]:
            logging.info("Registering service %s for client %s at path %s", service, self._clientId, self._servicePath(service))

            default_custom_name = 'My Temp Sensor'

            settings_device_path = "/Settings/Devices/{}/ClassAndVrmInstance".format(self._serviceId(service))
            requested_device_instance = "{}:1".format(service) # Append the ID requested by the MQTT client
            res = self._settings.addSetting(settings_device_path, requested_device_instance, "", "")
            s, device_instance = res.get_value().split(':') # Return the allocated ID provided from dbus SettingDevices

            settings_path = "/Settings/{}".format(self._serviceId(service))
            res = self._settings.addSetting(settings_path+"/CustomName", default_custom_name, "", "")

            dbus_service = VeDbusService(self._servicePath(service), bus=self._dbus_conn)
            # Add objects required by ve-api
            dbus_service.add_path('/Management/ProcessName', 'dbus-mqtt-devices')
            dbus_service.add_path('/Management/ProcessVersion', VERSION)
            dbus_service.add_path('/Management/Connection', 'MQTT', gettextcallback=self._get_text_for_connection) # 'MQTT {}'.format(self._clientId))
            dbus_service.add_path('/DeviceInstance', device_instance)
            dbus_service.add_path('/ProductId', 0xFFFF) # ???
            dbus_service.add_path('/ProductName', "{} Sensor via MQTT".format(service).capitalize())
            dbus_service.add_path('/FirmwareVersion', VERSION)
            dbus_service.add_path('/Connected', 1)

            dbus_service.add_path('/CustomName', value=default_custom_name, writeable=True, onchangecallback=self._handle_changed_value)
            dbus_service.add_path('/TemperatureType', value=2, writeable=True)
            #dbus_service.add_path('/Temperature', value=5, description="Cabin temperature", writeable=True)
            #dbus_service.add_path('/Humidity', value=59.56, description="Cabin humidity", writeable=True)
            #dbus_service.add_path('/Pressure', value=None, description="Cabin pressure", writeable=True)
            
            logging.info("Registered Service under %s (%s)", res.get_value(), device_instance)
            self._services[service] = {"deviceInstance": device_instance, "dbusService": dbus_service}

    def device_instances(self):
        return dict( map( lambda s : (s[0], s[1]['deviceInstance']), self._services.items() ))
        