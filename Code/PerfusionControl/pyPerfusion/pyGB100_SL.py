"""Adjusts GB_100 gas mixers based on CDI output

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""

import logging
import serial

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import mcqlib_GB100.mcqlib.main as mcq

PerfusionConfig.set_test_config()
utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
utils.configure_matplotlib_logging()

# dictionary of acceptable value ranges
physio_ranges = {'pH_lower': 7.3, 'pH_upper': 7.5,
                 'arterial_CO2_lower': 20, 'arterial_CO2_upper': 60,
                 'arterial_O2_lower_so2': 90, 'arterial_O2_upper_so2': 100,
                 'venous_CO2_lower': 20, 'venous_CO2_upper': 80,
                 'venous_O2_lower_so2': 60, 'venous_O2_upper_so2': 92}


class GasControl:
    def __init__(self):
        self._lgr = logging.getLogger(__name__)
        self.HA = GasDevice('HA')
        self.PV = GasDevice('PV')


class GasDevice:
    def __init__(self, channel_type):
        self._lgr = logging.getLogger(__name__)
        self.channel_type = channel_type  # channel_type = "HA" or "PV"

        if self.channel_type == "HA":
            try:
                self.gb100 = mcq.Main('Arterial Gas Mixer')
            except serial.serialutil.SerialException:
                self.gb100 = None
            self.pH_index = 0
            self.CO2_index = 1
            self.sO2_index = 4
            self.CO2_lower = physio_ranges['arterial_CO2_lower']
            self.CO2_upper = physio_ranges['arterial_CO2_upper']
            self.O2_lower = physio_ranges['arterial_O2_lower_so2']
            self.O2_upper = physio_ranges['arterial_O2_upper_so2']
        elif self.channel_type == "PV":
            try:
                self.gb100 = mcq.Main('Venous Gas Mixer')
            except serial.serialutil.SerialException:
                self.gb100 = None
            self.pH_index = 9
            self.CO2_index = 10
            self.sO2_index = 13
            self.CO2_lower = physio_ranges['venous_CO2_lower']
            self.CO2_upper = physio_ranges['venous_CO2_upper']
            self.O2_lower = physio_ranges['venous_O2_lower_so2']
            self.O2_upper = physio_ranges['venous_O2_upper_so2']
        else:
            self.gb100 = None
        self.co2_adjust = 5
        self.o2_adjust = 3  # Changing by 3% should change pO2 by 4.65 mmHg
        self.flow_adjust = 10  # mL/min

    def get_gas_type(self, numeric_id):
        if self.gb100 is not None:
            channel_id = self.gb100.get_channel_id_gas(numeric_id)
            gas_type = mcq.mcq_utils.get_gas_type(channel_id)
        else:
            gas_type = 'NA'
        return gas_type

    def get_total_channels(self):
        if self.gb100 is not None:
            channels = self.gb100.get_total_channels()
        else:
            channels = 0
        return channels

    def get_total_flow(self):
        if self.gb100 is not None:
            total_flow = self.gb100.get_mainboard_total_flow()
        else:
            total_flow = 0
        return total_flow

    def set_total_flow(self, total_flow):
        if self.gb100 is not None:
            self.gb100.set_mainboard_total_flow(int(total_flow))

    def get_percent_value(self, channel_number):
        if self.gb100 is not None:
            mix_percent = self.gb100.get_channel_percent_value(channel_number)
        else:
            mix_percent = 0
        return mix_percent

    def set_percent_value(self, channel_number, new_percent):
        if self.gb100 is not None:
            self.gb100.set_channel_percent_value(channel_number, new_percent)

    def get_sccm(self, channel_number):
        if self.gb100 is not None:
            sccm = self.gb100.get_channel_sccm(channel_number)
        else:
            sccm = 0
        return sccm

    def get_sccm_av(self, channel_number):
        if self.gb100 is not None:
            sccm = self.gb100.get_channel_sccm_av(channel_number)
        else:
            sccm = 0
        return sccm

    def get_target_sccm(self, channel_number):
        if self.gb100 is not None:
            sccm = self.gb100.get_channel_target_sccm(channel_number)
        else:
            sccm = 0
        return sccm

    def get_working_status(self):
        working_status = self.gb100.get_working_status()
        return working_status

    def set_working_status(self, turn_on: bool):
        if self.gb100 is not None:
            if turn_on:
                self.gb100.set_working_status_ON()
            else:
                self.gb100.set_working_status_OFF()

    def update_pH(self, CDI_input):
        new_flow = []
        total_flow = self.gas_control.get_mainboard_total_flow()
        if CDI_input[self.pH_index] < physio_ranges['pH_lower']:
            new_flow = total_flow + self.flow_adjust
        elif CDI_input[self.pH_index] > physio_ranges['pH_upper']:
             new_flow = total_flow - self.flow_adjust
        self.gas_control.set_mainboard_total_flow(new_flow)

    def update_CO2(self, CDI_input):  # can only adjust CO2 in HA
        if self.channel_type == "HA":
            new_percentage_mix = []
            percentage_mix = self.gas_control.get_channel_percent_value(self.gas_dict['Carbon Dioxide'])
            if 0 < percentage_mix < 100:
                if CDI_input[self.CO2_index] < self.CO2_lower:
                    new_percentage_mix = percentage_mix + self.co2_adjust
                elif CDI_input[self.CO2_index] > self.CO2_upper:
                    new_percentage_mix = percentage_mix - self.co2_adjust
                self.gas_control.set_channel_percent_value(self.gas_dict['Carbon Dioxide'], new_percentage_mix)
            else:
                self._lgr.debug(f'CO2 % is at {percentage_mix} and cannot be changed automatically')
        else:
            self._lgr.debug(f'Cannot update CO2 in PV - gas mix only contains N2 and O2. Increasing total flow by '
                               f'10 mL/min to blow off more CO2. Adjust total flow for continued changes')
            total_flow = self.gas_control.get_mainboard_total_flow()
            new_flow = total_flow + 10
            self.gas_control.set_mainboard_total_flow(new_flow)

    def update_O2(self, CDI_input):
        new_percentage_mix = []
        percentage_mix = self.gas_control.get_channel_percent_value(self.gas_dict['Oxygen'])
        if 0 < percentage_mix < 100:
            if CDI_input[self.sO2_index] < self.O2_lower:
                new_percentage_mix = percentage_mix + self.o2_adjust
            elif CDI_input[self.sO2_index] > self.O2_upper:
                new_percentage_mix = percentage_mix - self.o2_adjust
            self.gas_control.set_channel_percent_value(self.gas_dict['Oxygen'], new_percentage_mix)
        else:
            self._lgr.debug(f'Oxygen % is at {percentage_mix} and cannot be further changed')

# continue working on error cases
