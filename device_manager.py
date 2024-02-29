"""
DEVICE MANAGER ---> Device ---> Device Service
                                      |
                                      v
                             Device Service Config

The Device Manager subscribes to the MQTT device/+/Status topics and handles 
registration and de-registration of devices.
"""
import logging
import paho.mqtt.client as MQTT
import dbus
import json
import os
import sys
import re
import yaml

from device import MQTTDevice
from device_proxy import MQTTDeviceProxy
from helpers import build_dbus_payload, device_instances

AppDir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(AppDir, 'ext', 'dbus-mqtt'))
from mqtt_gobject_bridge import MqttGObjectBridge
sys.path.insert(1, os.path.join(AppDir, 'ext', 'velib_python'))
from vedbus import VeDbusItemImport


CLIENTID = "dbus_mqtt_device_manager" # the client id this process will connect to MQTT with

class MQTTDeviceManager(MqttGObjectBridge):

    def __init__(self, mqtt_server=None, ca_cert=None, user=None, passwd=None, dbus_address=None, init_broker=False, debug=False):
        self._dbus_conn = (dbus.SessionBus(private=True) if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus(private=True)) \
			if dbus_address is None \
			else dbus.bus.BusConnection(dbus_address)
        self.dbus_address = dbus_address
        self.portalId = self._lookup_portalId()
        self.service_types = self._read_service_types()
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
            self._subscribe_to_proxy_topic()
    
    def _on_message(self, client, userdata, msg):
        MqttGObjectBridge._on_message(self, client, userdata, msg)

        if MQTT.topic_matches_sub("device/+/Status", msg.topic):
            status = json.loads(msg.payload)
            logging.info("Received device status message %s", status)
            
            if self._status_is_valid(status):
                if status['connected'] == 1:
                    self._process_device(status)
                elif status['connected'] == 0:
                    self._remove_device(status)
                else:
                    logging.warning("Unrecognised device Connected status %s for client %s", status["clientId"])
            else:
                logging.warning("Status message from client %s failed validation and has been rejected", status["clientId"])

        elif MQTT.topic_matches_sub("device/+/Proxy", msg.topic):
            proxy = MQTTDeviceProxy(client)
            payload = json.loads(msg.payload)
            client_id = msg.topic.split("/")[1]
            proxy.process_message(client_id, payload)
        else:
            logging.warning('Received message on topic %s, but no action is defined', msg.topic)

    def _status_is_valid(self, status):
        validFormat = "^[a-zA-Z0-9_]*$"
        isValid = True

        # Check the connected attribute, expect 1 = connected, 0 = disconnected 
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
                logging.warning("status.clientId %s can only contain alpha numeric characters and _ (underscores)", clientId)

        # Check the services dictionary object
        services = status.get('services')
        if connected == 1:
            if services is None or services == "" or not isinstance(services, dict):
                isValid = False
                logging.warning("status.services must contain a dictionary of values if connected = 1")
            else:
                for service_id in services.keys(): # Check each service in the dictionary
                    if re.search(validFormat, service_id) == None : 
                        isValid = False
                        logging.warning("status.services contains a service %s with an invalid identifier, only alpha numeric characters and _ (underscores) are allowed", service_id)

                    if services.get(service_id) not in self.service_types: # as defined in services.yml
                        isValid = False
                        logging.warning("status.service type %s is not supported, please check services.yml", services.get(service_id))

        return isValid

    def _lookup_portalId(self):
        portalId = VeDbusItemImport(self._dbus_conn, "com.victronenergy.system", "/Serial").get_value()
        logging.info("Using portalId %s", portalId)
        return portalId


    def _read_service_types(self):
        try:                                                    
            base = os.path.dirname(os.path.realpath(__file__))  
            with open(os.path.join(base, 'services.yml'), 'r') as services_file:
                configs = yaml.safe_load(services_file)                         
                return configs.keys()
        except IOError as e:                                                                            
            logging.error("I/O error(%s): %s", e.errno, e.strerror)
        except: #handle other exceptions such as attribute errors                                       
            logging.error("Unexpected error: %s", sys.exc_info()[0])


    def _subscribe_to_device_topic(self):
        mqtt = self._client
        mqtt.subscribe("device/+/Status")

    def _subscribe_to_proxy_topic(self):
        mqtt = self._client
        mqtt.subscribe("device/+/Proxy")

    def _process_device(self, status):
        mqtt = self._client
        clientId = status["clientId"] # the device's client id
        device = self._devices.get(clientId)
        if device is None:
            # create a new device
            self._devices[clientId] = device = MQTTDevice(device_mgr=self, device_status=status)
        #deprecated - start
        topic = "device/{}/DeviceInstance".format(clientId)
        res = mqtt.publish(topic, json.dumps(device_instances(device.services)))
        #deprecated - end

        topic = "device/{}/DBus".format(clientId)
        #res = mqtt.publish(topic, json.dumps( { "portalId": self.portalId, "deviceInstance": device.device_instances() } ) )
        res = mqtt.publish(topic, json.dumps( build_dbus_payload(self.portalId, device.services) ) )

        logging.info('publish %s to %s, status is %s', build_dbus_payload(self.portalId, device.services), topic, res.rc)


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