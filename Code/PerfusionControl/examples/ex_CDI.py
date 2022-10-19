'''

Example script to parse single set of float(response_str from CDI saturation monitor

@project: Liver Perfusion, NIH
@author: Stephie Lux, NIH

'''

import logging
import serial

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as LP_CFG # work this in later not in example code

utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)

class CDIStreaming:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.comport = 'comport name, add later'
        # should there be something indicating this is for packet mode instead of ASCII here?
        self.baudrate = 9600
        self.parity = None
        self.__serial = serial.Serial()
        # later add something to account for rate of reading and sampling

    def open(self, comport, baudrate):
        if self.__serial.is_open:
            self.__serial.close()

        self.__serial.port = comport
        self.__serial.baudrate = baudrate
        self.__serial.open()




class Data:
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

    # SCl test ability to read all 3 sensors on CDI
    def ExampleReturn(self):
        print(f'Arterial pH is {self.arterial_pH}')
        print(f'Venous pH is {self.venous_pH}')
        print(f'Hemoglobin is {self.hb}')

cdi = CDIStreaming()
cdi.open()
unparsed = cdi.get_data()
data = Data(unparsed)
data.ExampleReturn()