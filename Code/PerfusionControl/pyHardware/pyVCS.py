# -*- coding: utf-8 -*-
"""Class for control Valve Control System
Handles opening and closing valves to direct perfusate to chemical and glucose sensors

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from itertools import cycle
from threading import Timer, Lock

from pyHardware.pyDIO import pyDIO


class VCS:
    def __init__(self, clearance_time_ms=150_000, samples_per_read=5):
        self._lgr = logging.getLogger(__name__)
        self._cycled = {}
        self._independent = {}
        self._cycled_it = None
        self._active_valve = {}
        self._clearance_time_ms = clearance_time_ms
        self._clearance_timer = {}
        self._read_timer = {}
        self._samples_per_read = samples_per_read
        self._cycled_valve_lock = Lock()
        self._sensors = {}

    def _start_clearance_timer(self, set_name):
        if set_name in self._clearance_timer.keys():
            self._clearance_timer[set_name].cancel()
            self._lgr.warning(f'Tried to start already running clearance timer for {set_name}'
                              f'Timer will be stopped and re-started')
        self._clearance_timer[set_name] = Timer(self._clearance_time_ms / 1000.0,
                                                function=self._cleared_perfusate,
                                                kwargs={'set_name': set_name})
        self._clearance_timer[set_name].start()

    def _next_chemical_sensor(self):
        with self._cycled_valve_lock:
            self._active_valve.deactivate()
            self._active_valve = next(self._cycled_inputs)
            self._active_valve.start()

    def _cleared_perfusate(self, set_name):
        if set_name in self._read_timer.keys():
            self._read_timer[set_name].cancel()
            self._lgr.warning(f'Tried to start already running read timer for {set_name}'
                              f'Timer will be stopped and re-started')
        self._read_timer[set_name] = Timer(self._read_period_ms / 1000.0,
                                           function=self._read_sensors,
                                           kwargs={'set_name': set_name})

    def _read_sensors(self, set_name):
        if set_name in self._sensors.keys():
            for sensor in self._sensors[set_name]:
                sensor.read()

    def add_cycled_input(self, set_name: str, valve_name: str, dio: pyDIO):
        self.close_cycled_valves(set_name)
        if set_name in self._cycled.keys():
            if valve_name in self._cycled[set_name].keys():
                self._lgr.warning(f'Valve {valve_name} already exists in set {set_name}.'
                                  f'Valve data will be overwritten.')
        else:
            self._cycled[set_name] = {}
            self._active_valve[set_name] = None
            self._sensors[set_name] = []
        self._cycled[set_name][valve_name] = dio
        self._cycled_it[set_name] = cycle(self._cycled[set_name])

    def add_independent_input(self, set_name: str, valve_name: str, dio: pyDIO):
        if set_name in self._independent.keys():
            if valve_name in self._independent[set_name].keys():
                self._lgr.warning(f'Valve {valve_name} already exists in set {set_name}.'
                                  f'Valve data will be overwritten.')
        else:
            self._independent[set_name] = {}
        self._independent[set_name][valve_name] = dio

    def add_chemical_sensor(self, name, sensor):
        self._chemical_sensors.update({name: sensor})

    def add_glucose_sensor(self, name, sensor):
        self._glucose_sensors.update({name: sensor})

    def close_cycled_valves(self, set_name):
        if set_name in self._cycled.keys():
            if self._clearance_timer:
                self._clearance_timer.cancel()
            with self._cycled_valve_lock:
                for valve in self._cycled[set_name]:
                    valve.close()
                self._active_valve[set_name] = None

    def close_independent_valves(self, set_name):
        if set_name in self._independent.keys():
            for valve in self._independent[set_name]:
                valve.close()

    def close_all_valves(self):
        for set_name in self._cycled.keys():
            self.close_cycled_valves(set_name)
        for set_name in self._independent.keys():
            self.close_independent_valves(set_name)

    def start_cycle(self, set_name):
        if set_name in self._cycled.keys():
            self.close_cycled_valves(set_name)
            self._active_valve[set_name] = next(self._cycled[set_name])
            self._active_valve[set_name].activate()
        else:
            self._lgr.error(f'Cannot start cycle on non-existent valve-set {set_name}')
