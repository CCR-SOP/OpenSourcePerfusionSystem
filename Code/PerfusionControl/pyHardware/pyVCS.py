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
from threading import Timer, Lock, Event
from time import sleep

from pyHardware.pyDIO import DIO
from pyHardware.pyAO import AO


class VCSPump:
    def __init__(self, ao: AO):
        self._ao = ao
        self._speed = 0
        self._active = False

    @property
    def active(self):
        return self._active

    def set_speed(self, speed: int):
        self._speed = speed

    def start(self):
        volts = self._speed / 100.0 * 5
        self._ao.set_dc(volts)
        self._active = True

    def stop(self):
        self._ao.set_dc(0)
        self._active = False


class VCS:
    def __init__(self, clearance_time_ms=150_000):
        self._lgr = logging.getLogger(__name__)
        self._cycled = {}
        self._independent = {}
        self._cycled_it = {}
        self._active_valve = {}
        self._clearance_time_ms = clearance_time_ms
        self._timer_clearance = {}
        self._timer_acq = {}
        self._cycled_valve_lock = Lock()
        self._evt_halt = Event()
        self._sensors4cycled = {}
        self._sensors4independent = {}
        self._cycle_active = {}
        self._notify = {}
        self._pump = None

    def _start_clearance_timer(self, set_name):
        if not self._cycle_active[set_name]:
            self._lgr.debug(f'Attempted to start clearance timer for inactive cycle {set_name}')
            return
        self._lgr.debug(f'starting clearance timer for {set_name} for {self._clearance_time_ms}')
        # set_name can also be an independent valve name
        if set_name in self._timer_clearance.keys():
            if self._timer_clearance[set_name]:
                self._timer_clearance[set_name].cancel()
                self._lgr.warning(f'Tried to start already running clearance timer for {set_name}. '
                                  f'Timer will be stopped and re-started')
        self._timer_clearance[set_name] = Timer(self._clearance_time_ms / 1000.0,
                                                function=self._cleared_perfusate,
                                                kwargs={'set_name': set_name})
        if self._pump:
            self._pump.start()
        self._timer_clearance[set_name].start()

    def _cleared_perfusate(self, set_name):
        try:
            if not self._cycle_active[set_name]:
                self._lgr.debug(f'Cycle {set_name} inactive in _cleared_perfusate')
                return
        except KeyError:
            self._lgr.debug(f'No set name {set_name} in _cleared_perfusate')
        try:
            self._pump.stop()
            self._lgr.debug(f'perfusate cleared for {set_name}')
            self._timer_clearance[set_name] = None
            key = f'{set_name}:{self._active_valve[set_name].name}'
            sensor = self._sensors4cycled[set_name][0]
            self._lgr.debug(f'setting to notify = {self._notify.get(key, None)}')
            sensor.hw.start(notify=self._notify.get(key, None))
            wait_time = sensor.hw.expected_acq_time
            self._timer_acq[set_name] = Timer(wait_time/1000.0, function=self._wait_for_data_collection, args=(set_name,))
            self._timer_acq[set_name].start()
        except KeyError:
            self._lgr.warning(f'No sensors were added for set {set_name}')

    def _wait_for_data_collection(self, set_name):
        while not self._evt_halt.is_set():
            try:
                if not self._cycle_active[set_name]:
                    self._lgr.debug(f'Cycle {set_name} inactive in _wait_for_data_collection, '
                                    f'ending wait')
                    break
            except KeyError:
                self._lgr.debug(f'No set name {set_name} in _wait_for_data_collection ')
            else:
                self._timer_acq[set_name] = None
                # TODO, this is a busy wait, replace with event/semaphore
                done = self._sensors4cycled[set_name][0].hw.is_done()
                if done:
                    self._lgr.debug(f'read sensor data for {set_name}')
                    self._cycle_next(set_name)
                    break
                else:
                    sleep(0.1)

    def _cycle_next(self, set_name):
        self._lgr.debug(f'cycling {set_name}')
        try:
            if not self._cycle_active[set_name]:
                self._lgr.debug(f'Cycle {set_name} inactive in _cycle_next')
        except KeyError:
            self._lgr.debug(f'No set name {set_name} in _cycle_next ')
        else:
            with self._cycled_valve_lock:
                if self._active_valve[set_name]:
                    self._lgr.debug(f'Deactivating {self._active_valve[set_name].name} in {set_name}')
                    self._active_valve[set_name].deactivate()
                self._active_valve[set_name] = next(self._cycled_it[set_name])
                self._lgr.debug(f'Activating {self._active_valve[set_name].name} in {set_name}')
                self._active_valve[set_name].activate()
                self._start_clearance_timer(set_name)

    def start_cycle(self, set_name):
        if set_name in self._cycled.keys():
            self._evt_halt.clear()
            self.close_cycled_valves(set_name)
            self._cycled_it[set_name] = cycle(self._cycled[set_name])
            self._cycle_active[set_name] = True
            self._cycle_next(set_name)
        else:
            self._lgr.error(f'Cannot start cycle on non-existent valve-set {set_name}')

    def stop_cycle(self, set_name):
        self._evt_halt.set()
        self._pump.stop()
        if set_name in self._cycled.keys():
            self._cycle_active[set_name] = False
        self.close_cycled_valves(set_name)

    def stop(self):
        if self._pump:
            self._pump.stop()
        self._evt_halt.set()
        self.close_all_valves()

    def add_cycled_input(self, set_name: str, dio: DIO):
        # TODO if cycle active, don't allow adding more inputs
        self.close_cycled_valves(set_name)
        if set_name not in self._cycled.keys():
            self._cycled[set_name] = []
        self._active_valve[set_name] = None
        self._sensors4cycled[set_name] = []
        self._cycled[set_name].append(dio)
        self._lgr.debug(f'# of cycled inputs is {len(self._cycled[set_name])}')

    def add_independent_input(self, dio: DIO):
        if dio.name in self._independent.keys():
            self._lgr.warning(f'Valve {dio.name} already exists.'
                              f'Valve data will be overwritten.')
        self._independent[dio.name] = dio
        dio.deactivate()
        self._sensors4independent[dio.name] = []

    def add_sensor_to_cycled_valves(self, set_name, sensor):
        # TODO check if sensor had already been added
        self._sensors4cycled[set_name].append(sensor)

    def add_sensor_to_independent_valves(self, valve_name, sensor):
        # TODO check if sensor had already been added
        self._sensors4cycled[valve_name].append(sensor)

    def open_independent_valve(self, valve_name):
        self._lgr.debug(f'Opening independent valve {valve_name}')
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
            if set_name in self._timer_clearance.keys():
                if self._timer_clearance[set_name]:
                    self._timer_clearance[set_name].cancel()
            with self._cycled_valve_lock:
                for dio in self._cycled[set_name]:
                    dio.deactivate()
                self._active_valve[set_name] = None
        else:
            self._lgr.warning(f'Attempt to close non-existent valve set {set_name}')

    def close_all_cycled_valves(self):
        self._evt_halt.set()
        for set_name in self._cycled.keys():
            self.close_cycled_valves(set_name)

    def close_all_valves(self):
        self.close_all_cycled_valves()
        self.close_all_independent_valves()

    def add_notify(self, set_name, group_name, notify):
        key = f'{set_name}:{group_name}'
        self._notify.update({key: notify})

    def set_pump(self, pump: VCSPump):
        self._pump = pump
        self._pump.stop()
