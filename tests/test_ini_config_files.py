from logging import NullHandler
import os
import sys
import copy
test_dir = os.path.dirname(__file__)
sys.path.insert(1, os.path.join(test_dir, '..'))
sys.path.insert(1, os.path.join(test_dir, '..', 'ext', 'dbus-mqtt'))

from device_service_ini_config import MQTTDeviceServiceConfig


def test_temperature_config():
    serviceName = "ts1"
    serviceType = "temperature"
    config = MQTTDeviceServiceConfig(serviceName, serviceType) 

    assert config.local_settings() == {
        'CustomName': ["/Settings/MqttDevices/{}/CustomName".format(serviceName), 'My {} Sensor'.format(serviceType.capitalize()), 0, 0],
        'TemperatureType': ["/Settings/MqttDevices/{}/TemperatureType".format(serviceName), 2, 0, 2]
    }

    #print(config.dbus_paths())
    dbus_paths = { key: val for (key, val) in list(config.dbus_paths()) }
    assert list(dbus_paths.keys()) == ['ProductId', 'CustomName', 'TemperatureType', 'Temperature', 'Pressure', 'Humidity']

    assert dbus_paths['CustomName'].get('default') == 'My Temperature Sensor'
    assert dbus_paths['CustomName'].getboolean('persist') == True

    assert dbus_paths['Temperature'].get('description') == 'C'
    assert dbus_paths['Pressure'].get('description') == 'hPa'
    assert dbus_paths['Humidity'].get('description') == '%'

    assert dbus_paths['TemperatureType'].get('description') == 'Battery, Fridge or Generic'
    assert dbus_paths['TemperatureType'].getboolean('persist') == True
    assert dbus_paths['TemperatureType'].getint('default') == 2
    assert dbus_paths['TemperatureType'].getint('min') == 0
    assert dbus_paths['TemperatureType'].getint('max') == 2


def test_gps_config():
    serviceName = "GPS1"
    serviceType = "gps"
    config = MQTTDeviceServiceConfig(serviceName, serviceType) 

    assert config.local_settings() == {
        'CustomName': ["/Settings/MqttDevices/{}/CustomName".format(serviceName), 'My GPS Sensor', 0, 0]
    }

    #print(config.dbus_paths())
    dbus_paths = { key: val for (key, val) in list(config.dbus_paths()) }
    assert list(dbus_paths.keys()) == ['ProductId', 'CustomName', 'Position/Longitude', 'Position/Latitude', 'Course', 'Speed', 'Fix', 'Altitude', 'NrOfSatellites']

    assert dbus_paths['CustomName'].get('default') == 'My GPS Sensor'
    assert dbus_paths['CustomName'].getboolean('persist') == True

    assert dbus_paths['Position/Longitude'].get('description') == 'Decimal degrees'
    assert dbus_paths['Position/Latitude'].get('description') == 'Decimal degrees'
    assert dbus_paths['Course'].get('description') == 'Degrees'
    assert dbus_paths['Speed'].get('description') == 'm/s'


def test_tank_config():
    serviceName = "tks99"
    serviceType = "tank"
    config = MQTTDeviceServiceConfig(serviceName, serviceType) 

    assert config.local_settings() == {
        'CustomName': ["/Settings/MqttDevices/{}/CustomName".format(serviceName), 'My Tank Sensor', 0, 0],
        'Capacity': ["/Settings/MqttDevices/{}/Capacity".format(serviceName), '0.1', 0, 9999],
        'FluidType': ["/Settings/MqttDevices/{}/FluidType".format(serviceName), 1, 0, 5]
    }

    #print(config.dbus_paths())
    dbus_paths = { key: val for (key, val) in list(config.dbus_paths()) }
    assert list(dbus_paths.keys()) == ['ProductId', 'CustomName', 'FluidType', 'Capacity', 'Level', 'Remaining']

    assert dbus_paths['CustomName'].get('default') == 'My Tank Sensor'
    assert dbus_paths['CustomName'].getboolean('persist') == True

    assert dbus_paths['Capacity'].get('description') == 'm3'
    assert dbus_paths['Capacity'].getfloat('default') == 0.1
    assert dbus_paths['FluidType'].get('description') == '0=Fuel, 1=Fresh water, 2=Waste water, 3=Live well, 4=Oil, 5=Black water (sewage)'
    assert dbus_paths['FluidType'].getint('default') == 1

