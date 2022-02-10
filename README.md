# dbus-mqtt-devices

This Venus GX Driver works in concert with the Victron dbus-mqtt gateway. It 
enables devices (such as Arduino microcontrollers or Raspberry Pi) to self 
register to the dbus over MQTT. This avoids the need for additional dedicated 
custom drivers to be developed and deployed.

## Registration Protocol
The driver uses a pair of MQTT topics under the "devices/*" namespace to establish the 
registration, using the following protocol:

1)  When a device initialises, it does 2 things:

    a) subscribes to a topic `"device/<client id>/DeviceInstance"`.

	b) publishes a status message on the MQTT topic `"device/<client id>/Status"`. 
		
        The Status payload is a json object containing :
    	
        `{ "clientid": <client id>, "connected": <either 1 or 0>, "version": "<text string>", "services": [<a dictionary of services that this device wants to use>] }`
   	
        for example:
		
        `{ "clientid": "fe001", "connected": 1, "version": "v1.0 ALPHA", "services": {"t1": "temperature", "t2": "temperature"} }`

2)	The driver will the use this infomation to :
    - obtain a numeric device instance (for VRM), 
    - set up local settings for persistent storage of some attributes
    - register the device on the dbus, 
    - set up the appropriate dbus paths for the service type (i.e. temperature sensor can provide Temperature, Pressure and Humidity)
    

3)	The driver publishes a DeviceInstance message under the same MQTT Topic
	namespace. This is the topic the device subscribed to in 1a). The 
	DeviceInstance message contains the numeric device instances (one for each 
	service) that the device should use when publishing messages for dbus-mqtt
	to process (see 5). 
    
    For example:

		`Topic: "device/<client id>DeviceInstance"
		Payload: {"t1": 5, "t2":12}`


4)	The device uses the device instance to periodically publish messages to the 
	appropriate dbus-mqtt topics for the service they are providing. 
	
    For example:
	
    	`Topic: "W/<portal id>/temperature/<device instance>/Temperature"
		Payload: { "value": 24.91 }`


5) 	When a device disconnects it should notify the driver by publishing a 
	status message with a connected value of 0. With MQTT the preferred
	methos of achieving this is through am MQTT "last will". 
    
    For example:

		`{ "clientid": "fe001", "connected": 0, "services": {"t1": "temperature", "t2": "temperature"}}`
	
    
    plead note: the contents of the "services" are actually irrelevant as all 
	the device services are cleared by the message


## Things to consider:

- 	The device can have multiple sensors of the same time (e.g. two 
	temperature sensors), each publishing to different dbus-mqtt topics as 
	different device services.
- 	Each device service will appear separately on the Venus GX device, and 
	each can have a customised name that will show on the display and in 
	VRM.
- 	Currently this driver only supports temperature services but the 
	protocol and the driver have been designed to be easily extended for 
	other services supported by dbus-mqtt.
-   A working Arduino Sketch that publishes temperature readings from an 
    Adafruit AHT20 temperature and humidty module using this driver and 
    mqtt-dbus is available at github. etc etc
	
## Running

    git clone git@github.com: etc etc
    cd etc etc
    git submodule update --init
    python dbus_mqtt_devices

## To Do
1) Change handling of payload of status message to allow for multiple services of the same type
2) Pass firmware version information from the device to dbus for display on GX device
2) Use of command line args
3) Figure out why ctrl-C isn't working right

