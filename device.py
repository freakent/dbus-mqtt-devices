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
        self.clientId = device_status.get("clientId")
        self.version = device_status.get("version")
        self._status = device_status
        logging.info("**** Registering device: %s, services: %s ****", self.clientId, self._status['services'])

        self.services = {}
        if self._status.get("services") is not None and type(self._status.get("services")) is dict:
            for id, service in self._status["services"].items():
                logging.info("Registering Service %s for client %s", service, self.clientId)
                device_service = MQTTDeviceService(self, id, service)
                self.services[id] = device_service
        else:
            logging.warning("Device registration for client %s did not contain a valid services object", self.clientId)


    def __del__(self):
        if hasattr(self, 'services'):
            for serviceId in self.services:
                self.services[serviceId].__del__()
                logging.info("Removed Service %s from client %s", serviceId, self.clientId)
            del self.services


    def dbus_conn(self):
        return self.device_mgr.dbus_conn
        