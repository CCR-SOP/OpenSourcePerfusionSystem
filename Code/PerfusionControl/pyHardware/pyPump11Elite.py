# -*- coding: utf-8 -*-
""" Class for controlling a Pump 11 Elite syringe pump

    @project: LiverPerfusion NIH
    @author: John Kakareka, NIH

    This work was created by an employee of the US Federal Gov
    and under the public domain.
"""
from threading import Thread, Event
from queue import Queue, Empty
from dataclasses import dataclass
from enum import Enum
from time import sleep
from binascii import hexlify

import numpy as np
import serial
import serial.tools.list_ports

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils


class Pump11EliteException(PerfusionConfig.HardwareException):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


DATA_VERSION = 3

INFUSION_START = -2
INFUSION_STOP = -1


DEFAULT_SYRINGES = {
    'air': '1 ml\n2.5 ml\n5 ml\n10 ml\n20 ml\n30 ml\n50 ml',
    'bdg': '500 ul\n1 ml\n2.5 ml\n5 ml\n10 ml\n20 ml\n30 ml\n50 ml\n100 ml',
    'bdp': '1 ml\n3 ml\n5 ml\n10 ml\n20 ml\n30 ml\n50 ml\n60 ml',
    'cad': '250 ul\n500 ul\n1 ml\n2 ml\n3 ml\n5 ml\n10 ml\n20 ml\n30 ml\n50 ml\n100 ml',
    'cma': '1 ml\n2.5 ml\n5 ml\n10 ml',
    'hm1': '5 ul\n10 ul\n25 ul\n50 ul\n100 ul\n250 ul\n500 ul',
    'hm2': '1 ml\n1.25 ml\n2.5 ml\n5 ml\n10 ml\n25 ml\n50 ml\n100 ml',
    'hm3': '10 ul\n25 ul\n50 ul\n100 ul\n250 ul\n500 ul',
    'hm4': '0.5 ul\n1 ul\n2 ul\n5 ul',
    'has': '2.5 ml\n8 ml\n20 ml\n50 ml\n100 ml',
    'hos': '1 ml\n2 ml\n3 ml\n5 ml\n10 ml\n20 ml\n30 ml\n50 ml\n100 ml',
    'ils': '250 ul\n500 ul\n1 ml\n2.5 ml\n5 ml\n10 ml\n25 ml\n50 ml\n100 ml',
    'nip': '1 ml\n1 ml\n2.5 ml\n5 ml\n10 ml\n20 ml\n30 ml\n50 ml',
    'sge': '5 ul\n10 ul\n25 ul\n50 ul\n100 ul\n250 ul\n500 ul\n1 ml\n2.5 ml\n5 ml\n10 ml\n25 ml\n50 ml\n100 ml',
    'smp': '1 ml\n3 ml\n6 ml\n12 ml\n20 ml\n35 ml\n60 ml\n140 ml',
    'tej': '1 ml\n1 ml\n2.5 ml\n5 ml\n10 ml\n20 ml\n30 ml\n50 ml',
    'top': '1 ml\n2.5 ml\n5 ml\n10 ml\n20 ml\n30 ml\n50 ml'
}
DEFAULT_MANUFACTURERS = {
    'air':  'Air-Tite, HSW Norm-Ject',
    'bdg':  'Becton Dickinson, Glass (all types)',
    'bdp':  'Becton Dickinson, Plasti-pak',
    'cad':  'Cadence Science, Micro-Mate Glass',
    'cma':  'CMA Microdialysis, CMA',
    'hm1':  'Hamilton 700, Glass',
    'hm2':  'Hamilton 1000, Glass',
    'hm3':  'Hamilton 1700, Glass',
    'hm4':  'Hamilton 7000, Glass',
    'has':  'Harvard Apparatus, Stainless Steel',
    'hos':  'Hoshi',
    'ils':  'ILS, Glass',
    'nip':  'Nipro',
    'sge':  'Scientific Glass Engineering',
    'smp':  'Sherwood-Monoject, Plastic',
    'tej':  'Terumo Japan, Plastic',
    'top':  'Top'
    }


