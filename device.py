import logging
import os
import sys
import json

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
        self._settings = SettingsDevice(bus=self._dbus_conn)
        self._services = {}
        self._register_device_services()

    def _serviceId(self, service):
        return 'mqtt_{}_{}'.format(self._clientId, service)
    

    def _register_device_services(self):
        for service in self._status["services"]:
            res = self._settings.addSetting("Settings/Devices/{}".format(self._serviceId(service)), "{}:1".format(service), None, None)
            print(res)
            self._services[service] = 101 #this will be populated from dbus

    def device_instance(self):
        return self._services
