import logging
import paho.mqtt.client as MQTT
import json
import os
import sys

from device import MQTTDevice

AppDir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(AppDir, 'ext', 'dbus-mqtt'))
from mqtt_gobject_bridge import MqttGObjectBridge

clientId = "dbus_mqtt_device_manager"

class MQTTDeviceManager(MqttGObjectBridge):

    def __init__(self, mqtt_server=None, ca_cert=None, user=None, passwd=None, dbus_address=None, init_broker=False, debug=False):
        self._dbus_address = dbus_address
        self._debug = debug
        self._devices = {}
        MqttGObjectBridge.__init__(self, mqtt_server, clientId, ca_cert, user, passwd, debug)

    # RC is the Connection Result 0: Connection successful 1: Connection refused - incorrect protocol version 
    # 2: Connection refused - invalid client identifier 3: Connection refused - server unavailable 
    # 4: Connection refused - bad username or password 5: Connection refused - not authorised 
    # 6-255: Currently unused.
    def _on_connect(self, client, userdata, flags, rc): 
        MqttGObjectBridge._on_connect(self, client, userdata, dict, rc)
        logging.info('[Connected] Result code {}'.format(rc))
        if rc == 0:
            self._subscribe_to_device_topic()
    
    def _on_message(self, client, userdata, msg):
        MqttGObjectBridge._on_message(self, client, userdata, msg)

        if MQTT.topic_matches_sub("device/+/Status", msg.topic):
            logging.info("Received device status message")
            self._process_device(json.loads(msg.payload))
        else:
            logging.info('Received message on topic %s, but no action ifs defined', msg.topic)

    def _subscribe_to_device_topic(self):
        mqtt = self._client
        mqtt.subscribe("device/+/Status")

    def _process_device(self, status):
        mqtt = self._client
        clientId = status["clientId"]
        device = self._devices.get(clientId)
        if device is None:
            # create a new device
            self._devices[clientId] = device = MQTTDevice(device_status=status, dbus_address=self._dbus_address, debug=self._debug)
        topic = "device/" + clientId + "/DeviceInstance"
        res = mqtt.publish(topic, json.dumps(device.device_instance()))
        logging.info('publish %s to %s, status is %s', device.device_instance(), topic, res.rc)
