#!/bin/bash
# Description: This script disables the GPS D-Bus service by removing its entry from the serial-starter configuration file.
NAME="gps-dbus"
FILE="/etc/venus/serial-starter.conf"

if grep -q "$NAME" "$FILE"; then

    # check to see if filesystem is readonly
    readonly=$(awk '$2 == "/" { print $4 }' /proc/mounts | grep -q 'ro' && echo "yes" || echo "no")
    if [ "$readonly" = "yes" ]; then
        echo "$PREFIX Temporarily enable writing to root partition"
        mount -o remount,rw /
        remount="yes"
    fi

    # Make changes to the config file
    mv "$FILE" "$FILE.bak"
    grep -v "$NAME" "$FILE.bak" > "$FILE"
    echo "Serial service $NAME has been disabled."

    # Set filesystem back to readonly if required
    if [ "$remount" = "yes" ]; then
        echo "$PREFIX Setting root partition back to readonly"
        mount -o remount,ro /
    fi

else
    echo "Serial service $NAME is already disabled."
fi

SERVICE_COUNT=$(ls /service/*.ttyUSB0 | wc -l)
if [ $SERVICE_COUNT -ne 0 ]; then
    echo "stopping $SERVICE_COUNT serial service(s) on ttyUSB0"
    /opt/victronenergy/serial-starter/stop-tty.sh ttyUSB0 
fi
