"""
Device Manager ---> DEVICE ---> Device Service

The Device represents the actual client device sending data to the dbus over 
MQTT. Each device can support multiple device services, either of the same of 
different types.
"""
import logging
import os
import sys

#AppDir = os.path.dirname(os.path.realpath(__file__))
#sys.path.insert(1, os.path.join(AppDir, 'ext', 'velib-python'))

from device_service import MQTTDeviceService

class MQTTDevice(object):

    def __init__(self, device_mgr=None, device_status=None):
        self.device_mgr = device_mgr
        self.clientId = device_status["clientId"]
        self._status = device_status
        logging.info("*** New device: %s, services: %s", self.clientId, self._status['services'])

        self._services = {}
        for service in self._status["services"]:
            logging.info("Registering Service %s for client %s", service, self.clientId)
            device_service = MQTTDeviceService(self, service)
            self._services[service] = device_service


    def __del__(self):
        for service in self._services:
            self._services[service].__del__()
            logging.info("Removed Service %s from client %s", service, self.clientId)
        del self._services


    def device_instances(self):
        return dict( map( lambda s : (s[0], s[1].device_instance), self._services.items() ))
        