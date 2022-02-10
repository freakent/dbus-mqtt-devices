import logging
import paho.mqtt.client as MQTT
import json
import os
import sys

from device import MQTTDevice

AppDir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(AppDir, 'ext', 'dbus-mqtt'))
from mqtt_gobject_bridge import MqttGObjectBridge

CLIENTID = "dbus_mqtt_device_manager" # the client id this process will connect to MQTT with

class MQTTDeviceManager(MqttGObjectBridge):

    def __init__(self, mqtt_server=None, ca_cert=None, user=None, passwd=None, dbus_address=None, init_broker=False, debug=False):
        self.dbus_address = dbus_address
        self.debug = debug
        self._devices = {}
        MqttGObjectBridge.__init__(self, mqtt_server, CLIENTID, ca_cert, user, passwd, debug)

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
            status = json.loads(msg.payload)
            logging.info("Received device status message %s", status)
            
            if status['connected'] == 1:
                self._process_device(status)
            elif status['connected'] == 0:
                self._remove_device(status)
            else:
                logging.info("Unrecognised device Connected status %s for client %s", status["clientId"])

        else:
            logging.warning('Received message on topic %s, but no action is defined', msg.topic)

    def _subscribe_to_device_topic(self):
        mqtt = self._client
        mqtt.subscribe("device/+/Status")

    def _process_device(self, status):
        mqtt = self._client
        clientId = status["clientId"] # the device's client id
        device = self._devices.get(clientId)
        if device is None:
            # create a new device
            self._devices[clientId] = device = MQTTDevice(device_mgr=self, device_status=status)
        topic = "device/{}/DeviceInstance".format(clientId)
        res = mqtt.publish(topic, json.dumps(device.device_instances()))
        logging.info('publish %s to %s, status is %s', device.device_instances(), topic, res.rc)
    
    def _remove_device(self, status):
        clientId = status["clientId"] # the device's client id
        del self._devices[clientId]
        logging.info('Device %s has been removed', clientId)
