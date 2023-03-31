"""Panel class for streaming data from CDI saturation monitor

@project: Liver Perfusion, NIH
@author: Stephie Lux, NIH

"""
import logging
from threading import Thread, Event
from time import sleep
from queue import Queue, Empty
from enum import IntEnum
from datetime import datetime
from  dataclasses import dataclass

import numpy as np
import serial
import serial.tools.list_ports

from pyPerfusion.utils import get_epoch_ms
import pyPerfusion.PerfusionConfig as PerfusionConfig


class CDIDeviceException(Exception):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


CDIIndex = IntEnum('CDIIndex', ['arterial_pH', 'arterial_CO2', 'arterial_O2', 'arterial_temp',
                                'arterial_sO2', 'arterial_bicarb', 'arterial_BE', 'K', 'VO2',
                                'venous_pH', 'venous_CO2', 'venous_O2', 'venous_temp', 'venous_sO2',
                                'venous_bicarb', 'venous_BE', 'hct', 'hgb'], start=0)

class CDIData:
    def __init__(self, data):
        self._lgr = logging.getLogger(__name__)
        # self._lgr.debug(f'Data is {data}')
        if data is not None:
            for idx in range(18):
                # self._lgr.debug(f'Setting {CDIIndex(idx).name} to {data[idx]}')
                setattr(self, CDIIndex(idx).name, data[idx])

@dataclass
class CDIConfig:
    name: str = 'CDI'
    port: str = ''
    sampling_period_ms: int = 1000


class CDIStreaming:
    def __init__(self, name):
        self._lgr = logging.getLogger(__name__)
        self.name = name
        self._queue = Queue()
        self.data_type = np.float64
        self.buf_len = 18
        self.samples_per_read = 18
        self.acq_start_ms = 0

        self.cfg = CDIConfig()

        self.__serial = serial.Serial()
        self._timeout = 0.5

        self._event_halt = Event()
        self.__thread = None
        self.is_streaming = False

    @property
    def sampling_period_ms(self):
        return self.cfg.sampling_period_ms

    def get_acq_start_ms(self):
        return self.acq_start_ms

    def write_config(self):
        PerfusionConfig.write_from_dataclass('hardware', self.name, self.cfg)

    def read_config(self):
        cfg = CDIConfig()
        PerfusionConfig.read_into_dataclass('hardware', self.name, cfg)
        self.open(cfg)

    def is_open(self):
        return self.__serial.is_open

    def open(self, cfg: CDIConfig = None) -> None:
        self._lgr.debug('Attempting to open CDI')
        if self.__serial.is_open:
            self.__serial.close()
        if cfg is not None:
            self.cfg = cfg
        self.__serial.port = self.cfg.port
        self.__serial.baudrate = 9600
        self.__serial.stopbits = serial.STOPBITS_ONE
        self.__serial.parity = serial.PARITY_NONE
        self.__serial.bytesize = serial.EIGHTBITS
        try:
            self.__serial.open()
            self._lgr.debug('Serial port opened')
        except serial.serialutil.SerialException as e:
            self._lgr.error(f'Could not open serial port {self.__serial.portstr}')
            self._lgr.error(f'Message: {e}')
            raise CDIDeviceException(f'Could not open serial port {self.cfg.port}')
        self._queue = Queue()

    def close(self):
        if self.__serial:
            self.__serial.close()

    def parse_response(self, response: str):
        data = []
        if response is None:
            return data

        fields = response.strip('\r\n').split(sep='\t')
        # in addition to codes, there is a start code, CRC, and end code
        expected_vars = max(CDIIndex).value + 1

        if len(fields) == expected_vars + 2:
            data = np.zeros(expected_vars, dtype=self.data_type)
            # skip first field which is SN and timestamp
            # timestamp will be ignored,  we will use the timestamp when the response arrives
            # self.timestamp = fields[0][-8:]
            for field in fields[1:-1]:
                # get code and convert string hex value to an actual integer
                code = int(field[0:2].upper(), 16)
                try:
                    value = self.data_type(field[4:])
                except ValueError:
                    logging.getLogger(__name__).error(f'Field {code} (value={field[4:]}) is out-of-range')
                    value = self.data_type(-1)
                data[code] = value
        else:
            logging.getLogger(__name__).error(f'in parse_response(), could parse CDI response, '
                                              f'expected {expected_vars + 2} fields, '
                                              f'found {len(fields)}')
        return data

    def run(self):  # continuous data stream
        self.is_streaming = True
        self._event_halt.clear()
        self.__serial.timeout = self._timeout
        while not self._event_halt.is_set():
            if self.__serial.is_open:
                self._lgr.debug('Attempting to read serial data from CDI')
                resp = self.__serial.read_until(expected=b'\r\n').decode('utf-8')
                self._lgr.debug(f'got response {resp}')
                sleep(1)
                if len(resp) > 0:
                    self._lgr.debug(f'{len(resp)} > 0')
                    self._event_halt.set()
                    self._lgr.debug(f'Type: {type(resp)}')
                    if resp[-1] == '\n':
                        data = self.parse_response(resp)
                        self._lgr.debug(f'DATA ARRAY IS {data}')
                        ts = get_epoch_ms()
                        self._queue.put((data, ts))
            else:
                sleep(0.5)

    def start(self):
        self._lgr.debug('attempting to start CDI')
        self.stop()
        self._event_halt.clear()
        self.acq_start_ms = get_epoch_ms()

        self.__thread = Thread(target=self.run)
        self.__thread.name = f'pyCDI'
        self.__thread.start()
        self._lgr.debug('CDI started')

    def stop(self):
        if self.is_streaming:
            self._event_halt.set()
            self.is_streaming = False

    def get_data(self, timeout=0):
        buf = None
        t = None
        try:
            buf, t = self._queue.get(timeout=timeout)
        except Empty:
            pass
        return buf, t


class MockCDI(CDIStreaming):
    def __init__(self, name):
        self._lgr = logging.getLogger(__name__)
        super().__init__(name)
        self._is_open = False

    def is_open(self):
        return self._is_open

    def open(self, cfg: CDIConfig = None) -> None:
        if cfg is not None:
            self.cfg = cfg
        self._is_open = True
        self._queue = Queue()

    def close(self):
        pass

    def request_data(self, timeout=30):  # request single data packet
        return self._form_pkt()

    def _form_pkt(self):
        pkt_stx = 0x2
        pkt_etx = 0x3
        pkt_dev = 'X2000A5A0'
        ts = datetime.now()
        timestamp = f'{ts.hour:02d}:{ts.minute:02d}:{ts.second:02d}'
        # self._lgr.debug(f'timestamp is {timestamp}')
        data = [f'{idx.value:02x}{idx.value*2:04d}\t' for idx in CDIIndex]
        data_str = ''.join(data)
        crc = 0
        pkt = f'{pkt_stx}{pkt_dev}{timestamp}\t{data_str}{crc}{pkt_etx}\r\n'
        # self._lgr.debug(f'pkt is {pkt}')
        return pkt

    def run(self):  # continuous data stream
        self.is_streaming = True
        self._event_halt.clear()
        while not self._event_halt.is_set():
            if self._is_open:
                resp = self._form_pkt()
                data = self.parse_response(resp)
                ts = get_epoch_ms()
                self._queue.put((data, ts))
                sleep(1.0)
            else:
                sleep(0.5)
