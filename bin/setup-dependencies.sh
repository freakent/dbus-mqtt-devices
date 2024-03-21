#!/bin/sh
BASE=$(dirname $(dirname $(realpath "$0")))
PREFIX="dbus-mqtt-devices:"

check_online() {
    local url="https://vrm.victronenergy.com"
    local attempts=0
    while [ $attempts -lt 10 ]; do
        wget --spider --quiet --tries=1 --timeout=5 "$url"  # Check URL without downloading content
        if [ $? -eq 0 ]; then  # If wget succeeds (exit status 0)
            break  # Exit loop
        else
            attempts=$((atempts + 1))
            echo "`date` $PREFIX GX Device does not appear to be online, retrying in 1 minute..."
            sleep 60  # Wait for 1 minute before retrying
        fi
    done
}

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
    check_online
    opkg update && opkg install python3-pip
fi

#echo "$PREFIX Checking to see if python3-misc library is installed"
#if [ -z "`opkg list-installed | grep python3-misc`" ]; then
#    opkg update && opkg install python3-misc
#fi

echo "$PREFIX Pip install module dependencies"
check_online
python -m pip install -r $BASE/requirements.txt

if [ "$remount" = "yes" ]; then
    echo "$PREFIX Setting root partion back to readonly"
    mount -o remount,ro /
fi
