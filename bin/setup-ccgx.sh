#!/bin/sh
BASE=$(dirname $(dirname $(realpath "$0")))

echo "Setup dbus-mqtt-devices in $BASE started"
cd $BASE/ext

echo "Ensure PyYAML is installed "
wget -qO- https://files.pythonhosted.org/packages/36/2b/61d51a2c4f25ef062ae3f74576b01638bebad5e045f747ff12643df63844/PyYAML-6.0.tar.gz | tar xvz -C $BASE/ext
cd $BASE/ext/PyYAML-6.0
python setup.py --without-libyaml install

cd $BASE

echo "Set up Victron module libraries"
rm -fr $BASE/ext/dbus-mqtt $BASE/ext/velib_python
ln -s /opt/victronenergy/dbus-mqtt $BASE/ext
ln -s /opt/victronenergy/dbus-digitalinputs/ext/velib_python $BASE/ext

echo "Set up device service to autorun on restart"
chmod +x $BASE/dbus_mqtt_devices.py
# Use awk to inject correct BASE path into the run script
awk -v base=$BASE '{gsub(/\$\{BASE\}/,base);}1' $BASE/bin/service/run.tmpl >$BASE/bin/service/run
chmod -R a+rwx $BASE/bin/service
rm -f /service/dbus-mqtt-devices
ln -s $BASE/bin/service /service/dbus-mqtt-devices

CMD="ln -s $BASE/bin/service /service/dbus-mqtt-devices"
if ! grep -q "$CMD" /data/rc.local; then
    echo "$CMD" >> /data/rc.local
fi
chmod +x /data/rc.local
echo "Setup dbus-mqtt-devices complete"