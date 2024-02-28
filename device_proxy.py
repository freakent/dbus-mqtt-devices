import logging
import os
import sys
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
            if not self.mqtt.topic_matches_sub("W/+/+/+", input["topicPath"]):
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
    
    def publish(self, input): 
        for message in self.transform(input):
            print(message["key"], message["value"])
            self.mqtt.publish( message["key"], {"value": message["value"]}) 
