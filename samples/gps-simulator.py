import paho.mqtt.client as mqtt
import json
import copy

clientid = "fe003"

registration = {
  "clientId": clientid,
  "connected": 1,
  "version": "v0.9",
  "services": {
    "gps1": "gps"
  }
}

unregister = copy.deepcopy(registration)
unregister["connected"] = 0

data = {
    "Position/Latitude": 51.5072,
    "Position/Longitude": 0.1276,
    "Course" : 0,
    "Speed": 0,
    "Altitude": 0,
    "Fix": 10,
    "NrOfSatellites": 10
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
    deviceId = dbus_msg.get("deviceInstance").get("gps1") # UPDATE THIS

    for key in data:
        topic = "W/{}/gps/{}/{}".format(portalId, deviceId, key) # UPDATE THIS
        print("{} = {}".format(topic, data.get(key) ) )
        client.publish(topic, json.dumps({ "value": data.get(key) }) )

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.will_set("device/{}/Status".format(clientid), json.dumps(unregister)) # UPDATE THIS

client.connect("venus.local", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
