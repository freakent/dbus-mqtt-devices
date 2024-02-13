import paho.mqtt.client as mqtt
import json
import copy

clientid = "st002"

registration = {
  "clientId": clientid,
  "connected": 1,
  "version": "v0.9",
  "services": {
    "pv1": "pvinverter"
  }
}

unregister = copy.deepcopy(registration)
unregister["connected"] = 0

data = {
    "ErrorCode": 0,
    "Ac/MaxPower": 133,
    "Ac/Energy/Forward" : 1.1,
    "Ac/Power": 1100,
    "Ac/Current": 11,
    "Ac/L1/Current": 3,
    "Ac/L1/Energy/Forward": 30,
    "Ac/L1/Power": 33.3,
    "Ac/L1/Voltage": 12.3,
    "Ac/L2/Current": 4,
    "Ac/L2/Energy/Forward": 40,
    "Ac/L2/Power": 44.4,
    "Ac/L2/Voltage": 12.4,
    "Ac/L3/Current": 5,
    "Ac/L3/Energy/Forward": 50,
    "Ac/L3/Power": 55.5,
    "Ac/L3/Voltage": 12.5
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
    deviceId = dbus_msg.get("deviceInstance").get("pv1") # UPDATE THIS

    for key in data:
        topic = "W/{}/pvinverter/{}/{}".format(portalId, deviceId, key) # UPDATE THIS
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
