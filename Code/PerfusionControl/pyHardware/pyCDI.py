"""Panel class for streaming data from CDI saturation monitor

@project: Liver Perfusion, NIH
@author: Stephie Lux, NIH

"""
from threading import Thread, Event
from time import sleep
from queue import Queue
from enum import IntEnum
from datetime import datetime
from dataclasses import dataclass

import numpy as np
import serial
import serial.tools.list_ports

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyHardware.pyGeneric as pyGeneric


class CDIException(pyGeneric.HardwareException):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


CDIIndex = IntEnum('CDIIndex', ['arterial_pH', 'arterial_CO2', 'arterial_O2', 'arterial_temp',
                                'arterial_sO2', 'arterial_bicarb', 'arterial_BE', 'K', 'VO2',
                                'venous_pH', 'venous_CO2', 'venous_O2', 'venous_temp', 'venous_sO2',
                                'venous_bicarb', 'venous_BE', 'hct', 'hgb'], start=0)


class CDIData:
    def __init__(self, data):
        if data is not None:
            for idx in range(18):
                # self._lgr.debug(f'Setting {CDIIndex(idx).name} to {data[idx]}')
                setattr(self, CDIIndex(idx).name, data[idx])


@dataclass
class CDIConfig:
    port: str = ''
    sampling_period_ms: int = 1000


class CDI(pyGeneric.GenericDevice):
    def __init__(self, name: str):
        super().__init__(name)
        self.buf_len = 18
        self.samples_per_read = 18
        self.cfg = CDIConfig()

        self.__serial = serial.Serial()
        self._timeout = 1.0

        self._evt_halt = Event()
        self.__thread = None
        self.is_streaming = False

    @property
    def sampling_period_ms(self):
        return self.cfg.sampling_period_ms

    def is_open(self):
        return self.__serial and self.__serial.is_open

    def open(self) -> None:
        super().open()
        if self.__serial.is_open:
            self.__serial.close()
        self.__serial.port = self.cfg.port
        self.__serial.baudrate = 9600
        self.__serial.stopbits = serial.STOPBITS_ONE
        self.__serial.parity = serial.PARITY_NONE
        self.__serial.bytesize = serial.EIGHTBITS
        self.__serial.timeout = self._timeout
        try:
            self.__serial.open()
        except serial.serialutil.SerialException as e:
            self.__serial = None
            self._lgr.exception(f'CDI: Could not open serial port {self.cfg.port}')
            raise CDIException(f'CDI: Could not open serial port at {self.cfg.port}')

    def close(self):
        super().close()
        self.stop()
        if self.__serial:
            self.__serial.close()

    def parse_response(self, response: str):
        data = np.zeros(0, dtype=self.data_dtype)
        if response is None:
            return data

        fields = response.strip('\r\n').split(sep='\t')
        # in addition to codes, there is a start code, CRC, and end code
        expected_vars = max(CDIIndex).value + 1

        if len(fields) == expected_vars + 2:
            data = np.zeros(expected_vars, dtype=self.data_dtype)
            # skip first field which is SN and timestamp
            # timestamp will be ignored,  we will use the timestamp when the response arrives
            # self.timestamp = fields[0][-8:]
            for field in fields[1:-1]:
                # get code and convert string hex value to an actual integer
                code = int(field[0:2].upper(), 16)
                try:
                    value = self.data_dtype.type(field[4:])
                except ValueError:
                    # self._lgr.error(f'Field {code} (value={field[4:]}) is out-of-range')
                    value = self.data_dtype.type(-1)
                data[code] = value
        else:
            # this may be a result of an incomplete serial response.
            # Assume it is a random occurrence so log the response, but
            # do not raise the exception further. Calling code will know it is
            # a bad response due to data = None
            self._lgr.error(f'CDI: could parse CDI response, '
                            f'expected {expected_vars + 2} fields, found {len(fields)}')

        return data

    def read_from_serial(self):
        # self._lgr.debug('Attempting to read serial data from CDI')
        resp = self.__serial.read_until(expected=b'\r\n').decode('utf-8')
        return resp

    def run(self):  # continuous data stream
        self.is_streaming = True
        self._evt_halt.clear()
        good_response = False
        loops = 0
        # only wait for a second so if the MASTER HALT is set,
        # we can break out of the loop
        while not PerfusionConfig.MASTER_HALT.is_set():
            if self._evt_halt.wait(self._timeout):
                break
            if self.is_open():
                resp = ''
                try:
                    while not good_response:
                        resp += self.read_from_serial()
                        if len(resp) > 0:
                            if resp[-1] == '\n':
                                good_response = True
                                loops = 0
                            else:
                                loops += 1
                        elif loops > 10:
                            break
                except serial.SerialException:
                    self._lgr.exception(f'CDI: error attempting to read response.')
                    # assuming this is an occasional glitch so log, but keep going

                if good_response:
                    data = self.parse_response(resp)
                    ts = utils.get_epoch_ms()
                    self._queue.put((data, ts))
                    good_response = False
                else:
                    msg = f'CDI: Failed to read good response after multiple attempts. ' \
                          f'Something may be wrong with CDI interface'
                    self._lgr.error(msg)
                    raise CDIException(msg)
        self.is_streaming = False

    def start(self):
        super().start()
        self._evt_halt.clear()

        self.__thread = Thread(target=self.run)
        self.__thread.name = f'pyCDI'
        self.__thread.start()

    def stop(self):
        if self.is_streaming:
            self._evt_halt.set()
        super().stop()


class MockCDI(CDI):
    def __init__(self, name):
        super().__init__(name)
        self._is_open = False
        self.last_pkt = ''
        self.last_pkt_index = 0

    def is_open(self):
        return self._is_open

    def open(self, cfg: CDIConfig = None) -> None:
        if cfg is not None:
            self.cfg = cfg
        self._is_open = True
        self._queue = Queue()

    def close(self):
        pass

    def read_from_serial(self):
        pkt_stx = 0x2
        pkt_etx = 0x3
        pkt_dev = 'X2000A5A0'
        ts = datetime.now()
        timestamp = f'{ts.hour:02d}:{ts.minute:02d}:{ts.second:02d}'
        # self._lgr.debug(f'timestamp is {timestamp}')
        cdi_array = [idx.value*2 for idx in CDIIndex]
        cdi_array[CDIIndex.K] = 1
        data = [f'{idx.value:02x}{cdi_array[idx.value]:04d}\t' for idx in CDIIndex]
        data_str = ''.join(data)
        crc = 0
        pkt = f'{pkt_stx}{pkt_dev}{timestamp}\t{data_str}{crc}{pkt_etx}\r\n'
        rand = np.random.randint(10, size=1)[0]
        if self.last_pkt:
            pkt = self.last_pkt[self.last_pkt_index:]
            self.last_pkt_index = 0
            self.last_pkt = ''
        else:
            if rand < 5:
                self.last_pkt = pkt
                self.last_pkt_index = np.random.randint(low=0, high=len(pkt)-2, size=1)[0]
                pkt = pkt[0:self.last_pkt_index]
            else:
                self.last_pkt = ''
                self.last_pkt_index = 0
        sleep(2)
        return pkt
