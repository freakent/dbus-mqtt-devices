import logging
import paho.mqtt.client as MQTT
import json
import os
import sys

AppDir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(AppDir, 'ext', 'dbus-mqtt'))
from mqtt_gobject_bridge import MqttGObjectBridge

clientId = "dbus_mqtt_device_manager"

class MQTTDeviceManager(MqttGObjectBridge):

    def __init__(self, mqtt_server=None, ca_cert=None, user=None, passwd=None, dbus_address=None, init_broker=False, debug=False):
        self._dbus_address = dbus_address
        self._devices = {}
        MqttGObjectBridge.__init__(self, mqtt_server, clientId, ca_cert, user, passwd, debug)

    # RC is the Connection Result 0: Connection successful 1: Connection refused - incorrect protocol version 
    # 2: Connection refused - invalid client identifier 3: Connection refused - server unavailable 
    # 4: Connection refused - bad username or password 5: Connection refused - not authorised 
    # 6-255: Currently unused.
    def _on_connect(self, client, usedata, flags, rc): 
        MqttGObjectBridge._on_connect(self, client, userdata, dict, rc)
        logging.info('[Connected] Result code {}'.format(rc))
        if rc == 0:
            self._subscribe_to_device_topic()
    
    def _on_message(self, client, userdata, msg):
        MqttGObjectBridge._on_message(self, client, userdata, msg)
        print(msg.topic+" "+str(msg.payload))
        if self._mqtt.topic_matches_sub(msg.top, "device/+/Status"):
            logging.info("Received device status message")
            self._process_device(json.loads(msg.payload))

    def _subscribe_to_device_topic(self):
        mqtt = self._mqtt
        mqtt.subscribe("device/+/Status")

    def _process_device(self, status):
        device = self._devices.get(status.deviceId)
        if device is None:
            # create a new device
            self._devices[status.deviceId] = {}
        topic = "device/" + status.deviceId + "/DeviceInstance"
        self._mqtt.publish(topic, '{"Temperature": 399}')
