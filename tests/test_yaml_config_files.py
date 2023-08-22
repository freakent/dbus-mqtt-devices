from logging import NullHandler
import os
import sys
import copy
test_dir = os.path.dirname(__file__)
sys.path.insert(1, os.path.join(test_dir, '..'))
sys.path.insert(1, os.path.join(test_dir, '..', 'ext', 'dbus-mqtt'))

from device_service_config import MQTTDeviceServiceConfig

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

def test_temperature_config():
    serviceName = "ts1"
    serviceType = "temperature"
    config = MQTTDeviceServiceConfig(serviceName, serviceType) 

    assert config.local_settings() == {
        'CustomName': ["/Settings/MqttDevices/{}/CustomName".format(serviceName), 'My {} Sensor'.format(serviceType.capitalize()), 0, 0],
        'TemperatureType': ["/Settings/MqttDevices/{}/TemperatureType".format(serviceName), 2, 0, 2]
    }

    #print(config.dbus_paths())
    dbus_paths = { key: val for (key, val) in list(config.dbus_paths()) }
    assert list(dbus_paths.keys()) == ['ProductId', 'CustomName', 'TemperatureType', 'Temperature', 'Pressure', 'Humidity']
    assert dbus_paths['CustomName'] == {'default': 'My Temperature Sensor', 'persist': True}
    assert dbus_paths['TemperatureType'] == {'description': 'Battery, Fridge or Generic', 'persist': True, 'default': 2, 'min': 0, 'max': 2}

