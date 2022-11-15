"""Adjusts GB_100 gas mixers based on CDI output

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""

import logging
import serial
import time
from datetime import datetime

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import mcqlib_GB100.mcqlib.main as mcq

# dictionary of acceptable value ranges
physio_ranges = {'pH_lower': 7.3, 'pH_upper': 7.5,
                 'arterial_CO2_lower': 20, 'arterial_CO2_upper': 60,
                 'arterial_O2_lower': 50, 'arterial_O2_upper': 300,
                 'venous_CO2_lower': 20, 'venous_CO2_upper': 80,
                 'venous_O2_lower': 20, 'venous_O2_upper': 150}

HA_mixer = mcq.Main('Arterial Gas Mixer')
PV_mixer = mcq.Main('Venous Gas Mixer')  # Main is not configured to do this, can only do HA mixer rn

# code to turn on both mixers - or do we need this if starting manually?


class GB100_shift:
    def __init__(self, vessel, mixer):
        self.vessel = vessel  # vessel = 'HA' or 'PV'
        if self.vessel == "HA":
            self.pH_index = 0
            self.CO2_index = 1
            self.O2_index = 2
            self.CO2_lower = physio_ranges['arterial_CO2_lower']
            self.CO2_upper = physio_ranges['arterial_CO2_upper']
            self.O2_lower = physio_ranges['arterial_O2_lower']
            self.O2_upper = physio_ranges['arterial_O2_upper']
        elif self.vessel == "PV":
            self.pH_index = 9
            self.CO2_index = 10
            self.O2_index = 11
            self.CO2_lower = physio_ranges['venous_CO2_lower']
            self.CO2_upper = physio_ranges['venous_CO2_upper']
            self.O2_lower = physio_ranges['venous_O2_lower']
            self.O2_upper = physio_ranges['venous_O2_upper']

        self.mixer = mixer  # can you put an attribute that's really an object like this?
        self.co2_adjust = 3  # mmHg
        self.o2_adjust = 3  # mmHg. Changing by 3% should change pO2 by 4.65 mmHg
        self.flow_adjust = 10  # mL/min

        # determine channels and gases
        gas_types = []
        total_channels = self.mixer.get_total_channels()
        for channel in range(total_channels):
            channel = channel + 1
            print(f'{channel}')
            id_gas = mixer.get_channel_id_gas(channel)  # numeric ID
            gas_type = mcq.mcq_utils.get_gas_type(id_gas)  # gas compound names (oxygen, nitrogen, etc.)
            print(gas_type)
            gas_types += gas_type
            print(f' {gas_types}')
        self.gas_dict = {gas_types[0]: 1, gas_types[1]: 2}

    def check_pH(self, CDI_input):
        new_flow = []
        total_flow = self.mixer.get_mainboard_total_flow()
        if CDI_input[self.pH_index] < physio_ranges['pH_lower']:
            new_flow = total_flow + self.flow_adjust
        elif CDI_input[self.pH_index] > physio_ranges['pH_upper']:
             new_flow = total_flow - self.flow_adjust
        self.mixer.set_mainboard_total_flow(new_flow)

    def check_CO2(self, CDI_input):
        new_target_flow = []
        target_flow = self.mixer.get_channel_target_sccm(self.gas_dict['Carbon Dioxide'])
        if CDI_input[1] < self.CO2_lower:
            new_target_flow = target_flow + self.co2_adjust
        elif CDI_input[1] > self.CO2_upper:
            new_target_flow = target_flow - self.co2_adjust
        self.mixer.set_channel_percent_value(self.gas_dict['Carbon Dioxide'], new_target_flow)

    def check_O2(self, CDI_input):
        new_target_flow = []
        target_flow = self.mixer.get_channel_target_sccm(self.gas_dict['Oxygen'])
        if CDI_input[2] < self.O2_lower:
            new_target_flow = target_flow + self.o2_adjust
        elif CDI_input[2] > self.O2_upper:
            new_target_flow = target_flow - self.o2_adjust
        self.mixer.set_channel_percent_value(self.gas_dict['Oxygen'], new_target_flow)


# fix type problem with OXYGEN etc.
# work on error cases - you have no fixes rn
