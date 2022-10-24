"""Panel class for streaming data from CDI saturation monitor

@project: Liver Perfusion, NIH
@author: Stephie Lux, NIH

"""
import logging
from time import perf_counter
from queue import Queue, Empty

import numpy as np
import serial
import serial.tools.list_ports

from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.FileStrategy import StreamToFile

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as LP_CFG

utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
utils.configure_matplotlib_logging()


class CDIRawData:
    def __init__(self, response_str):
        self.arterial_pH = float(response_str[9:13])
        self.arterial_CO2 = float(response_str[14:18])
        self.arterial_O2 = float(response_str[19:23])
        self.arterial_temp = float(response_str[24:28])
        self.arterial_bicarb = float(response_str[29:33])
        self.arterial_BE = float(response_str[34:38])
        self.calculated_O2_sat = float(response_str[39:43])
        self.K = float(response_str[44:48])
        self.VO2 = float(response_str[49:53])
        self.Q = float(response_str[54:58])
        self.BSA = float(response_str[59:63])
        self.venous_pH = float(response_str[64:68])
        self.venous_CO2 = float(response_str[69:73])
        self.venous_O2 = float(response_str[74:78])
        self.venous_temp = float(response_str[79:83])
        self.measured_O2_sat = float(response_str[84:87])
        self.hct = float(response_str[89:92])
        self.hb = float(response_str[94:99])

    # test ability to read all 3 sensors on CDI
    def print_results(self):
        print(f'Arterial pH is {self.arterial_pH}')
        print(f'Venous pH is {self.venous_pH}')
        print(f'Hemoglobin is {self.hb}')


class CDIStreaming:
    def __init__(self, name):
        super().__init__()
        self._lgr = logging.getLogger(__name__)
        self.data_type = np.float32

        self.name = name

        self._serial = serial.Serial()
        self._baud = 9600

        self._queue = None
        self.__acq_start_t = None
        self.period_sampling_ms = 0
        self.samples_per_read = 0

        self.is_streaming = False

    def is_open(self):
        return self._serial.is_open

    def open(self, port_name: str, baud_rate: int) -> None:
        if self._serial.is_open:
            self._serial.close()

        self._serial.port = port_name
        self._serial.baudrate = baud_rate
        self._serial.stopbits = serial.STOPBITS_ONE
        self._serial.parity = serial.PARITY_NONE
        self._serial.bytesize = serial.EIGHTBITS

        try:
            self._serial.open()
        except serial.serialutil.SerialException as e:
            self._lgr.error(f'Could not open serial port {self._serial.portstr}')
            self._lgr.error(f'Message: {e}')
        self._queue = Queue()

    def close(self):
        if self._serial:
            self._serial.close()

    def request_data(self, timeout=0):
        # set output interval to 0 on CDI500 in order to request data
        self._serial.write('<X08Z36>')
        CDIPacket = self.__serial.read(self._serial.bytesize)
        return CDIPacket

''' 
methods

open

stream

save as data frame

stop streaming

close
'''