"""
DEVICE MANAGER ---> Device ---> Device Service

The Device Manager subscribes to the MQTT device/+/Status topics and handles 
registration and de-registration of devices.
"""
import logging
import paho.mqtt.client as MQTT
import json
import os
import sys
import re

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
                logging.warning("Unrecognised device Connected status %s for client %s", status["clientId"])

        else:
            logging.warning('Received message on topic %s, but no action is defined', msg.topic)

    def status_is_valid(self, status):
        validFormat = "^[a-zA-Z0-9_]*$"
        isValid = True

        # Check the connected attribute
        connected = status.get('connected')
        if connected is None or connected == "":
            isValid = False
            logging.warning("status.connected can not be blank")
        else:
            if connected < 0 or connected > 1 :
                isValid = False
                logging.warning("status.connected must be either 1 or 0")

        # Check the clientId attribute
        clientId = status.get('clientId')
        if clientId is None or clientId == "":
            isValid = False
            logging.warning("status.clientId can not be blank")
        else:
            if re.search(validFormat, clientId) == None :
                isValid = False
                logging.warning("status.clientId can only contain alpha numeric characters and _ (underscores)")

        # Check the services dictionary object
        services = status.get('services')
        if connected == 1:
            if (services is None or services == "") and not isinstance(services, dict):
                isValid = False
                logging.warning("status.services must contain a dictionary of values if connected = 1")
            else:
                for service_id in services.keys():
                    if re.search(validFormat, service_id) == None :
                        isValid = False
                        logging.warning("status.services contains a service with an invalid identifier, only alpha numeric characters and _ (underscores) are allowed")
                        # Please note, service types, such as  "temperature" and "tank", are validated later by matching against services.yml

        return isValid


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
        device = self._devices.get(clientId)
        if  device is not None:
            device.__del__()
            del device
            self._devices[clientId] = None
            logging.info('**** Unregistering device %s ****', clientId)
        else:
            logging.warning('tried to remove device %s that is not registered', clientId)
