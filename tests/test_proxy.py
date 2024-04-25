from logging import NullHandler
import os
import sys
import copy
test_dir = os.path.dirname(__file__)
sys.path.insert(1, os.path.join(test_dir, '..'))

import unittest
from device_proxy import MQTTDeviceProxy

#sys.path.insert(1, os.path.join(test_dir, '..', 'ext', 'dbus-mqtt'))

#from device_manager import MQTTDeviceManager

class MockMQTT(object):
    def __init__(self):
        self.published = []
    
    def publish(self, topic, payload):
        self.published.append({"topic": topic, "payload": payload})
    
    def topic_matches_sub(self, sub, topic):
        if topic == "W/12345/temperature/4":
            return True 
    


source_data = {
    "topicPath": "W/12345/temperature/4",
    "values": { 
        "Temperature" : 23,
        "Pressure": 900,
        "Humidity": 56
    }
}

target_data = [
    { "key": "W/12345/temperature/4/Temperature", "value" : 23 },
    { "key": "W/12345/temperature/4/Pressure", "value": 900 },
    { "key": "W/12345/temperature/4/Humidity", "value": 56 } 
]

published_data = [
    { "topic": "W/12345/temperature/4/Temperature", "payload": {"value": 23} },
    { "topic": "W/12345/temperature/4/Pressure", "payload": {"value": 900} },
    { "topic": "W/12345/temperature/4/Humidity", "payload": {"value": 56} }
]

invalid_data = [ 
    { "data": {"value": 300}, "errs": 2 },
    { "data": {"temperature": 100}, "errs": 2 },
    { "data": [ { "temperature": 100, "pressure": 55}, { "temperature": 75, "pressure": 76} ],  "errs": 3 },
    { "data": { "topic_path": "temperature", "values": {"temperature": 23} }, "errs": 2 }

] 
class TestProxy(unittest.TestCase):
    def test_transform(self):
        proxy = MQTTDeviceProxy(MockMQTT())
        self.assertEqual(proxy.transform(source_data), target_data)

    def test_publish(self):
        mqtt = MockMQTT()
        proxy = MQTTDeviceProxy(mqtt)
        proxy.publish(source_data)
        self.assertEqual(len(mqtt.published), 3)
        for p in published_data:
            self.assertTrue(p in mqtt.published, "Could not find {} in {}".format(p, mqtt.published))

    def test_validation(self):
        proxy = MQTTDeviceProxy(MockMQTT())
        self.assertTrue(len(proxy.validate(source_data)) == 0)

        for t in invalid_data:
            errs = proxy.validate(t["data"])
            self.assertTrue(len(errs) == t["errs"], "payload {} had {} errors: {}".format(t["data"], len(errs), errs ))
        
