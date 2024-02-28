from logging import NullHandler
import os
import sys
import copy
test_dir = os.path.dirname(__file__)
sys.path.insert(1, os.path.join(test_dir, '..'))

import unittest
#from device import MQTTDevice
from helpers import build_dbus_payload

portal_id = "ABC123XYZ"

status = {
    "clientId": "fe002", "connected": 1, "version": "v2.3", "services": {"t1": "temperature", "t2": "temperature", "tk1": "tank" } 
}

device_services = {
    "t1": { "device_instance": 1, "service_type": "temperature" }, 
    "t2": { "device_instance": 2, "service_type": "temperature" }, 
    "tk1": { "device_instance": 1, "service_type": "tank" }
}

dbus_payload = {
    "portalId": portal_id,
    "deviceInstance": { "t1": 1, "t2":2, "tk1": 1 },
    "topicPath": {
        "t1": { "N": "N/{}/temperature/1".format(portal_id), "R": "R/{}/temperature/1".format(portal_id), "W": "W/{}/temperature/1".format(portal_id)}, 
        "t2": { "N": "N/{}/temperature/2".format(portal_id), "R": "R/{}/temperature/2".format(portal_id), "W": "W/{}/temperature/2".format(portal_id)}, 
        "tk1": { "N": "N/{}/tank/1".format(portal_id),       "R": "R/{}/tank/1".format(portal_id),        "W": "W/{}/tank/1".format(portal_id)}
    }
}


class TestTopicPath(unittest.TestCase):
    def test_build_dbus_payload(self):     
        self.maxDiff = None  
        self.assertEqual(build_dbus_payload(portal_id, device_services), dbus_payload )

