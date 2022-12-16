"""Adjusts GB_100 gas mixers based on CDI output

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""

import logging
import time
from datetime import datetime

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import mcqlib_GB100.mcqlib.main as mcq

PerfusionConfig.set_test_config()
utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
utils.configure_matplotlib_logging()

# dictionary of acceptable value ranges
physio_ranges = {'pH_lower': 7.3, 'pH_upper': 7.5,
                 'arterial_CO2_lower': 20, 'arterial_CO2_upper': 60,
                 'arterial_O2_lower_so2': 90, 'arterial_O2_upper_so2': 100,
                 'venous_CO2_lower': 20, 'venous_CO2_upper': 80,
                 'venous_O2_lower_so2': 60, 'venous_O2_upper_so2': 92}

class GB100_shift:
    def __init__(self, vessel, mixer):
        self._logger = logging.getLogger(__name__)
        self.vessel = vessel  # vessel = "HA" or "PV"
        if self.vessel == "HA":
            self.pH_index = 0
            self.CO2_index = 1
            self.sO2_index = 4
            self.CO2_lower = physio_ranges['arterial_CO2_lower']
            self.CO2_upper = physio_ranges['arterial_CO2_upper']
            self.O2_lower = physio_ranges['arterial_O2_lower_so2']
            self.O2_upper = physio_ranges['arterial_O2_upper_so2']
        elif self.vessel == "PV":
            self.pH_index = 9
            self.CO2_index = 10
            self.sO2_index = 13
            self.CO2_lower = physio_ranges['venous_CO2_lower']
            self.CO2_upper = physio_ranges['venous_CO2_upper']
            self.O2_lower = physio_ranges['venous_O2_lower_so2']
            self.O2_upper = physio_ranges['venous_O2_upper_so2']

        self.mixer = mixer
        self.co2_adjust = 5
        self.o2_adjust = 3  # Changing by 3% should change pO2 by 4.65 mmHg
        self.flow_adjust = 10  # mL/min

        # Establish channels and gases
        gas_types = list()
        total_channels = self.mixer.get_total_channels()
        for channel in range(total_channels):
            channel = channel + 1
            id_gas = mixer.get_channel_id_gas(channel)  # numeric ID
            gas_type = mcq.mcq_utils.get_gas_type(id_gas)  # gas compound names (oxygen, nitrogen, etc.)
            if gas_type == "Air":
                self._logger.error(f'Gas type is set to {gas_type}. Please set to Oxygen, Carbon Dioxide, or Nitrogen.')
            gas_types.append(gas_type)
        self.gas_dict = {gas_types[0]: 1, gas_types[1]: 2}

    def check_pH(self, CDI_input):
        new_flow = []
        total_flow = self.mixer.get_mainboard_total_flow()
        if CDI_input[self.pH_index] < physio_ranges['pH_lower']:
            new_flow = total_flow + self.flow_adjust
        elif CDI_input[self.pH_index] > physio_ranges['pH_upper']:
             new_flow = total_flow - self.flow_adjust
        self.mixer.set_mainboard_total_flow(new_flow)

    def check_CO2(self, CDI_input):  # can only adjust CO2 in HA
        if self.vessel == "HA":
            new_percentage_mix = []
            percentage_mix = self.mixer.get_channel_percent_value(self.gas_dict['Carbon Dioxide'])
            if 0 < percentage_mix < 100:
                if CDI_input[self.CO2_index] < self.CO2_lower:
                    new_percentage_mix = percentage_mix + self.co2_adjust
                elif CDI_input[self.CO2_index] > self.CO2_upper:
                    new_percentage_mix = percentage_mix - self.co2_adjust
                self.mixer.set_channel_percent_value(self.gas_dict['Carbon Dioxide'], new_percentage_mix)
            else:
                self._logger.debug(f'CO2 % is at {percentage_mix} and cannot be changed automatically')
        else:
            self._logger.debug(f'Cannot update CO2 in PV - gas mix only contains N2 and O2. Increasing total flow by '
                               f'10 mL/min to blow off more CO2. Adjust total flow for continued changes')
            total_flow = self.mixer.get_mainboard_total_flow()
            new_flow = total_flow + 10
            self.mixer.set_mainboard_total_flow(new_flow)

    def check_O2(self, CDI_input):
        new_percentage_mix = []
        percentage_mix = self.mixer.get_channel_percent_value(self.gas_dict['Oxygen'])
        if 0 < percentage_mix < 100:
            if CDI_input[self.sO2_index] < self.O2_lower:
                new_percentage_mix = percentage_mix + self.o2_adjust
            elif CDI_input[self.sO2_index] > self.O2_upper:
                new_percentage_mix = percentage_mix - self.o2_adjust
            self.mixer.set_channel_percent_value(self.gas_dict['Oxygen'], new_percentage_mix)
        else:
            self._logger.debug(f'Oxygen % is at {percentage_mix} and cannot be further changed')

# continue working on error cases
