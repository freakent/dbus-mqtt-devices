import logging
import os
import sys
import json
import paho.mqtt.client as MQTT

from version import VERSION 

class MQTTDeviceProxy(object):

    def __init__(self, mqtt):
        self.mqtt = mqtt
        #self.device = device

    def validate(self, input):
        errs = []
        if type(input) is not dict:
            errs.append("Payload is not a JSON Object")
        
        if "topicPath" not in input:
            errs.append("No topicPath attribute found in JSON payload")
        else:
            if not MQTT.topic_matches_sub("W/+/+/+", input["topicPath"]):
                errs.append("Attribute topic_path must match W/<portal id>/<service>/<device instance>")
        
        if "values" not in input:
            errs.append("No values attribute found in JSON payload")
        else:
            if type(input["values"]) is not dict:
                errs.append("Attribute values is not a JSON Object")
            else:
                for k in input["values"]:
                    if k[0].upper() != k[0]:
                        errs.append("Dbus keys must start with a capital letter")

            if len(input["values"]) == 0:
                errs.append("Attribute values contains no data")

        return errs

    def transform(self, input):
        topic_path = input["topicPath"]
        output = []
        for k, v in input["values"].items():
            output.append(  { "key": topic_path + '/' + k, "value": v} )
        return output
    
    def process_message(self, client_id, msg): 
        errs =  self.validate(msg)
        if len(errs) == 0:
            logging.info("Processing device proxy message from %s: %s", client_id, msg)
            msg_count = 0
            for message in self.transform(msg):
                self.mqtt.publish( message["key"], json.dumps({"value": message["value"]}))
                msg_count = msg_count +1
            logging.info("%s proxy message(s) sent on behalf of %s", msg_count, client_id )
        else:
            logging.warning("*** Invalid Proxy payload was rejected: %s", msg)
            logging.warning("*** The following errors were found in Proxy payload: %s", errs)