@dataclass
class Pump11EliteConfig:
    com_port: str = ''
    manufacturer_code: str = ''
    size: str = ''
    baud: int = 9600
    address: int = 0


PumpState = Enum('PumpState', ['idle', 'infusing', 'withdrawing', 'stalled', 'target_reached'])
PumpMap = {':': PumpState.idle, '>': PumpState.infusing, '<': PumpState.withdrawing,
           '*': PumpState.stalled, 'T*': PumpState.target_reached}


def get_available_manufacturer_codes() -> list:
    return list(DEFAULT_MANUFACTURERS.keys())


def get_available_manufacturer_names() -> list:
    return list(DEFAULT_MANUFACTURERS.values())


def get_name_from_code(code: str):
    manu_str = DEFAULT_MANUFACTURERS.get(code, '')
    return manu_str


def get_code_from_name(desired_name: str):
    code = [code for code, name in DEFAULT_MANUFACTURERS.items() if name == desired_name]
    if len(code) > 0:
        code = code[0]
    else:
        code = ''
    return code


class Pump11Elite:
    def __init__(self, name):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.data_dtype = np.dtype(np.float64)

        self.name = name
        self.cfg = Pump11EliteConfig()
        self.cfg.name = name

        self.pump_state = PumpState.idle

        self._serial = serial.Serial()
        self._serial.timeout = 0.10
        self._queue = None
        self._timeout = 0.05

        self.acq_start_ms = 0
        self.period_sampling_ms = 0
        self.samples_per_read = 0

    @property
    def is_infusing(self):
        response = self.send_wait4response('status\r')
        status = response.split(' ')[-1]
        if status == '':
            return self.pump_state
        if status[0].islower():
            self.pump_state = PumpState.idle
        elif status[0] == 'W':
            self.pump_state = PumpState.withdrawing
        elif status[0] == 'I':
            self.pump_state = PumpState.infusing
        return self.pump_state == PumpState.infusing

    def get_acq_start_ms(self):
        return self.acq_start_ms

    def is_open(self):
        return self._serial.is_open

    def read_config(self):
        PerfusionConfig.read_into_dataclass('hardware', self.name, self.cfg)
        self.open(self.cfg)

    def write_config(self):
        PerfusionConfig.write_from_dataclass('hardware', self.name, self.cfg)

    def open(self, cfg: Pump11EliteConfig = None) -> None:
        self._queue = Queue()
        if self._serial.is_open:
            self._serial.close()

        if cfg is not None:
            self.cfg = cfg
            self._serial.port = self.cfg.com_port
            self._serial.baudrate = self.cfg.baud
            self._serial.xonxoff = True
        try:
            self._serial.open()
        except serial.serialutil.SerialException as e:
            self._lgr.error(f'Could not open serial port {self._serial.port}. Message: {e}')
            raise Pump11EliteException()

        self.send_wait4response(f'address {self.cfg.address}\r')
        self.send_wait4response('poll REMOTE\r')

    def close(self):
        if self._serial:
            self.stop()
            self._serial.close()

    def send_wait4response(self, str2send: str) -> str:
        self.send_command(str2send)
        response = self.get_response()
        return response

    def send_command(self, str2send: str):
        if self._serial.is_open:
            # self._lgr.debug(f'sending {str2send}')
            self._serial.write(str2send.encode('UTF-8'))
            self._serial.flush()

    def _set_param(self, param, value):
        """ helper function to send a properly formatted parameter-value pair"""
        response = self.send_wait4response(f'{param} {value}')

    def set_infusion_rate(self, rate_ul_min: int):
        # can be changed mid-run
        self._set_param('irate', f'{int(rate_ul_min)} ul/min\r')
        self._lgr.info(f'{self.name}: Syringe infusion set at rate {rate_ul_min} uL/min')

    def clear_infusion_volume(self):
        self.send_wait4response('civolume\r')

    def get_infusion_rate(self):
        response = self.send_wait4response('irate\r')
        try:
            infuse_rate, infuse_unit = response.split(' ')
        except ValueError as e:
            # this will happen if com port is not opened or
            # an error occurred
            self._lgr.error(f'Error occurred parsing get_infusion_rate response for syringe {self.name}')
            self._lgr.error(f'Message: {e}')
            infuse_rate = 0
            infuse_unit = ''
        return infuse_rate, infuse_unit

    def set_target_volume(self, volume_ul):
        self._set_param('tvolume', f'{int(volume_ul)} ul\r')
        self._lgr.info(f'{self.name}: Target infusion volume set at {volume_ul} uL')

    def get_target_volume(self):
        response = self.send_wait4response('tvolume\r')
        if response == 'Target volume not set' or response == '':
            vol = 0
            vol_unit = ''
            # self._lgr.warning(f'Attempt to read target volume before it was set')
            # Doesn't need a warning - normal functionality during basal infusions
        else:
            try:
                vol, vol_unit = response.split(' ')
            except ValueError as e:
                # this will happen if com port is not opened or
                # an error occurred
                self._lgr.error(f'Error occurred parsing get_target_volume response for syringe {self.name}')
                self._lgr.error(f'Message: {e}')
                self._lgr.error(f'Response: {response}')
                vol = 0
                vol_unit = ''
        return vol, vol_unit

    def clear_target_volume(self):
        self.send_wait4response('ctvolume\r')

    def get_infused_volume(self):
        response = self.send_wait4response('ivolume\r')
        vol, vol_unit = response.split(' ')
        return vol, vol_unit

    def clear_syringe(self) -> None:
        self.clear_infusion_volume()
        self.clear_target_volume()

    def record_targeted_infusion(self, t):
        """ targeted infusion actions in ul and ul/min
        """
        target_vol, target_vol_unit = self.get_target_volume()
        rate, rate_unit = self.get_infusion_rate()
        if target_vol_unit == 'ul':
            pass
        elif target_vol_unit == 'ml':
            target_vol = target_vol * 1000
        elif not target_vol_unit or target_vol == 0:
            self._lgr.info(f'Please manually stop syringe pump and add a target volume to bolus')
        else:
            self._lgr.error(f'Unknown target volume unit in syringe {self.name}: {target_vol_unit}')
            target_vol = 0
        if rate_unit == 'ul/min':
            pass
        elif rate_unit == 'ml/min':
            rate = rate * 1000
        elif rate_unit == 'ul/sec':
            rate = rate * 60
        elif rate_unit == 'ml/sec':
            rate = rate * 60 * 1000
        else:
            self._lgr.error(f'Unknown rate unit in syringe {self.name}: ++{rate_unit}++')
            rate = 0

        buf = np.array([target_vol, rate], dtype=self.data_dtype)
        if self._queue:
            self._queue.put((buf, t))

    def record_continuous_infusion(self, t, start: bool):
        """ targeted infusion actions in ul and ul/min
        """
        rate, rate_unit = self.get_infusion_rate()
        if rate_unit == 'ul/min':
            pass
        elif rate_unit == 'ml/min':
            rate = rate * 1000
        elif rate_unit == 'ul/sec':
            rate = rate * 60
        elif rate_unit == 'ml/sec':
            rate = rate * 60 * 1000
        else:
            self._lgr.error(f'Unknown rate unit in syringe {self.name}: {rate_unit}')
            rate = 0

        flag = INFUSION_START if start else INFUSION_STOP
        buf = np.array([flag, rate], dtype=self.data_dtype)
        if self._queue:
            self._queue.put((buf, t))

    def infuse_to_target_volume(self):
        """ infuse a set volume. Requires a target volume to be set.
        """
        # JWK, should check if target volume is set
        self.send_wait4response('irun\r')
        t = utils.get_epoch_ms()
        self.record_targeted_infusion(t)
        self.pump_state = PumpState.infusing
        self._lgr.info(f'{self.name}: Bolus infusion started')

    def start_constant_infusion(self):
        """ start a constant infusion. Requires a target volume to be cleared.
        """
        # JWK, should check if target volume is cleared
        self.send_wait4response('irun\r')
        t = utils.get_epoch_ms()
        self.record_continuous_infusion(t, start=True)
        self.pump_state = PumpState.infusing
        self._lgr.info(f'{self.name}: Basal syringe infusion started')

    def start(self):
        pass

    def stop(self):
        """ stop an infusion. Typically, used to stop a continuous infusion
            but can be used to abort a targeted infusion
        """
        t = utils.get_epoch_ms()
        # check if targeted volume is 0, if so, then this is a continuous injection
        # so record the stop. If non-zero, then it is an attempt to abort a targeted injection
        target_vol, target_unit = self.get_target_volume()
        if target_vol == 0:
            self.record_continuous_infusion(t, start=False)
        self.send_wait4response('stop\r')
        self.pump_state = PumpState.idle

    def set_syringe(self, manu_code: str, syringe_size: str) -> None:
        self._set_param('syrm', f'{manu_code} {syringe_size}\r')
        self._lgr.info(f'Setting syringe {self.name} to manufacturer: {manu_code} and size: {syringe_size}')

    def get_syringe_info(self) -> str:
        response = self.send_wait4response('syrm\r')
        return response

    def get_manufacturer_info_from_syringe(self):
        manufacturers = {}
        response = self.send_wait4response('syrmanu ?\r')
        if response:
            # First and last values of the string are '\n'; remove these, then separate by '\n'
            resp = response[1:-1].split('\n')
            for i in range(len(resp)):
                syringe_info = resp[i]
                # Double spaces separate manufacturing code from manufacturing information
                syringe_info_separation = syringe_info.split('  ')
                try:
                    manufacturers[syringe_info_separation[0]] = syringe_info_separation[1]
                except IndexError as e:
                    self._lgr.error(f'Error parsing manufacturer info from Pump 11 Elite')
                    self._lgr.error(f'Response: {syringe_info}')
                    self._lgr.error(f'Msg: {e}')
        return manufacturers

    def get_available_syringes(self, manufacturer_code: str) -> list:
        syringes = []
        response = self.send_wait4response(f'syrmanu {manufacturer_code} ?\r')
        if response:
            # First and last values of each syringe's volume string are '\n', remove these, then separate by '\n'
            syringes = response.split('\n')
        return syringes

    def get_data(self):
        buf = None
        t = None
        try:
            buf, t = self._queue.get(timeout=1.0)
        except Empty:
            # this can occur if there are attempts to read data before it has been acquired
            # this is not unusual, so catch the error but do nothing
            pass
        return buf, t

    def get_response(self) -> str:
        resp_str = ''
        if self._serial.is_open:
            response = self._serial.read_until('\r', size=1000)
            resp_str = response.decode('ascii').strip('\r').strip('\n')
            # self._lgr.debug(f'response is ||{resp_str}||')
            # self._lgr.debug(f'response in hex is ||{hexlify(response)}')

        return resp_str


