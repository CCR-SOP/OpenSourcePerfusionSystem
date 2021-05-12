# -*- coding: utf-8 -*-
"""Class for control Valve Control System
Handles opening and closing valves to direct perfusate to chemical and glucose sensors

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from itertools import cycle
from threading import Timer, Lock

from pyHardware.pyDIO import pyDIO


class VCS:
    def __init__(self, clearance_time_ms=150_000, samples_per_read=5):
        self._cycled_inputs = {}
        self._chemical_valves = {}
        self._glucose_valves = {}
        self._chemical_sensors = {}
        self._glucose_sensors = {}
        self._active_valve = None
        self._clearance_time_ms = clearance_time_ms
        self._clearance_timer = None
        self._read_timer = None
        self._samples_per_read = samples_per_read
        self._cycled_valve_lock = Lock()

    def _start_clearance_timer(self):
        self._clearance_timer = Timer(self._clearance_time_ms / 1000.0, function=self._cleared_perfusate)
        self._clearance_timer.start()

    def _next_chemical_sensor(self):
        with self._cycled_valve_lock:
            self._active_valve.deactivate()
            self._active_valve = next(self._cycled_inputs)
            self._active_valve.start()

    def _cleared_perfusate(self):
        self._read_timer = Timer(self._read_period_ms / 1000.0, function=self._read_sample)


    def add_chemical_valves(self, ha_dio, pv_dio, ivc_dio):
        with self._cycled_valve_lock:
            self._chemical_valves = {'Hepatic Artery': ha_dio,
                                     'Portal Vein': pv_dio,
                                     'Inferior Vena Cava': ivc_dio}
            self._cycled_inputs = cycle(self._chemical_valves)

    def add_glucose_valves(self, ha_dio, pv_dio, ivc_dio):
        self._glucose_valves = {'Hepatic Artery', ha_dio,
                                'Portal Vein', pv_dio,
                                'Inferior Vena Cava', ivc_dio}

    def add_chemical_sensor(self, name, sensor):
        self._chemical_sensors.update({name: sensor})

    def add_glucose_sensor(self, name, sensor):
        self._glucose_sensors.update({name: sensor})


    def close_chemical_valves(self):
        if self._clearance_timer:
            self._clearance_timer.cancel()
        with self._cycled_valve_lock:
            for valve in self._chemical_valves:
                valve.close()

    def close_glucose_valves(self):
        for valve in self._glucose_valves:
            valve.close()
        self._active_valve = None

    def close_all_valves(self):
        self.close_chemical_valves()
        self.close_glucose_valves()

    def start_cycle(self):
        self.close_chemical_valves()
        self._active_valve = next(self._cycled_inputs)
        self._active_valve.activate()
