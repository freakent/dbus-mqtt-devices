# dbus-mqtt-devices 0.9.0

## If you have upgraded to Venus OS 3.60, please upgrade to dbus-mqtt-devices V0.9.0 or above asap! ##

This VenusOS Driver for GX devices works in concert with the [Victron dbus-mqtt gateway](https://github.com/victronenergy/dbus-mqtt), now known as dbus-flashmq. It has been designed to allow Wi-Fi enabled edge devices (such as ESP32, some Arduino microcontrollers or Raspberry Pis) to self register to the dbus over MQTT. This avoids the need for additional dedicated custom drivers to be developed and deployed.

The following Victron dbus services are currently supported:
- temperature (com.victronenergy.temperature._device_)
- tank (com.victronenergy.tank._device_)
- pvinverter (com.victronenergy.pvinverter._device_)
- grid (com.victronenergy.grid._device_)
- gps (com.victronenergy.gps._device_)
- evcharger (com.victronenergy.evcharger._device_)
- battery (for JK BMS) (com.victronenergy.battery._device_)
- vebus (com.victronenergy.vebus._device_)
- dcdc (com.victronenergy.dcdc._device_)
- dcload (com.victronenergy.dcload._device_)
- dcsystem (com.victronenergy.dcsystem._device_)
- acload (com.victronenergy.acload._device_)

(See https://github.com/victronenergy/venus/wiki/dbus for detailed explanation of each attribute)

## [How To Say Thanks](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=R4Y63PPPD4CGG&source=url)
If you find this driver useful and you want to say thanks, feel free to buy me a coffee using the "Thank You" link below.

[![Say Thanks](https://raw.githubusercontent.com/freakent/node-red-contrib-sunevents/main/docs/thankyou.jpg "Say Thanks")
](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=R4Y63PPPD4CGG&source=url)

## Contents
1. [Install and Setup](#Install-and-Setup)
2. [Updating after VenusOS updates](#Updating-after-VenusOS-updates)
3. [How this driver works - The Registration Protocol](#how-this-driver-works---the-registration-protocol)
4. [The MQTT Proxy (optional)](#The-MQTT-Proxy)
5. [Last Will Topic](#Last-Will-Topic)
6. [Troubleshooting](#Troubleshooting)
7. [Developers](#Developers)


## Install and Setup

**Please Note: this driver is not supported on CCGX due to it's limited system resources. Installation on CCGX has been known to can cause random reboots.**

To get the driver up and running, follow the steps below to download the latest release from github and then run the setup script.

1. ssh into venus device (as root)

If you have not yet enabled root (superuser) access via SSH, follow the instructions here: https://www.victronenergy.com/live/ccgx:root_access.

2. Download the latest zip from github and extract contents

```
mkdir -p /data/drivers
cd /data/drivers
wget -O dbus-mqtt-devices.zip https://github.com/freakent/dbus-mqtt-devices/archive/refs/tags/v0.9.0.zip
unzip dbus-mqtt-devices.zip
```

3. Run the setup script
```
./dbus-mqtt-devices-0.9.0/bin/setup.sh
```

4. Check the contents of /data/rc.local to ensure the correct version starts automatically on reboot
```
# cat /data/rc.local
/data/drivers/dbus-mqtt-devices-0.9.0/bin/setup-dependencies.sh
ln -s /data/drivers/dbus-mqtt-devices-0.9.0/bin/service /service/dbus-mqtt-devices
```

5. Reboot device (recommended)
```
reboot
```

## Updating after VenusOS updates

The driver will automatically check and update (if required) it's own module dependencies on every reboot. There should be no need to do anything to the installation after a VenusOS upgrade.
If you do experience issues after a VenusOS upgrade, please follow the usual troubleshooting tips described later.


## How to use this driver - The Registration Protocol
This driver uses a pair of MQTT topics under the "device/*" MQTT namespace to establish the
device registration using the following protocol.

Please note: `<client id>` is a unique, short name you can use to identify the device (you MUST avoid using special characters ,.-/: in the client id). It is recommended (but not essential) that you use the same client ID during MQTT initialisation and connection.

1)  When a device initialises and EVERY time it connects to MQTT, it MUST do 2 things :

    1) subscribes to a topic `"device/<client id>/DBus"`.

	2) publishes a status message on the MQTT topic `"device/<client id>/Status"`.

        The Status payload is a json object containing :

        `{ "clientId": <client id>, "connected": <either 1 or 0>, "version": "<text string>", "services": [<a dictionary of services that this device wants to use>] }`

        example 1:

        `{ "clientId": "fe001", "connected": 1, "version": "v1.0 ALPHA", "services": {"t1": "temperature"} }`
		In example 1, the device is registering that it is equipped with one temperature sensor which we are calling "t1". The label t1 is just an arbitrary identifier that distinguishes one service from another within a device. "temperature" is the exact name of the service used in Victron's dbus. The version field can contain any string you like and is displayed within the GX console and on VRM.

        example 2:

        `{ "clientId": "fe002", "connected": 1, "version": "v2.3", "services": {"t1": "temperature", "t2": "temperature", "tk1": "tank" } }`
		In example 2, the device is registering that it is equipped with two temperature sensors and a tank level sensor. The labels t1, t2, tk2 are the unique arbitrary identifiers that distinguish one service from another within a device.

2)	The driver will then use this information to :
    - obtain a numeric device instance (for VRM) for each device service (using the [ClassAndVrmInstance](https://github.com/victronenergy/localsettings#using-addsetting-to-allocate-a-vrm-device-instance) dbus service),
    - set up [local settings](https://github.com/victronenergy/localsettings) for persistent storage of some attributes
    - register the device on the dbus,
    - set up the appropriate dbus paths for the service type (i.e. temperature sensor can provide Temperature, Pressure and Humidity)


3)	Once successfully registered, the driver publishes a message on the device/\<client id\>/DBus topic.
	This must be the same topic the device subscribed to in step 1.1. The
	DBus message contains the all important numeric device instances (one for each
	service) that the device should use when publishing messages for dbus-mqtt
	to process. It also contains the portal id needed to construct a dbus-mqtt topic (see 4).

    For example:

		Topic: "device/<client id>/DBus"
		Payload: {"portalId": "<vrm portal id>", deviceInstance":{"t1": 5, "t2":12}, "topicPath": {...} }

	_Please note_:
	1) the original `device/<client id>/DeviceInstance` topic has now been removed in favour of `device/<client id>/DBus`. By combining the `<portal id>` and `<device instance>` in the same message payload, client code will be simpler and it leaves scope for future expansion.
	2) for topicPath details see the [MQTT Proxy](#the-mqtt-proxy) section below.


4)	Custom code on the device then uses the device instance to periodically publish messages to the
	appropriate dbus-mqtt topics for the service(s) they are providing.
	Note the "W" at the start of the topic. See the Victron dbus-mqtt documentation for an explanation.

    For example:

    	Topic: "W/<portal id>/temperature/<device instance>/Temperature"
		Payload: { "value": 24.91 }


5) 	When a device disconnects it should notify the driver by publishing a
	status message with a connected value of 0. With MQTT, the preferred
	method of achieving this is through publishing an MQTT "last will" message.

    For example:

		{ "clientId": "fe001", "version": "v1.0", "connected": 0, "services": {"t1": "temperature", "t2": "temperature"}}


    _please note_: on disconnect the contents of the "services" are actually irrelevant as all
	the device services are cleared by this action.

### Design notes
-	Client devices MUST always self register (by sending a Status message with connected = 1) every time they connect to MQTT. Re-registering an
	already registered device has no adverse affect.
- 	The device can have multiple sensors of the same type (e.g. two
	temperature sensors), each publishing to different dbus-mqtt topics as
	different device services and unique Device Instance values.
- 	Each device service will appear separately on the Venus GX device, and
	each can have a customised name that will show on the GX display and in
	VRM.
- 	This driver currently supports a subset of the Victron services exposed through dbus-mqtt but the
	protocol and the driver have been designed to be easily extended for
	other services supported by dbus-mqtt (see [services.yml](https://github.com/freakent/dbus-mqtt-devices/blob/main/services.yml) config file).
-   A working Arduino Sketch (for Arduino Nano 33 IOT) that publishes temperature readings from an
    Adafruit AHT20 temperature and humidity module using this driver and
    mqtt-dbus is available at https://github.com/freakent/mqtt_wifi_sis
-   Simple client examples (gps-simulator and tank-simulator) can be found in the samples directory.
    These are NOT designed to be run on the GX, but you can run them from any other computer connected to the same network as the Venus OS device.


## The MQTT Proxy

The design of VenusOS MQTT api (either flashmq-mqtt or dbus-mqtt) requires the client device to publish separate MQTT messages for each data value to be published on the DBUS. In many cases this can require
a lot of extra boiler plate code to format each data value payload and publish each individual value to the appropriate "W" topic. The goal of this driver is to simplify use of the
DBUS MQTT api, especially for edge sensing client devices. Reducing the amount of boiler plate code running on the client device will help simplify device code and simplify development. Use of the
dbus-mqtt-devices proxy will help simplify client side code.

**The use of the Proxy is entirely optional, the client device can continue to use the driver for dbus registration and publish values to the "W" topics without using the proxy.**

To use the proxy, format your payload as follows and publish to topic `device/<clientId>/Proxy`:
```
{
   "topicPath": "W/<portalid>/<service>/<deviceid>", # deviceid is the Id returned by registration process
   "values": {
       "<attribute 1>" : <value 1>,
       "<attribute 2": <value 2>,
       "<attribute n>": <value n>
    }
}
```

For example, to publish data for a temperature device you would format your payload like this:
```
{
   "topicPath": "W/<portalid>>/temperature/1", # Note the W for a write topic
   "values": {
       "Temperature" : 23,
       "Pressure": 900,
       "Humidity": 56
    }
}
```

When you publish that payload to topic `device/<clientId>/Proxy`, the Proxy will perform some basic validation and perform a publish on behalf of the client for
each attribute and value pair in the payload. The actual topic written to is a concatenation of the topic path and the attribute name.

### Topic Path
To help simplify client code further, a "topic path" collection is returned in the `device/<device>/DBus`
message obtained during device registration, removing the need for the client to have to build this topic path string.
for example:

if a device known as "venusnr", with a temperature service known as "temp01" were to publish the following payload to `device/venusnr/Status`
```
{"clientId": "venusnr", "connected": 1, "version": "v1.0.0", "services": {"temp01": "temperature"} }
```

The following registration message would be published by the driver to `device/venusnr/DBus`
```
{
  "portalId": "<portalId>",
  "deviceInstance": {"temp01": 7},
  "topicPath": {"temp01": {"N': "N/portId>/temperature/7", "R": "R/<portalid>/temperature/7", "W": "W/<portalId>/temperature/7"} }
}
```
The expectation is that the client can then simply select the correct topic path by using an expression such as `payload.topicPath["temp01"]["W"]`.

## Last Will Topic
If a device shuts down or disconnects from MQTT it should send a disconnect message to signal to the dbus that is has become disconnected. The preferred
mechanism for doing thi is via a "last will" message, see step 5 of [How this driver works - The Registration Protocol](#how-this-driver-works---the-registration-protocol)
for more details.

However some devices with built-in MQTT support (such as Shelly devices) do not allow the user to set their own the last will message. Instead Shelly devices publish their own
status message to a device specific topic. From dbus-mqtt-devices v0.9.0 onwards you can you include "lwt_topic" and "lwt_value" attributes
in your device connection payload. For example:
```
    {
        "clientId": "fe001",
        "connected": 1,
        "lwt_topic": "shellies/myshelly/online", "lwt_value": "false",
        "version": "v1.0 ALPHA",
        "services": {
            "t1": "temperature"
        }
    }
```
Once registered, dbus-mqtt-devices will subscribe to the supplied "lwt_topic". If the contents matches the "lwt_value" then dbus_mqtt_devices will automatically
disconnect the device from the dbus. On device start-up, the device will obviously need to re-send a registration payload to start sending data again.

This feature should allow devices like Shelly to be managed and disconnected more easily with Venus OS.

## Troubleshooting
### during installation
If you receive an error during setup that includes the lines
```
ModuleNotFoundError: No module named 'dataclasses'
```
Try running the following before running the setup.sh script again.
```
opkg install python3-modules
```
### at runtime
1) First thing to check is that you are not sending numeric values as strings.
publishing a payload like this can cause unexpected problems:
```
{
    "value": "100" <- WRONG
}
```
Make sure numeric values are not surrounded by quotes in your json.
```
{
    "value": 100 <- CORRECT
}
```
Similarly, if your payload is created in Javascript (node-red), be careful with values like "Null", "infinity" and "NaN".

2) Check the dbus-mqtt-devices service is running, from the ssh command line use
```
svstat /service/dbus-mqtt-devices
```
More info on deamontools that VenusOs uses here: https://cr.yp.to/daemontools.html

3) If the service is not running then ensure that your rc.local script has execute permissions.
```
ls -l /data/rc.local
...
chmod +x /data/rc.local
```
4) Check whether there were any errors whilst setting up dependencies during system startup by checking the boot log file with the command:

```
$ more /var/log/boot
```
It should contain something like this:
```
Wed Apr  9 08:13:53 2025: dbus-mqtt-devices:: Setup-dependencies started
Wed Apr  9 08:13:53 2025: dbus-mqtt-devices: Temporarily enable writing to root partition
...
Wed Apr  9 08:15:56 2025: dbus-mqtt-devices: Setting root partition back to readonly
Wed Apr  9 08:15:58 2025: dbus-mqtt-devices: Setup-dependencies complete

```
5) If the service is running, then the next thing to check is the dbus-mqtt-devices log file with the command:
```
$ more /var/log/dbus-mqtt-devices/current
```
It should contain something like this:
```
@400000006238ead134c233e4 INFO:device_manager:Received device status message {'clientId': 'fe001', 'connected': 1, 'version': 'v1.0', 'services': {'t1': 'temperature'}}
@400000006238ead134c25324 INFO:device:**** Registering device: fe001, services: {'t1': 'temperature'} ****
@400000006238ead134c25edc INFO:device:Registering Service temperature for client fe001
@400000006238ead134c26a94 INFO:device_service_config:About to open config file
@400000006238ead136d95fcc INFO:device_service:Unregistered mqtt_fe001_t1 from dbus
@400000006238ead136df10d4 INFO:device_service:Unregistered mqtt_fe001_t1 from dbus
@400000006238ead136ea9ddc INFO:device_service:Unregistered mqtt_fe001_t1 from dbus
@400000006238ead13755bbbc INFO:device_service:Registering service temperature for client fe001 at path com.victronenergy.temperature.mqtt_fe001_t1
@400000006238ead13903b20c INFO:settingsdevice:Setting /Settings/Devices/mqtt_fe001_t1/ClassAndVrmInstance does not exist yet or must be adjusted
@400000006238ead13a94dd44 INFO:vedbus:registered ourselves on D-Bus as com.victronenergy.temperature.mqtt_fe001_t1
@400000006238ead13ac572c4 INFO:device_service:Registered Service com.victronenergy.temperature.mqtt_fe001_t1 under DeviceInstance 1
@400000006238ead13ad8d79c INFO:device_manager:publish {'portalId': '<portal id>', 'deviceInstance': 't1': '1'} to device/fe001/DBus, status is 0
```

If you can have ssh open in another window, then
```
tail -f /var/log/dbus-mqtt-devices/current
```
is a useful way to monitor the driver.

If you need human readable timestamps you have to pipe the output through tai64nlocal, for example
```
tail -f /var/log/dbus-mqtt-devices/current | tai64nlocal
```

6) If you have re-installed more than once, make sure there is only one line in your rc.local for dbus-mqtt-devices.
```
more /data/rc.local
```

7) I highly recommend using *MQTT-Explorer* (http://mqtt-explorer.com/) to monitor the N/* topics while debugging and if you are doing anything with MQTT.
There is a keepalive script in the samples directory if you need it.

8) In the unlikely event that the installation fails, and your ccgx device will not boot, follow these instructions to recover it.
https://community.victronenergy.com/questions/48309/ccgx-firmware-upgrade-problem.html

9) If you are still having a problem feel free to start an Discussion on the Github project here: https://github.com/freakent/dbus-mqtt-devices/discussions
Please start a discussion instead of an issue.


## Developers
if you are wanting to run the pytests on macos you need to install a few dependencies:

#### using homebrew
```
$ brew install dbus pygobject3 gtk+3
$ pip3 install pytest python-dbus paho-mqtt PyGObject
$ pytest --ignore=ext

```