class MockPump11Elite(Pump11Elite):
    def __init__(self, name):
        super().__init__(name)
        self._lgr = utils.get_object_logger(__name__, self.name)
        self._lgr.debug(f'Creating MockPump11Elite with name {name}')
        self._serial.is_open = False
        self._values = {'tvolume': '0 ul', 'irate': '0 ul/min'}

    def open(self, cfg: Pump11EliteConfig = None) -> None:
        self.cfg = cfg
        self._queue = Queue()
        self._serial.is_open = True

    def send_command(self, str2send: str):
        pass

    def send_wait4response(self, str2send: str) -> str:
        response = ''
        if self._serial.is_open:
            # strip off trailing \r
            str2send = str2send[:-1]
            parts = str2send.split(' ', 1)
            if parts[0] == 'syrmanu':
                if parts[1] == '?':
                    response = DEFAULT_MANUFACTURERS.values()
                else:
                    code = parts[1].split(' ')[0]
                    response = DEFAULT_SYRINGES[code]
            elif parts[0] in ['tvolume', 'irate']:
                if len(parts) == 2:
                    self._values[parts[0]] = parts[1]
                else:
                    response = self._values[parts[0]]
            elif parts[0] == 'irun':
                self.pump_state = PumpState.infusing
            elif parts[0] == 'stop':
                self.pump_state = PumpState.idle

        return response

    def read_from_port(self):
        pass