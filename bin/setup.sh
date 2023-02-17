#!/bin/sh
#BASE=/data/drivers/dbus-mqtt-devices
BASE=$(dirname $(dirname $(realpath "$0")))

echo "dbus-mqtt-devices: Setup in $BASE started"
cd $BASE

echo "dbus-mqtt-devices: Checking to see if Python's Pip is installed"
python -m pip --version
piperr=$?
if [ "$piperr" -ne 0 ]; then
    opkg update && opkg install python3-modules python3-pip
fi

echo "dbus-mqtt-devices: Pip install module dependencies"
python -m pip install -r requirements.txt

echo "dbus-mqtt-devices: Set up Victron module libraries"
rm -fr $BASE/ext/dbus-mqtt $BASE/ext/velib_python
ln -s /opt/victronenergy/dbus-mqtt $BASE/ext
ln -s /opt/victronenergy/dbus-digitalinputs/ext/velib_python $BASE/ext

echo "dbus-mqtt-devices: Set up device service to autorun on restart"
chmod +x $BASE/dbus_mqtt_devices.py
# Use awk to inject correct BASE path into the run script
awk -v base=$BASE '{gsub(/\$\{BASE\}/,base);}1' $BASE/bin/service/run.tmpl >$BASE/bin/service/run
chmod -R a+rwx $BASE/bin/service
rm -f /service/dbus-mqtt-devices
ln -s $BASE/bin/service /service/dbus-mqtt-devices

echo "dbus-mqtt-devices: Adding device service to /data/rc.local"
CMD="ln -s $BASE/bin/service /service/dbus-mqtt-devices"
if ! grep -s -q "$CMD" /data/rc.local; then
    echo "$CMD" >> /data/rc.local
fi
chmod +x /data/rc.local
echo "dbus-mqtt-devices: Setup complete"
