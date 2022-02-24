# dbus-mqtt-devices

This Venus GX Driver works in concert with the Victron dbus-mqtt gateway. It 
allows Wi-Fi enabled devices (such as ESP32, some Arduino microcontrollers or Raspberry Pis) to self 
register to the dbus over MQTT. This avoids the need for additional dedicated 
custom drivers to be developed and deployed.

## Registration Protocol
This driver uses a pair of MQTT topics under the "devices/*" namespace to establish the 
registration, using the following protocol.  `<client id>` is the unique MQTT client ID set during MQTT initialisation (avoid using special characters ,.-/: in the client id).

1)  When a device initialises, it does 2 things :

    1) subscribes to a topic `"device/<client id>/DeviceInstance"`.

	2) publishes a status message on the MQTT topic `"device/<client id>/Status"`. 
		
        The Status payload is a json object containing :
    	
        `{ "clientid": <client id>, "connected": <either 1 or 0>, "version": "<text string>", "services": [<a dictionary of services that this device wants to use>] }`
   	
        example 1:
		
        `{ "clientid": "fe001", "connected": 1, "version": "v1.0 ALPHA", "services": {"t1": "temperature"} }`
		In example 1, the device is registering that it is equipped with two temperature sensors. The label t1 is just an arbitrary identifier that distinguish one service from another within a device. The version field can contain any string you like and is displayed within the GX console and on VRM.

        example 2:
		
        `{ "clientid": "fe002", "connected": 1, "version": "v2.3", "services": {"t1": "temperature", "t2": "temperature", "tk1": "tank" } }`
		In example 2, the device is registering that it is equipped with two temperature sensors and a tank level sensor. The labels t1, t2, tk2 are the unique arbitrary identifiers that distinguish one service from another within a device. 

2)	The driver will then use this information to :
    - obtain a numeric device instance (for VRM) for each device service (using the [ClassAndVrmInstance](https://github.com/victronenergy/localsettings#using-addsetting-to-allocate-a-vrm-device-instance) dbus service), 
    - set up [local settings](https://github.com/victronenergy/localsettings) for persistent storage of some attributes
    - register the device on the dbus, 
    - set up the appropriate dbus paths for the service type (i.e. temperature sensor can provide Temperature, Pressure and Humidity)
    

3)	The driver publishes a DeviceInstance message under the same MQTT Topic
	namespace. This is the topic the device subscribed to in step 1.1. The 
	DeviceInstance message contains the numeric device instances (one for each 
	service) that the device should use when publishing messages for dbus-mqtt
	to process (see 5). 
    
    For example:

		Topic: "device/<client id>DeviceInstance"
		Payload: {"t1": 5, "t2":12}


4)	The device uses the device instance to periodically publish messages to the 
	appropriate dbus-mqtt topics for the service they are providing. 
	
    For example:
	
    	Topic: "W/<portal id>/temperature/<device instance>/Temperature"
		Payload: { "value": 24.91 }


5) 	When a device disconnects it should notify the driver by publishing a 
	status message with a connected value of 0. With MQTT the preferred
	method of achieving this is through publishing an MQTT "last will" message.  
    
    For example:

		{ "clientid": "fe001", "version": "v1.0", "connected": 0, "services": {"t1": "temperature", "t2": "temperature"}}
	
    
    please note: on disconnect the contents of the "services" are actually irrelevant as all 
	the device services are cleared by this action.


## Things to consider:

- 	The device can have multiple sensors of the same type (e.g. two 
	temperature sensors), each publishing to different dbus-mqtt topics as 
	different device services and unique Device Instance values.
- 	Each device service will appear separately on the Venus GX device, and 
	each can have a customised name that will show on the GX display and in 
	VRM.
- 	Currently this driver only supports temperature and tank level services but the 
	protocol and the driver have been designed to be easily extended for 
	other services supported by dbus-mqtt (see [services.yml](https://github.com/freakent/dbus-mqtt-devices/blob/main/services.yml)).
-   A working Arduino Sketch (for Arduino Nano 33 IOT) that publishes temperature readings from an 
    Adafruit AHT20 temperature and humidity module using this driver and 
    mqtt-dbus is available at https://github.com/freakent/mqtt_wifi_sis
	
## Install and Setup:
To get the driver up and running, download the latest release from github and then run the setup script.

1. ssh into venus device

2. Download the latest zip from github and extract contents

```
$ mkdir -p /data/drivers
$ cd /data/drivers
$ wget -O dbus-mqtt-devices.zip https://github.com/freakent/dbus-mqtt-devices/archive/refs/tags/v0.2.1.zip
$unzip dbus-mqtt-devices.zip
```

3. Run the set up script
```
$ ./dbus-mqtt-devices-0.2.1/bin/setup.sh
```

4. Check the contents of /data/rc.local to ensure dbus-mqtt-device automatically starts on reboot
```
$ cat /data/rc.local
ln -s /data/drivers/dbus-mqtt-devices-0.2.1/bin/service /service/dbus-mqtt-devices
```

5. Reboot (recommended)
```
$ reboot
```

## To Do
1) Use of command line args
2) Figure out why ctrl-C isn't working right
3) Substitute any special characters in the client id for safe underscores _
4) Add support for more dbus-mqtt services

