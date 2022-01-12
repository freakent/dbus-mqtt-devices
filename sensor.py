#!/usr/bin/python -u

import sys, os
import json
import logging
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'ext', 'velib_python'))

from dbus.mainloop.glib import DBusGMainLoop
import dbus
import gobject
from vedbus import VeDbusService

class Sensor(object):
    """ Represent a meter object on dbus. """

    def __init__(self, name, host, base, instance, cts):
        self.instance = instance
        self.cts = cts
        self.service = service = VeDbusService(
            "{}.smappee_{:02d}".format(base, instance), bus=dbusconnection())

        # Add objects required by ve-api
        service.add_path('/Management/ProcessName', __file__)
        service.add_path('/Management/ProcessVersion', VERSION)
        service.add_path('/Management/Connection', host)
        service.add_path('/DeviceInstance', instance)
        service.add_path('/ProductId', 0xFFFF) # 0xB012 ?
        service.add_path('/ProductName', "Smappee - {}".format(name))
        service.add_path('/FirmwareVersion', None)
        service.add_path('/Serial', None)
        service.add_path('/Connected', 1)

        _kwh = lambda p, v: (str(v) + 'KWh')
        _a = lambda p, v: (str(v) + 'A')
        _w = lambda p, v: (str(v) + 'W')
        _v = lambda p, v: (str(v) + 'V')

        service.add_path('/Ac/Energy/Forward', None, gettextcallback=_kwh)
        service.add_path('/Ac/Energy/Reverse', None, gettextcallback=_kwh)
        service.add_path('/Ac/L1/Current', None, gettextcallback=_a)
        service.add_path('/Ac/L1/Energy/Forward', None, gettextcallback=_kwh)
        service.add_path('/Ac/L1/Energy/Reverse', None, gettextcallback=_kwh)
        service.add_path('/Ac/L1/Power', None, gettextcallback=_w)
        service.add_path('/Ac/L1/Voltage', None, gettextcallback=_v)
        service.add_path('/Ac/L2/Current', None, gettextcallback=_a)
        service.add_path('/Ac/L2/Energy/Forward', None, gettextcallback=_kwh)
        service.add_path('/Ac/L2/Energy/Reverse', None, gettextcallback=_kwh)
        service.add_path('/Ac/L2/Power', None, gettextcallback=_w)
        service.add_path('/Ac/L2/Voltage', None, gettextcallback=_v)
        service.add_path('/Ac/L3/Current', None, gettextcallback=_a)
        service.add_path('/Ac/L3/Energy/Forward', None, gettextcallback=_kwh)
        service.add_path('/Ac/L3/Energy/Reverse', None, gettextcallback=_kwh)
        service.add_path('/Ac/L3/Power', None, gettextcallback=_w)
        service.add_path('/Ac/L3/Voltage', None, gettextcallback=_v)
        service.add_path('/Ac/Power', None, gettextcallback=_w)

        # Provide debug info about what cts make up what meter
        service.add_path('/Debug/Cts', ','.join(str(c) for c in cts))

    def set_path(self, path, value):
        if self.service[path] != value:
            self.service[path] = value

    def update(self, voltages, powers):
        totalpower = totalforward = totalreverse = 0
        for phase, ct in izip(count(), self.cts):
            # Fill in the values
            d = powers[ct]
            line = '/Ac/L{}'.format(phase+1)
            self.set_path('{}/Current'.format(line), d['current'])
            self.set_path('{}/Energy/Forward'.format(line), round(d['importEnergy']/3600000, 1))
            self.set_path('{}/Energy/Reverse'.format(line), round(d['exportEnergy']/3600000, 1))
            self.set_path('{}/Power'.format(line), d['power'])
            self.set_path('{}/Voltage'.format(line), voltages.get(phase, None))

            totalpower += d['power']
            totalforward += d['importEnergy']
            totalreverse += d['exportEnergy']

        # Update the totals
        self.set_path('/Ac/Power', totalpower)
        self.set_path('/Ac/Energy/Forward', round(totalforward/3600000, 1))
        self.set_path('/Ac/Energy/Reverse', round(totalreverse/3600000, 1))

    def __repr__(self):
        return self.__class__.__name__ + "(" + str(self.cts) + ")"

    def __del__(self):
        self.service.__del__()
