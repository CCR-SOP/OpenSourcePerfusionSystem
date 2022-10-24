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
        self.arterial_pH = float(response_str[23:27])
        # self.arterial_CO2 = float(response_str[32:35]
        # self.arterial_O2 = float(response_str[40:43])
        self.arterial_temp = float(response_str[48:52])
        # self.arterial_bicarb = float(response_str[57:60])  # finish parsing out numbers with blood running through to accurately see values
        # self.arterial_BE = float(response_str[65:67])
        # self.calculated_O2_sat = float(response_str[72:74])
        # self.K = float(response_str[79:82])
        # self.VO2 = float(response_str[87:90])
        # self.Q = float(response_str[95:99])
        # self.BSA = float(response_str[50:53])
        # self.venous_pH = float(response_str[54:57])
        # self.venous_CO2 = float(response_str[58:61])
        # self.venous_O2 = float(response_str[61:64])
        # self.venous_temp = float(response_str[65:68])
        # self.measured_O2_sat = float(response_str[69:72])
        # self.hct = float(response_str[73:76])
        # self.hb = float(response_str[77:80])

    # test ability to read all 3 sensors on CDI
    def print_results(self):
        print(f'Arterial pH is {self.arterial_pH}')
        print(f'Temperature is {self.arterial_temp}')
        # print(f'Venous pH is {self.venous_pH}')
        # print(f'Hemoglobin is {self.hb}')


class CDIStreaming:
    def __init__(self, name):
        super().__init__()
        self._lgr = logging.getLogger(__name__)
        self.data_type = np.float32

        self.name = name

        self.__serial = serial.Serial()
        self._baud = 9600

        self._queue = None
        self.__acq_start_t = None
        self.period_sampling_ms = 0
        self.samples_per_read = 0

        self.is_streaming = False

    def is_open(self):
        return self.__serial.is_open

    def open(self, port_name: str, baud_rate: int) -> None:  # do we need baudrate as an input when we already know what it is?
        if self.__serial.is_open:
            self.__serial.close()

        self.__serial.port = port_name
        self.__serial.baudrate = baud_rate
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

    def request_data(self, timeout=0):
        # set output interval to 0 on CDI500 in order to request data
        # actually it works without this? Not sure why. Accidentally kept it set to
        expected_bytes = 160
        self.__serial.write('<X08Z36>'.encode())
        CDIPacket = self.__serial.read(expected_bytes)
        return CDIPacket

    def print_raw_results(self, CDIPacket):
        print({CDIPacket})

''' 
methods

open

stream

save as data frame

stop streaming

close
'''