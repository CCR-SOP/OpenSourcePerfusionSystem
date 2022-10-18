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

class CDIStreaming:
    def __init__(self, name): # find a good tutorial on this
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

        self.is_streaming = False

    def is_open(self):
        return self._serial.is_open

    def open(self, port_name: str, baud_rate: int, addr: int = 0) -> None: #how do we get port name, baudrate, etc.?
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

    def stream_data(self): # this is probably wrong

        self._serial.flushInput()
        self._serial.flushOutput()
        while True:
            bytesToRead = self._serial.inWaiting()
            data = self._serial.read(bytesToRead)
            return data # need to make this a data frame
''' 
methods

open

stream

save as data frame

stop streaming

close
'''