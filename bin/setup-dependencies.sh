#!/bin/sh
BASE=$(dirname $(dirname $(realpath "$0")))

echo "dbus-mqtt-devices: Checking to see if Python's Pip is installed"
python -m pip --version
piperr=$?
if [ "$piperr" -ne 0 ]; then
    opkg update && opkg install python3-pip
fi

echo "dbus-mqtt-devices: Checking to see if python3-misc library is installed"
if [ -z "`opkg list-installed | grep python3-misc`" ]; then
    opkg update && opkg install python3-misc
fi

echo "dbus-mqtt-devices: Pip install module dependencies"
python -m pip install -r $BASE/requirements.txt
