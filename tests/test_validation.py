from logging import NullHandler
import os
import sys
import copy
test_dir = os.path.dirname(__file__)
sys.path.insert(1, os.path.join(test_dir, '..'))
sys.path.insert(1, os.path.join(test_dir, '..', 'ext', 'dbus-mqtt'))

from device_manager import MQTTDeviceManager

class Mock(object):
    def __init__(self):
        self.service_types = ['temperature', 'tank', 'pvinverter']


test_data = { 
    "valid": {
        "clientId": "fe002",
        "connected": 1,
        "version": "v1.2",
        "services": {
            "te1": "temperature",
            "te2": "temperature",
            "ta1": "tank"
        }
    }, 
    "valid disconnect": {
        "clientId": "fe002",
        "connected": 0,
    }, 
    "missing connected": {
        "clientId": "fe002",
        "connect": 1,
        "version": "v1.2",
        "services": {
            "t1": "temperature"
        }
    },
    "missing clientId": {
        "clientid": "fe002",
        "connected": 1,
        "version": "v1.2",
        "services": {
            "t1": "temperature"
        }
    },
    "missing services": {
        "clientId": "fe002",
        "connected": 1,
        "version": "v1.2",
    },
    "no service dictionary": {
        "clientId": "fe002",
        "connected": 1,
        "version": "v1.2",
        "services": None
    }
}
_self = Mock()

def test_valid_status():
    assert MQTTDeviceManager._status_is_valid(_self, test_data["valid"]) == True, "connect status message should have validated OK"
    assert MQTTDeviceManager._status_is_valid(_self, test_data["valid disconnect"]) == True, "disconnect status message should have validated OK"

def test_status_connected():
    assert MQTTDeviceManager._status_is_valid(_self, test_data["missing connected"]) == False, "Missing status.connected value should not have passed validation"
    status = copy.deepcopy(test_data["valid"])
    for test_value in [[0, True], [1, True], [2, False], [3, False], [4, False],[-2, False], [-1, False]]:
        status["connected"] = test_value[0]
        assert MQTTDeviceManager._status_is_valid(_self, status) == test_value[1], "Incorrect status.connected value of {} should {}have passed validation".format(test_value[0], "" if test_value[1] else "NOT ")    

def test_status_clientID():
    assert MQTTDeviceManager._status_is_valid(_self, test_data["missing clientId"]) == False, "Missing status.clientId value should not have passed validation"
    status = copy.deepcopy(test_data["valid"])
    for test_value in [["fe001", True], ["fe_001_t", True], ["fe:001", False], ["fe-001-t", False], ["$clientid$", False],["", False], ["NULL!", False], [None, False]]:
        status["clientId"] = test_value[0]
        print(status)
        assert MQTTDeviceManager._status_is_valid(_self, status) == test_value[1], "Incorrect status.clientId value of {} should {}have passed validation".format(test_value[0], "" if test_value[1] else "NOT ")    

def test_status_services():
    assert MQTTDeviceManager._status_is_valid(_self, test_data["missing services"]) == False, "Missing status.services value should not have passed validation"
    assert MQTTDeviceManager._status_is_valid(_self, test_data["no service dictionary"]) == False, "status.services is not a dictionary and should not have passed validation"
    status = copy.deepcopy(test_data["valid"])
    for test_value in [ [{"t1": "temperature"}, True],  [{"t_1": "tank"}, True],  [{"t:001": "tank"}, False],  [{"sp1": "spicyness"}, False], [["t1", "t2", "t3"], False] ]:
        status["services"] = test_value[0]
        print(status)
        assert MQTTDeviceManager._status_is_valid(_self, status) == test_value[1], "Incorrect status.services value of {} should {}have passed validation".format(test_value[0], "" if test_value[1] else "NOT ")    

