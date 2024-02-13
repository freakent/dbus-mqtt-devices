import paho.mqtt.client as mqtt
import json
import copy
import time

clientid = "nr001"

registration = {
"clientId": clientid,
"connected": 1,
"version": "v2.3",
"services": {
  "t1": "temperature",
  "t2": "temperature",
  "t3": "temperature",
  "t4": "temperature",
  "t5": "temperature",
  "tk1": "tank",
  "tk2": "tank",
  "tk3": "tank",
  "tk4": "tank"
  }
}
unregister = copy.deepcopy(registration)
unregister["connected"] = 0

temp_data = {
    "Temperature": 12.34,
    "Pressure": 111,
}

tank_data = {
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
    deviceId = dbus_msg.get("deviceInstance").get("t1") 

    time.sleep(1)
    for key in temp_data:
        topic = "W/{}/temperature/{}/{}".format(portalId, deviceId, key) 
        print("{} = {}".format(topic, temp_data.get(key) ) )
        client.publish(topic, json.dumps({ "value": temp_data.get(key) }) )

    deviceId = dbus_msg.get("deviceInstance").get("tk1") 

    for key in tank_data:
        topic = "W/{}/tank/{}/{}".format(portalId, deviceId, key) 
        print("{} = {}".format(topic, tank_data.get(key) ) )
        client.publish(topic, json.dumps({ "value": tank_data.get(key) }) )

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.will_set("device/{}/Status".format(clientid), json.dumps(unregister)) 

client.connect("venus.local", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
