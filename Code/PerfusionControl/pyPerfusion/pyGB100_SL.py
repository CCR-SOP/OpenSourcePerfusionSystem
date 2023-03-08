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
physio_ranges = {'pH_lower': 7.4, 'pH_upper': 7.6,  # values shifted up by 0.1 based on experimental tests
                 'arterial_CO2_lower': 20, 'arterial_CO2_upper': 60,
                 'arterial_O2_lower_so2': 90, 'arterial_O2_upper_so2': 100,
                 'venous_CO2_lower': 20, 'venous_CO2_upper': 80,
                 'venous_O2_lower_so2': 60, 'venous_O2_upper_so2': 92}


class GasControl:
    def __init__(self):
        # self._lgr = logging.getLogger(__name__)
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
            self.CO2_lower = physio_ranges['arterial_CO2_lower']
            self.CO2_upper = physio_ranges['arterial_CO2_upper']
            self.O2_lower = physio_ranges['arterial_O2_lower_so2']
            self.O2_upper = physio_ranges['arterial_O2_upper_so2']
        elif self.channel_type == "PV":
            try:
                self.gb100 = mcq.Main('Venous Gas Mixer')
            except serial.serialutil.SerialException:
                self.gb100 = None
            self.CO2_lower = physio_ranges['venous_CO2_lower']
            self.CO2_upper = physio_ranges['venous_CO2_upper']
            self.O2_lower = physio_ranges['venous_O2_lower_so2']
            self.O2_upper = physio_ranges['venous_O2_upper_so2']
        else:
            self.gb100 = None
            self.CO2_lower = None
            self.CO2_upper = None
            self.O2_lower = None
            self.O2_upper = None

        self.co2_adjust = 1
        self.o2_adjust = 1
        self.flow_adjust = 2  # mL/min

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
        total_flow = self.get_total_flow()
        if 5 < total_flow < 250:
            if CDI_input.venous_pH == -1:
                self._lgr.warning(f'Venous pH is out of range. Cannot be adjusted automatically')
                return None
            elif CDI_input.venous_pH < physio_ranges['pH_lower']:
                new_flow = total_flow + self.flow_adjust
                self.set_total_flow(new_flow)
                self._lgr.info(f'Total flow in PV increased to {new_flow}')
                return new_flow
            elif CDI_input.venous_pH > physio_ranges['pH_upper']:
                new_flow = total_flow - self.flow_adjust
                self.set_total_flow(new_flow)
                self._lgr.info(f'Total flow in PV decreased to {new_flow}')
                return new_flow
        elif total_flow >= 250:
            self._lgr.warning(f'Total flow in PV at or above 250 mL/min. Cannot be run automatically')
            return None
        elif total_flow <= 5:
            self._lgr.warning(f'Total flow in portal vein at or below 5 mL/min. Cannot be run automatically')
            return None
        else:
            return None

    def update_CO2(self, CDI_input):
        new_percentage_mix = None
        percentage_mix = self.get_percent_value(2)  # TODO: make this find CO2 no matter which channel it is
        if 0 < percentage_mix < 100:
            if CDI_input.arterial_pH == -1:
                self._lgr.warning(f'Arterial pH is out of range. Cannot be adjusted automatically')
            elif CDI_input.arterial_CO2 == -1:
                self._lgr.warning(f'Arterial CO2 is out of range. Cannot be adjusted automatically')
            elif CDI_input.arterial_pH > physio_ranges['pH_upper'] or CDI_input.arterial_CO2 < self.CO2_lower:
                new_percentage_mix = percentage_mix + self.co2_adjust
                self._lgr.warning(f'CO2 low, blood alkalotic')
            elif CDI_input.arterial_pH < physio_ranges['pH_lower'] or CDI_input.arterial_CO2 > self.CO2_upper:
                new_percentage_mix = percentage_mix - self.co2_adjust
                self._lgr.warning(f'CO2 high, blood acidotic')

            if new_percentage_mix is not None:
                self.set_percent_value(2, new_percentage_mix)
                self._lgr.info(f'Arterial CO2 updated to {new_percentage_mix}%')
        else:
            self._lgr.debug(f'CO2 % is out of range and cannot be changed automatically')

        return new_percentage_mix

    def update_O2(self, CDI_input):
        new_percentage_mix = None
        percentage_mix = self.get_percent_value(1)  # TODO: make this find O2 no matter which channel it is
        if 0 < percentage_mix < 100:
            if CDI_input.venous_O2 == -1:
                self._lgr.warning(f'Venous O2 is out of range. Cannot be adjusted automatically')
            elif CDI_input.venous_O2 < self.O2_lower:
                new_percentage_mix = percentage_mix + self.o2_adjust
                self._lgr.warning(f'Venous O2 is low')
            elif CDI_input.venous_O2 > self.O2_upper:
                new_percentage_mix = percentage_mix - self.o2_adjust
                self._lgr.warning(f'Venous O2 is high')

            if new_percentage_mix is not None:
                self.set_percent_value(2, 100-new_percentage_mix)
                self._lgr.info(f'Venous O2 updated to {new_percentage_mix}%')
        else:
            self._lgr.debug(f'O2 % is out of range and cannot be changed automatically')

        return new_percentage_mix
