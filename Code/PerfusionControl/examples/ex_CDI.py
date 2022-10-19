'''

Example script to parse single set of packet mdoe data from CDI saturation monitor

@project: Liver Perfusion, NIH
@author: Stephie Lux, NIH

'''

import logging
import serial

import pyPerfusion.utils as utils
utils.setup_stream_logger(logging.getLogger(), logging.DEBUG) # add in debugging comments

class CDIStreaming:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._comport = 'comport name, add later'
        # should there be something indicating this is for packet mode instead of ASCII here?
        self._baudrate = 9600
        self._parity = None
        self.__serial = serial.Serial()
        # later add something to account for rate of reading and sampling

    def open(self):
        if self.__serial.is_open:
            self.__serial.close()

        self.__serial.port = self._comport
        self.__serial.baudrate = self._baudrate
        self.__serial.open()

    # how many bytes are in one timestamp's worth of data in packet mode? does the read function even get the packet correctly? look into this more
    def get_data(self, expected_bytes, timeout=0):
        if self.__serial.is_open:
            self.__serial.timeout = timeout
            CDIPacket = self.__serial.read(expected_bytes)
            return CDIPacket

class CDIRawData:
    def __init__ (self, response_str):
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
    def ExampleReturn(self):
        print(f'Arterial pH is {self.arterial_pH}')
        print(f'Venous pH is {self.venous_pH}')
        print(f'Hemoglobin is {self.hb}')

cdi = CDIStreaming()
cdi.open()
packet = cdi.get_data(1000) # temporary byte number
data = CDIRawData(packet)
data.ExampleReturn()