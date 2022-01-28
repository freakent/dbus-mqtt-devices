import logging
import os
import sys
import json

AppDir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(AppDir, 'ext', 'velib-python'))

class MQTTDevice(object):

    def __init__(self, device_status=None, dbus_address=None, debug=False):
        self._dbus_address = dbus_address
        self._status = device_status
        self._clientId = device_status["clientId"]
        self._services = {}
        self._register_device_services()

    def _serviceId(self, service):
        return 'mqtt_{}_{}'.format(self._clientId, service)
    

    def _register_device_services(self):
        for service in device_status["services"]:
            self._services[service] = 101 #this will be poulated from dbus

    def device_instance(self):
        return {"temperature": 333} # self._services
