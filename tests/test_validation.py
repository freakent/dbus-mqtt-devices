from logging import NullHandler
import os
import sys
import copy
test_dir = os.path.dirname(__file__)
sys.path.insert(1, os.path.join(test_dir, '..'))
sys.path.insert(1, os.path.join(test_dir, '..', 'ext', 'dbus-mqtt'))


from device_manager import MQTTDeviceManager

test_data = { 
    "valid": {
        "clientId": "fe002",
        "connected": 1,
        "version": "v1.2",
        "services": {
            "t1": "temperature"
        }
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
_self = None

def test_valid_status():
    assert MQTTDeviceManager.status_is_valid(_self, test_data["valid"]) == True, "status message should have validated OK"

def test_status_connected():
    assert MQTTDeviceManager.status_is_valid(_self, test_data["missing connected"]) == False, "Missing status.connected value should not have passed validation"
    status = copy.deepcopy(test_data["valid"])
    for test_value in [[0, True], [1, True], [2, False], [3, False], [4, False],[-2, False], [-1, False]]:
        status["connected"] = test_value[0]
        assert MQTTDeviceManager.status_is_valid(_self, status) == test_value[1], "Incorrect status.connected value of {} should {}have passed validation".format(test_value[0], "" if test_value[1] else "NOT ")    

def test_status_clientID():
    assert MQTTDeviceManager.status_is_valid(_self, test_data["missing clientId"]) == False, "Missing status.clientId value should not have passed validation"
    status = copy.deepcopy(test_data["valid"])
    for test_value in [["fe001", True], ["fe_001_t", True], ["fe:001", False], ["fe-001-t", False], ["$clientid$", False],["", False], ["NULL!", False], [None, False]]:
        status["clientId"] = test_value[0]
        print(status)
        assert MQTTDeviceManager.status_is_valid(_self, status) == test_value[1], "Incorrect status.clientId value of {} should {}have passed validation".format(test_value[0], "" if test_value[1] else "NOT ")    

def test_status_services():
    assert MQTTDeviceManager.status_is_valid(_self, test_data["missing services"]) == False, "Missing status.services value should not have passed validation"
    assert MQTTDeviceManager.status_is_valid(_self, test_data["no service dictionary"]) == False, "status.services is not a dictionary and should not have passed validation"
