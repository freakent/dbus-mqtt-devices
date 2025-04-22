import paho.mqtt.client as mqtt
import json
import copy

clientid = "jkmqtt"

registration = {
  "clientId": clientid,
  "connected": 1,
  "version": "v1.0",
  "services": {
    "jkbms2": "battery"
  }
}

unregister = copy.deepcopy(registration)
unregister["connected"] = 0

data = {
    "System/MinCellVoltage":  3.325,
    "System/MaxCellVoltage":  3.326,
    "Dc/0/Temperature":  13,
    "Dc/0/Voltage":  26.6,
    "Dc/0/Current":  -2.48,
    "Dc/0/Power":  -65,
    "Soc":  78,
    "System/NrOfCellsPerBattery":  8,
    "Capacity":  195,
    "InstalledCapacity":  250,
    "Io/AllowToCharge": 1,
    "Io/AllowToDischarge": 1,
    "System/NrOfModulesBlockingCharge": 0,
    "System/NrOfModulesBlockingDischarge": 0,
    "System/NrOfCellsPerBattery": 8,
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
    deviceId = dbus_msg.get("deviceInstance").get("jkbms2") # UPDATE THIS

    for key in data:
        topic = "W/{}/battery/{}/{}".format(portalId, deviceId, key) # UPDATE THIS
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
