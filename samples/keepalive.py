import paho.mqtt.client as mqtt
import re
import os
import json
import datetime
import time

clientid = "keepalive"
mqtt_host = os.environ.get("MQTT_HOST", "venus.local")
mqtt_port = int(os.environ.get("MQTT_PORT", "1883"))
portalId = None
lastKeepalive = datetime.datetime.now() - datetime.timedelta(hours=1)

def on_connect(client, userdata, flags, rc):
    print("Connected (result code "+str(rc)+")")
    client.subscribe("N/+/system/+/Serial")
    client.subscribe("N/+/full_publish_completed")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global portalId
    #print(msg.topic+" "+str(msg.payload))
    payload = json.loads(msg.payload)

    # if len(re.findall("^N\/\w*\/system\/\w*\/Serial", msg.topic)) != 0:
    if len(re.findall(r"^N\/\w*\/system\/\w*\/Serial", msg.topic)) != 0:
        portalId = payload["value"]
        print("portalId", portalId)

    if msg.topic == "N/{}/full_publish_completed".format(portalId):
        print("all messages received")
    


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(mqtt_host, mqtt_port, 60)

client.loop_start()

while True:
    print(".", end='', flush=True)
    if portalId != None and datetime.datetime.now() > lastKeepalive + datetime.timedelta(seconds=60) :
        client.publish("R/{}/keepalive".format(portalId))
        lastKeepalive = datetime.datetime.now()
        print()
        print(lastKeepalive.strftime("%X") + ": sending keepalive")
    time.sleep(10)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.disconnect()
client.loop_stop()