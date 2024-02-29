#!/bin/sh
#BASE=/data/drivers/dbus-mqtt-devices
BASE=$(dirname $(dirname $(realpath "$0")))
PREFIX="dbus-mqtt-devices:"

echo "$PREFIX Setup of `cat VERSION` in $BASE started"
cd $BASE

./bin/setup-dependencies.sh

echo "$PREFIX Set up Victron module libraries"
rm -fr $BASE/ext/dbus-mqtt $BASE/ext/velib_python
ln -s /opt/victronenergy/dbus-mqtt $BASE/ext
ln -s /opt/victronenergy/dbus-digitalinputs/ext/velib_python $BASE/ext

echo "$PREFIX Set up device service to autorun on restart"
chmod +x $BASE/dbus_mqtt_devices.py
# Use awk to inject correct BASE path into the run script
awk -v base=$BASE '{gsub(/\$\{BASE\}/,base);}1' $BASE/bin/service/run.tmpl >$BASE/bin/service/run
chmod -R a+rwx $BASE/bin/service
rm -f /service/dbus-mqtt-devices
ln -s $BASE/bin/service /service/dbus-mqtt-devices

CMD="$BASE/bin/setup-dependencies.sh"
if ! grep -s -q "$CMD" /data/rc.local; then
    echo "$CMD" >> /data/rc.local
fi

echo "$PREFIX Adding device service to /data/rc.local"

CMD="ln -s $BASE/bin/service /service/dbus-mqtt-devices"
if ! grep -s -q "$CMD" /data/rc.local; then
    echo "$CMD" >> /data/rc.local
fi

# comment out lines that match different versions of dbus-mqtt-devices 
# by a) ignoring lines that start with comments, b) only selecting lines that contain dbus-mqtt0-devices, c) ignore any that match the current BASE path
awk -v BASE="$BASE/" '/^[^#]/ && /dbus-mqtt-devices/ && $0 !~ BASE f{$0 = "# " $0}{print}' /data/rc.local > /data/rc.local.tmp
mv /data/rc.local.tmp /data/rc.local
chmod +x /data/rc.local

echo "$PREFIX Setup complete"
