#!/bin/sh
BASE=$(dirname $(dirname $(realpath "$0")))
PREFIX="dbus-mqtt-devices:"

readonly=$(awk '$2 == "/" { print $4 }' /proc/mounts | grep -q 'ro' && echo "yes" || echo "no")
if [ "$readonly" = "yes" ]; then
    echo "$PREFIX Temporarily enable writing to root partion"
    mount -o remount,rw /
    remount="yes"
fi

echo "$PREFIX Checking to see if Python's Pip is installed"
python -m pip --version
piperr=$?
if [ "$piperr" -ne 0 ]; then
    opkg update && opkg install python3-pip
fi

echo "$PREFIX Checking to see if python3-misc library is installed"
if [ -z "`opkg list-installed | grep python3-misc`" ]; then
    opkg update && opkg install python3-misc
fi

echo "$PREFIX Pip install module dependencies"
python -m pip install -r $BASE/requirements.txt

if [ "$remount" = "yes" ]; then
    echo "$PREFIX Setting root partion to readonly"
    mount -o remount,ro /
fi
