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
        logging.info("Deleting device %s", self.clientId)
        for service in self._services:
            logging.info("Deleting Service %s for client %s", service, self.clientId)
            self.services[service].__del__()
        del self._services


    def device_instances(self):
        return dict( map( lambda s : (s[0], s[1].device_instance), self._services.items() ))
        