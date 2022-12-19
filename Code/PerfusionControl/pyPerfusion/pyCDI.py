"""Panel class for streaming data from CDI saturation monitor

@project: Liver Perfusion, NIH
@author: Stephie Lux, NIH

"""
import logging
from threading import Thread, Lock, Event
from time import perf_counter, sleep
from queue import Queue, Empty
from dataclasses import dataclass

import numpy as np
import serial
import serial.tools.list_ports

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig


utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
utils.configure_matplotlib_logging()

code_mapping = {'00': 'arterial_pH', '01': 'arterial_CO2', '02': 'arterial_O2', '03': 'arterial_temp',
                '04': 'arterial_sO2', '05': 'arterial_bicarb', '06': 'arterial_BE', '07': 'K', '08': 'VO2',
                '09': 'venous_pH', '0A': 'venous_CO2', '0B': 'venous_O2', '0C': 'venous_temp', '0D': 'venous_sO2',
                '0E': 'venous_bicarb', '0F': 'venous_BE', '10': 'hct', '11': 'hgb'}


class CDIParsedData:
    def __init__(self, response):
        self.valid_data = False
        # parse raw ASCII output
        if response is None:
            return
        fields = response.strip('\r\n').split(sep='\t')
        # in addition to codes, there is a header packet
        # CRC and end packet
        if len(fields) == len(code_mapping) + 2:
            # skip first field which is SN and timestamp
            # timestamp will be ignored and will use the timestamp when the response arrives
            # self.timestamp = fields[0][-8:]
            for field in fields[1:-1]:
                code = field[0:2].upper()
                try:
                    # logging.getLogger(__name__).debug(f'code is {code}')
                    value = float(field[4:])
                except ValueError:
                    # logging.getLogger(__name__).error(f'Field {code} (value={field[4:]}) is out-of-range')
                    value = -1
                if code in code_mapping.keys():
                    setattr(self, code_mapping[code], value)
            self.valid_data = True
        else:
            logging.getLogger(__name__).error(f'Could parse CDI data, '
                                              f'expected {len(code_mapping) + 2} fields, '
                                              f'found {len(fields)}')

    def get_array(self):
        data = [getattr(self, value) for value in code_mapping.values()]
        return data

    # test ability to read all 3 sensors on CDI - delete eventually
    # def print_results(self):
        # if self.valid_data:
            # print(f'Arterial pH is {self.arterial_pH}')
            # print(f'Venous pH is {self.venous_pH}')
            # print(f'Hemoglobin is {self.hgb}')
        # else:
            # print('No valid data to print')


@dataclass
class CDIConfig:
    name: str = 'CDI'
    port: str = ''
    sampling_period_ms: int = 1000


class CDIStreaming:
    def __init__(self, name):
        self._lgr = logging.getLogger(__name__)
        self.name = name
        self._queue = None
        self.data_type = np.float32
        self.buf_len = 18
        self.samples_per_read = 18

        self.cfg = CDIConfig()

        self.__serial = serial.Serial()
        self._timeout = 0.5

        self._event_halt = Event()
        self.__thread = None
        self.is_streaming = False

    @property
    def sampling_period_ms(self):
        return self.cfg.sampling_period_ms

    def write_config(self):
        PerfusionConfig.write_from_dataclass('hardware', self.name, self.cfg)

    def read_config(self):
        cfg = CDIConfig()
        PerfusionConfig.read_into_dataclass('hardware', self.name, cfg)
        self.open(cfg)

    def is_open(self):
        return self.__serial.is_open

    def open(self, cfg: CDIConfig = None) -> None:
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
        except serial.serialutil.SerialException as e:
            self._lgr.error(f'Could not open serial port {self.__serial.portstr}')
            self._lgr.error(f'Message: {e}')
        self._queue = Queue()

    def close(self):
        if self.__serial:
            self.__serial.close()

    def request_data(self, timeout=30):  # request single data packet
        if self.__serial.is_open:
            self.__serial.timeout = timeout
            CDIpacket = self.__serial.readline().decode('ascii')
        else:
            CDIpacket = None
        return CDIpacket

    def run(self):  # continuous data stream
        self.is_streaming = True
        self._event_halt.clear()
        self.__serial.timeout = self._timeout
        while not self._event_halt.is_set():
            if self.__serial.is_open and self.__serial.in_waiting > 0:
                resp = self.__serial.readline().decode('ascii')
                one_cdi_packet = CDIParsedData(resp)
                ts = perf_counter()
                self._queue.put((one_cdi_packet, ts))
            else:
                sleep(0.5)

    def start(self):
        self.stop()
        self._event_halt.clear()

        self.__thread = Thread(target=self.run)
        self.__thread.name = f'pyCDI'
        self.__thread.start()

    def stop(self):
        if self.is_streaming:
            self._event_halt.set()
            self.is_streaming = False

    def get_data(self, timeout=0):  # from Pump11Elite. Might make sense so have this in the CDIParsedData class?
        buf = None  # not sure what buf and t do?
        t = None
        try:
            buf, t = self._queue.get(timeout)
        except Empty:
            pass
        return buf, t