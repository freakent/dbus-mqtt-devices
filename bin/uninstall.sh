#!/bin/sh
#BASE=/data/drivers/dbus-mqtt-devices
BASE=$(dirname $(dirname $(realpath "$0")))

echo "Uninstall dbus-mqtt-devices from $BASE"

rm -f /service/dbus-mqtt-devices
rm -r $BASE
echo "Uninstall dbus-mqtt-devices complete"