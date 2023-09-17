import paho.mqtt.client as mqtt
import json
import copy
import os

clientid = "fe002"
mqtt_host = os.environ.get("MQTT_HOST", "venus.local")
mqtt_port = int(os.environ.get("MQTT_PORT", "1883"))

registration = {
  "clientId": clientid,
  "connected": 1,
  "version": "v0.2",
  "services": {
    "tk1": "tank"
  }
}

unregister = copy.deepcopy(registration)
unregister["connected"] = 0

data = {
    "Level": 12.34,
    "Remaining": 0.5678
}

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("device/{}/DBus".format(clientid))
    client.publish("device/{}/Status".format(clientid), json.dumps(registration))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

    dbus_msg = json.loads(msg.payload)
    portalId = dbus_msg.get("portalId")
    deviceId = dbus_msg.get("deviceInstance").get("tk1") # UPDATE THIS

    for key in data:
        topic = "W/{}/tank/{}/{}".format(portalId, deviceId, key) # UPDATE THIS
        print("{} = {}".format(topic, data.get(key) ) )
        client.publish(topic, json.dumps({ "value": data.get(key) }) )

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.will_set("device/{}/Status".format(clientid), json.dumps(unregister)) # UPDATE THIS

client.connect(mqtt_host, mqtt_port, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()