# -*- coding: utf-8 -*-
""" Class for controlling a Pump 11 Elite syringe pump

    Requires a hardware object implementing the SerialInterface protocol

    @project: LiverPerfusion NIH
    @author: John Kakareka, NIH

    This work was created by an employee of the US Federal Gov
    and under the public domain.
"""

import logging
from time import perf_counter
from queue import Queue, Empty
from typing import Protocol

import numpy as np


DATA_VERSION = 3

INFUSION_START = -2
INFUSION_STOP = -1


class SerialInterface(Protocol):
    port_name: str  # e.g., 'COM1'
    baud_rate: int  # e.g., 115200

    def is_open(self) -> bool:
        """ returns true if serial port interface is opened """

    def open(self, port_name: str, baud_rate: int) -> None:
        """ opens a serial port interface using the passed parameters
            port_name and baud parameters will overwrite existing attributes if set """

    def close(self) -> None:
        """ closing an existing serial port """

    def send(self, str2send: str) -> None:
        """ sends the specified string over the serial port, if the port is opened"""

    def wait_for_string(self, max_bytes: int = 1, terminator: str = '\r', timeout: float = 1.0) -> str:
        """ returns a string from the serial port until the terminator is reached or max_bytes has been acquired
            If no response occurs within the timeout specified in seconds, then '' is returned
            This should be used when the response is a string with a defined terminator (e.g., CR/LF)
            """


class Pump11Elite:
    def __init__(self, name):
        super().__init__()
        self._lgr = logging.getLogger(__name__)
        self.data_type = np.float32

        self.name = name

        self._hw = None
        self.__addr = 0

        self._queue = None
        self.__acq_start_t = None

        self._params = {
            'File Format': DATA_VERSION,
            'Syringe': self.name,
            'Volume Unit': 'ul',
            'Rate Unit': 'ul/min',
            'Data Format': str(np.dtype(np.float32)),
            'Datapoints Per Timestamp': 2,
            'Bytes Per Timestamp': 4,
            'Start of Acquisition': 0
            }

    def set_hw(self, hw: SerialInterface) -> None:
        self._hw = hw

    def open(self, port_name: str, baud_rate: int, addr: int = 0) -> None:
        self._hw.open(port_name=port_name, baud_rate=baud_rate, xonoff=True)
        self.__addr = addr
        self._queue = Queue()

        # JWK, why do we need to send a blank?
        self.send_wait4response('')
        self._hw.send(f'address {self.__addr}\r')
        self._hw.send('poll REMOTE\r')

    def send_wait4response(self, str2send: str) -> str:
        self._hw.send(str2send)
        response = self._hw.wait_for_string(max_bytes=1000)
        # JWK, we should be checking error responses
        return response

    def _set_param(self, param, value) -> str:
        """ helper function to send a properly formatted parameter-value pair"""
        response = self.send_wait4response(f'{param} {value}')
        return response

    def set_infusion_rate(self, rate_ul_min: int):
        # can be changed mid-run
        self._set_param('irate', f'{rate_ul_min} ul/sec\r')

    def clear_infusion_volume(self):
        self.send_wait4response('civolume\r')

    def get_infusion_rate(self):
        response = self.send_wait4response('irate\r')
        infuse_rate, infuse_unit = response.split(' ')
        return infuse_rate, infuse_unit

    def set_target_volume(self, volume_ul):
        self._set_param('tvolume', f'{volume_ul} ul\r')

    def get_target_volume(self):
        response = self.send_wait4response('tvolume\r')
        vol, vol_unit = response.split(' ')
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

    def record_targeted_infusion(self, t: np.float32):
        """ targeted infusion actions in ul and ul/min
        """
        target_vol, target_vol_unit = self.get_target_volume()
        rate, rate_unit = self.get_infusion_rate()
        if target_vol_unit == 'ul':
            pass
        elif rate_unit == 'ml':
            target_vol = target_vol * 1000
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
            self._lgr.error(f'Unknown rate unit in syringe {self.name}: {rate_unit}')
            rate = 0

        buf = np.array([target_vol, rate], np.float32)
        self._queue.put((buf, t))

    def record_continuous_infusion(self, t: np.float32, start: bool):
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
        buf = np.array([flag, rate], np.float32)
        self._queue.put((buf, t))

    def infuse_to_target_volume(self):
        """ infuse a set volume. Requires a target volume to be set.
        """
        # JWK, should check if target volume is set
        self.send_wait4response('irun\r')
        t = perf_counter()
        self.record_targeted_infusion(t)

    def start_constant_infusion(self):
        """ start a constant infusion. Requires a target volume to be cleared.
        """
        # JWK, should check if target volume is cleared
        self.send_wait4response('irun\r')
        t = perf_counter()
        self.record_continuous_infusion(t, start=True)

    def stop(self):
        """ stop an infusion. Typically, used to stop a continuous infusion
            but can be used to abort a targeted infusion
        """
        self.send_wait4response('stop\r')
        t = perf_counter()
        # check if targeted volume is 0, if so, then this is a continuous injection
        # so record the stop. If non-zero, then it is an attempt to abort a targeted injection
        target_vol, target_unit = self.get_target_volume()
        if target_vol == 0:
            self.record_continuous_infusion(t, start=False)

    def set_syringe(self, manu_code: str, syringe_size: str) -> None:
        self._set_param('syrm', f'{manu_code} {syringe_size}\r')
        self._lgr.info(f'Setting syringe {self.name} to manufacturer: {manu_code} and size: {syringe_size}')

    def get_syringe_info(self) -> str:
        response = self.send_wait4response('syrm\r')
        return response

    def get_available_manufacturers(self) -> dict:
        manufacturers = {}
        response = self.send_wait4response('syrmanu ?\r')
        if response:
            # First and last values of the string are '\n'; remove these, then separate by '\n'
            resp = response[1:-1].split('\n')
            for i in range(len(resp)):
                syringe_info = resp[i]
                # Double spaces separate manufacturing code from manufacturing information
                syringe_info_separation = syringe_info.split('  ')
                manufacturers[syringe_info_separation[0]] = syringe_info_separation[1]
        return manufacturers

    def get_available_syringes(self, manufacturer_cde: str) -> list:
        syringes = []
        response = self.send_wait4response(f'syrmanu {manufacturer_cde} ?\r')
        if response:
            # First and last values of each syringe's volume string are '\n', remove these, then separate by '\n'
            syringes = response[1:-1].split('\n')
        return syringes
