# -*- coding: utf-8 -*-
""" Class for controlling a Pump 11 Elite syringe pump

    @project: LiverPerfusion NIH
    @author: John Kakareka, NIH

    This work was created by an employee of the US Federal Gov
    and under the public domain.
"""

import logging
from time import perf_counter
from queue import Queue, Empty

import numpy as np
import serial
import serial.tools.list_ports


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
DEFAULT_MANUFACTURERS_STR = \
"""
air  Air-Tite, HSW Norm-Ject
bdg  Becton Dickinson, Glass (all types)
bdp  Becton Dickinson, Plasti-pak
cad  Cadence Science, Micro-Mate Glass
cma  CMA Microdialysis, CMA
hm1  Hamilton 700, Glass
hm2  Hamilton 1000, Glass
hm3  Hamilton 1700, Glass
hm4  Hamilton 7000, Glass
has  Harvard Apparatus, Stainless Steel
hos  Hoshi
ils  ILS, Glass
nip  Nipro
sge  Scientific Glass Engineering
smp  Sherwood-Monoject, Plastic
tej  Terumo Japan, Plastic
top  Top
"""

# utility function to return all available comports in a list
# typically used in a GUI to provide a selection of com ports
def get_avail_com_ports() -> list:
    ports = [comport.device for comport in serial.tools.list_ports.comports()]
    return ports


class Pump11Elite:
    def __init__(self, name):
        super().__init__()
        self._lgr = logging.getLogger(__name__)
        self.data_type = np.float32

        self.name = name

        self._serial = serial.Serial()
        self.__addr = 0

        self._queue = None
        self.__acq_start_t = None
        self.period_sampling_ms = 0
        self.samples_per_read = 0

        # JWK, this should be tied to actual hardware
        self.is_infusing = False

        self._params = {
            'File Format': DATA_VERSION,
            'Syringe': self.name,
            'Volume Unit': 'ul',
            'Rate Unit': 'ul/min',
            'Data Format': str(np.dtype(np.int32)),
            'Datapoints Per Timestamp': 2,
            'Bytes Per Timestamp': 4,
            'Start of Acquisition': 0
            }

    def is_open(self):
        return self._serial.is_open

    def open(self, port_name: str, baud_rate: int, addr: int = 0) -> None:
        if self._serial.is_open:
            self._serial.close()

        self._serial.port = port_name
        self._serial.baudrate = baud_rate
        self._serial.xonxoff = True
        try:
            self._serial.open()
        except serial.serialutil.SerialException as e:
            self._lgr.error(f'Could not open serial port {self._serial.portstr}')
            self._lgr.error(f'Message: {e}')
        self.__addr = addr
        self._queue = Queue()

        # JWK, why do we need to send a blank?
        self.send_wait4response('')
        self.send_wait4response(f'address {self.__addr}\r')
        self.send_wait4response('poll REMOTE\r')

    def close(self):
        if self._serial:
            self.stop()
            self._serial.close()

    def send_wait4response(self, str2send: str) -> str:
        response = ''
        if self._serial.is_open:
            self._serial.write(str2send.encode('UTF-8'))
            self._serial.flush()
            response = ''
            self._serial.timeout = 1.0
            response = self._serial.read_until('\r', size=1000).decode('UTF-8')
        # JWK, we should be checking error responses
        # strip starting \r and ending \r
        return response[1:-1]

    def _set_param(self, param, value) -> str:
        """ helper function to send a properly formatted parameter-value pair"""
        response = self.send_wait4response(f'{param} {value}')
        return response

    def set_infusion_rate(self, rate_ul_min: int):
        # can be changed mid-run
        self._set_param('irate', f'{int(rate_ul_min)} ul/min\r')

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

    def get_target_volume(self):
        response = self.send_wait4response('tvolume\r')
        self._lgr.debug(f'get_target_volume: response={response}')
        try:
            vol, vol_unit = response.split(' ')
        except ValueError as e:
            # this will happen if com port is not opened or
            # an error occurred
            self._lgr.error(f'Error occurred parsing get_target_volume response for syringe {self.name}')
            self._lgr.error(f'Message: {e}')
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

    def record_targeted_infusion(self, t: np.float32):
        """ targeted infusion actions in ul and ul/min
        """
        target_vol, target_vol_unit = self.get_target_volume()
        rate, rate_unit = self.get_infusion_rate()
        if target_vol_unit == 'ul':
            pass
        elif target_vol_unit == 'ml':
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
            self._lgr.error(f'Unknown rate unit in syringe {self.name}: ++{rate_unit}++')
            rate = 0

        buf = np.array([target_vol, rate], np.int32)
        if self._queue:
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
        if self._queue:
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
        self.is_infusing = True

    def stop(self):
        """ stop an infusion. Typically, used to stop a continuous infusion
            but can be used to abort a targeted infusion
        """
        self.send_wait4response('stop\r')
        self.is_infusing = False
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

    def get_data(self, ch_id=None):
        buf = None
        t = None
        try:
            buf, t = self._queue.get(timeout=1.0)
        except Empty:
            # this can occur if there are attempts to read data before it has been acquired
            # this is not unusual, so catch the error but do nothing
            pass
        return buf, t


class MockPump11Elite(Pump11Elite):
    def __init__(self, name):
        super().__init__(name)
        self._serial.is_open = False
        self._values = {'tvolume': '0 ul', 'irate': '0 ul/min'}

    def open(self, port_name: str, baud_rate: int, addr: int = 0) -> None:
        self.__addr = addr
        self._queue = Queue()
        self._serial.is_open = True

    def send_wait4response(self, str2send: str) -> str:
        response = ''
        if self._serial.is_open:
            # strip off trailing \r
            str2send = str2send[:-1]
            parts = str2send.split(' ', 1)
            if parts[0] == 'syrmanu':
                if parts[1] == '?':
                    response = DEFAULT_MANUFACTURERS_STR
                else:
                    code = parts[1].split(' ')[0]
                    response = DEFAULT_SYRINGES[code]
            elif parts[0] in ['tvolume', 'irate']:
                if len(parts) == 2:
                    self._values[parts[0]] = parts[1]
                else:
                    response = self._values[parts[0]]

        # JWK, we should be checking error responses
        return response