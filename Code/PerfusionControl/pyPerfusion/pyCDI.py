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


class CDIParsedData:
    def __init__(self, response):
        # parse raw ASCII output
        self.response_str = str(response)
        self.fields = self.response_str.split(sep="\\t")
        
        self.analyte_codes = ("00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "0A", "0B", "0C", "0D", "0E",
                              "0F", "10", "11")
        self.arterial_pH = None
        self.arterial_CO2 = None
        self.arterial_O2 = None
        self.arterial_temp = None
        self.arterial_sO2 = None
        self.arterial_bicarb = None
        self.arterial_BE = None
        self.K = None
        self.VO2 = None
        self.venous_pH = None
        self.venous_CO2 = None
        self.venous_O2 = None
        self.venous_temp = None
        self.venous_sO2 = None
        self.venous_bicarb = None
        self.venous_BE = None
        self.hct = None
        self.hgb = None

        grouping = {self.arterial_pH,
                    self.arterial_CO2,
                    self.arterial_O2,
                    self.arterial_temp,
                    self.arterial_sO2,
                    self.arterial_bicarb,
                    self.arterial_BE,
                    self.K,
                    self.VO2,
                    self.venous_pH,
                    self.venous_CO2,
                    self.venous_O2,
                    self.venous_temp,
                    self.venous_sO2,
                    self.venous_bicarb,
                    self.venous_BE,
                    self.hct,
                    self.hgb}

        for n in range(17):
            if self.fields[n][0:2] == self.analyte_codes[n]:
                try:
                    grouping[n] = float(self.fields[n][4:])  # not sure how we can correctly assign the attributes: this is definitely wrong but this was the concept I wanted to achieve
                except self.fields[n][4] == "-":
                    print(f'Cannot read {grouping[n]}')
            else:
                print('Analyte code order not correct')
                # better way of handling this? test other n's or not worth it?
        #if self.fields[2][0:2] == "01":
            #try:
               # self.arterial_CO2 = float(self.fields[2][4:])
           # except self.fields[2][4] == "-":
              #  print("Cannot read arterial CO2")
               # self.arterial_CO2 = None
        #if self.fields[3][0:2] == "02":
           # self.arterial_O2 = float(self.fields[3][4:])
       # if self.fields[4][0:2] == "03":
            #self.arterial_temp = float(self.fields[4][4:])
       # if self.fields[5][0:2] == "04":
           # self.arterial_sO2 = float(self.fields[5][4:])
       # if self.fields[6][0:2] == "05":
           # self.arterial_bicarb = float(self.fields[6][4:])
       # if self.fields[7][0:2] == "06":
            #self.arterial_BE = float(self.fields[7][4:])
       # if self.fields[8][0:2] == "07":
          #  self.K = float(self.fields[8][4:])
       # if self.fields[9][0:2] == "08":
          #  self.VO2 = float(self.fields[9][4:])
       # if self.fields[10][0:2] == "09":
          #  self.venous_pH = float(self.fields[10][4:])
        #if self.fields[11][0:2] == "0A":
            #self.venous_CO2 = float(self.fields[11][4:])
       # if self.fields[12][0:2] == "0B":
          # self.venous_O2 = float(self.fields[12][4:])
       # if self.fields[13][0:2] == "0C":
          #  self.venous_temp = float(self.fields[13][4:])
       # if self.fields[14][0:2] == "0D":
          #  self.venous_sO2 = float(self.fields[14][4:])
        #if self.fields[15][0:2] == "0E":
           # self.venous_bicarb = float(self.fields[15][4:])
      #  if self.fields[16][0:2] == "0F":
         #   self.venous_BE = float(self.fields[16][4:])
       # if self.fields[17][0:2] == "10":
        #    self.hct = float(self.fields[17][4:])
      #  if self.fields[18][0:2] == "11":
            #self.hgb = float(self.fields[18][4:])

    # test ability to read all 3 sensors on CDI
    def print_results(self):
        print(f'Arterial pH is {self.arterial_pH}')
        print(f'Venous pH is {self.venous_pH}')
        print(f'Hemoglobin is {self.hgb}')

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
        # self.__serial.write('X08Z36'.encode(encoding='ascii'))
        self.__serial.timeout = 30.0  # if we set this higher will we get multiple packets?
        CDIPacket = self.__serial.readline()
        return CDIPacket

''' 
methods

open

stream

save as data frame

stop streaming

close
'''