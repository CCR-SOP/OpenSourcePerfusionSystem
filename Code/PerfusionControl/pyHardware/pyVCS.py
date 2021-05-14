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
from threading import Timer, Lock, Event, Semaphore

from pyHardware.pyDIO import pyDIO


class VCS:
    def __init__(self, clearance_time_ms=150_000):
        self._lgr = logging.getLogger(__name__)
        self._cycled = {}
        self._independent = {}
        self._cycled_it = None
        self._active_valve = {}
        self._clearance_time_ms = clearance_time_ms
        self._timer_clearance = {}
        self._timer_acq = {}
        self._cycled_valve_lock = Lock()
        self._evt_halt = Event()
        self._sensors4cycled = {}
        self._sensors4independent = {}
        self._cycled_semaphore = {}

    def _start_clearance_timer(self, set_name):
        # set_name can also be an independent valve name
        if set_name in self._timer_clearance.keys():
            self._timer_clearance[set_name].cancel()
            self._lgr.warning(f'Tried to start already running clearance timer for {set_name}'
                              f'Timer will be stopped and re-started')
        self._timer_clearance[set_name] = Timer(self._clearance_time_ms / 1000.0,
                                                function=self._cleared_perfusate,
                                                kwargs={'set_name': set_name})
        self._timer_clearance[set_name].start()

    def _cleared_perfusate(self, set_name):
        try:
            self._cycled_semaphore[set_name] = Semaphore(len(self._sensors4cycled[set_name]))
            wait_time = 0
            for sensor in self._sensors4cycled[set_name]:
                sensor.semaphore = self._cycled_semaphore[set_name]
                sensor.start()
                expected_time = sensor.expected_acq_time
                if expected_time > wait_time:
                    wait_time = expected_time
            self._timer_acq = Timer(wait_time/1000.0, function=self._wait_for_data_collection, args=(set_name,))
            self._timer_acq.start()
            self._lgr.debug(f'cleared perfusate for set {set_name}, waiting on sensor read')
        except KeyError:
            self._lgr.warning(f'No sensors were added for set {set_name}')

    def _wait_for_data_collection(self, set_name):
        self._cycled_semaphore[set_name].wait()
        self._cycle_next(set_name)

    def _cycle_next(self, set_name):
        with self._cycled_valve_lock:
            if self._active_valve[set_name]:
                self._active_valve[set_name].deactivate()
            self._active_valve[set_name] = next(self._cycled[set_name])
            self._active_valve[set_name].activate()
            self._start_clearance_timer(set_name)

    def start_cycle(self, set_name):
        if set_name in self._cycled.keys():
            self.close_cycled_valves(set_name)
            self._cycled_it[set_name] = cycle(self._cycled[set_name])
            self._cycle_next(set_name)
        else:
            self._lgr.error(f'Cannot start cycle on non-existent valve-set {set_name}')

    def add_cycled_input(self, set_name: str, valve_name: str, dio: pyDIO):
        self.close_cycled_valves(set_name)
        if set_name in self._cycled.keys():
            if valve_name in self._cycled[set_name].keys():
                self._lgr.warning(f'Valve {valve_name} already exists in set {set_name}.'
                                  f'Valve data will be overwritten.')
        else:
            self._cycled[set_name] = {}
            self._active_valve[set_name] = None
            self._sensors4cycled[set_name] = []
        self._cycled[set_name][valve_name] = dio
        self._cycled_it[set_name] = cycle(self._cycled[set_name])

    def add_independent_input(self, valve_name: str, dio: pyDIO):
        if valve_name in self._independent.keys():
            self._lgr.warning(f'Valve {valve_name} already exists.'
                              f'Valve data will be overwritten.')
        self._independent[valve_name] = dio
        self._sensors4independent[valve_name] = []

    def add_sensor_to_cycled_valves(self, set_name, sensor):
        # TODO check if sensor had already been added
        self._sensors4cycled[set_name].update(sensor)

    def add_sensor_to_independent_valves(self, valve_name, sensor):
        # TODO check if sensor had already been added
        self._sensors4cycled[valve_name].append(sensor)

    def open_independent_valve(self, valve_name):
        if valve_name in self._independent.keys():
            self._independent[valve_name].activate()
        else:
            self._lgr.warning(f'Attempted to open non-existent independent valve {valve_name}')

    def close_independent_valve(self, valve_name):
        if valve_name in self._independent.keys():
            self._independent[valve_name].deactivate()
        else:
            self._lgr.warning(f'Attempted to close non-existent independent valve {valve_name}')

    def open_all_independent_valves(self):
        for valve_name in self._independent.keys():
            self._independent[valve_name].activate()

    def close_all_independent_valves(self):
        for valve_name in self._independent.keys():
            self._independent[valve_name].deactivate()

    def close_cycled_valves(self, set_name):
        if set_name in self._cycled.keys():
            if self._timer_clearance[set_name]:
                self._timer_clearance[set_name].cancel()
            with self._cycled_valve_lock:
                for valve in self._cycled[set_name]:
                    valve.close()
                self._active_valve[set_name] = None
        else:
            self._lgr.warning(f'Attempt to close non-existent valve set {set_name}')

    def close_all_cycled_valves(self):
        for set_name in self._cycled.keys():
            self.close_cycled_valves(set_name)

    def close_all_valves(self):
        self.close_all_cycled_valves()
        self.close_all_independent_valves()
