import logging
import os
import sys
import json
import dbus

AppDir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(AppDir, 'ext', 'velib-python'))

from vedbus import VeDbusService
from settingsdevice import SettingsDevice

class MQTTDevice(object):

    def __init__(self, device_status=None, dbus_address=None, debug=False):
        self._dbus_address = dbus_address
        self._dbus_conn = (dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()) \
			if dbus_address is None \
			else dbus.bus.BusConnection(dbus_address)
        self._status = device_status
        self._clientId = device_status["clientId"]
        self._settings = SettingsDevice(bus=self._dbus_conn, supportedSettings={}, eventCallback=self._handle_changed_setting)
        self._services = {}
        self._register_device_services()

    def _handle_changed_setting(setting, oldvalue, newvalue):
        print("setting changed, setting: {}, old: {}, new: {}".format(setting, oldvalue, newvalue))

    def _serviceId(self, service):
        return 'mqtt_{}_{}'.format(self._clientId, service)
    
    def _servicePath(self, service):
        return 'com.victronenergy.{}.mqtt{}'.format(service, self._clientId)

    def _register_device_services(self):
        for service in self._status["services"]:
            logging.info("Registering service {} for client {}", service, self._clientId)

            path = "/Settings/Devices/{}/ClassAndVrmInstance".format(self._serviceId(service))
            requested_id = "{}:1".format(service)
            res = self._settings.addSetting(path, requested_id, "", "")
            s, device_instance = res.get_value().split(':')

            dbus_service = VeDbusService(self._servicePath(service), bus=self._dbus_conn)
            # Add objects required by ve-api
            dbus_service.add_path('/Management/ProcessName', 'dbus-mqtt-devices')
            dbus_service.add_path('/Management/ProcessVersion', VERSION)
            dbus_service.add_path('/Management/Connection', 'mqtt{}'.format(self._clientId))
            dbus_service.add_path('/DeviceInstance', device_instance)
            dbus_service.add_path('/ProductId', 0xFFFF) # ???
            dbus_service.add_path('/ProductName', "{} Sensor via MQTT".format(service))
            dbus_service.add_path('/FirmwareVersion', None)
            dbus_service.add_path('/Connected', 1)

            dbus_service.add_path('/CustomName', value='FreakEnt Temp Sensor', writeable=True)
            dbus_service.add_path('/TemperatureType', value=2, writeable=True)
            dbus_service.add_path('/Temperature', value=5, description="Cabin temperature", writeable=True)
            dbus_service.add_path('/Humidity', value=59.56, description="Cabin humidity", writeable=True)
            #dbus_service.add_path('/Pressure', value=None, description="Cabin pressure", writeable=True)
            
            logging.info("Registered Service under %s (%s)", res.get_value(), device_instance)
            self._services[service] = {"deviceInstance": device_instance, "dbusService": dbus_service}

    def device_instance(self):
        return self._services
