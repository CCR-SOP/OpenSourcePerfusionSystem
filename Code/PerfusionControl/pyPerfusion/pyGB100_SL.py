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
import pyPerfusion.pyCDI as pyCDI
from pyPerfusion.FileStrategy import MultiVarToFile, MultiVarFromFile
from pyPerfusion.SensorPoint import SensorPoint, ReadOnlySensorPoint

import mcqlib_GB100.mcqlib.main as mcq

# Below I copy-pasted test_multivar_sensor_point to pull in last_samples but should not keep like this long term
# Also test this in person to make sure last_samples is what you want
def main():
    cdi = pyCDI.CDIStreaming('Test CDI')
    cdi.open('COM13', 9600)

    sensorpt = SensorPoint('multi_var', 'na', cdi)
    write_strategy = MultiVarToFile('write', 1, 17)
    write_strategy.open(PerfusionConfig.get_date_folder(), f'{sensorpt.name}_raw', sensorpt.params)
    sensorpt.add_strategy(write_strategy)
    sensorpt.set_ch_id(0)

    ro_sensorpt = ReadOnlySensorPoint('multi_var', 'na', cdi)

    read_strategy = MultiVarFromFile('multi_var', 1, 17, 1)
    read_strategy.open(PerfusionConfig.get_date_folder(), f'{sensorpt.name}_raw', ro_sensorpt.params)
    ro_sensorpt.add_strategy(read_strategy)

    sensorpt.start()
    cdi.start()

    data = list(range(18))
    time.sleep(60.0)
    ts, last_samples = read_strategy.retrieve_buffer(60000, 5)
    print(last_samples)
    print(type(last_samples))
    for ts, samples in zip(ts, last_samples):
        print(f'{ts}: sample is {samples}')

    cdi.stop()
    sensorpt.stop()
    ro_sensorpt.stop()


if __name__ == '__main__':
    PerfusionConfig.set_test_config()
    main()

# start of new GB100 code

# dictionary of acceptable value ranges - double check values against how we set CDI
physio_ranges = {'pH_lower': 7.35, 'pH_upper': 7.45,
                 'arterial_CO2_lower': 20, 'arterial_CO2_upper': 45,
                 'arterial_O2_lower': 100, 'arterial_O2_upper': 450,
                 'venous_CO2_lower': 20, 'venous_CO2_upper': 45,
                 'venous_O2_lower': 100, 'venous_O2_upper': 450}

HA_mixer = mcq.Main('Arterial Gas Mixer')
PV_mixer = mcq.Main('Venous Gas Mixer')  # Main is not configured to do this

# code to turn on both mixers - or do we need this if starting manually?

class GB100_shift:
    def __init__(self, vessel, last_samples, mixer):
        self.vessel = vessel  # vessel = 'HA' or 'PV'
        self.CDI_input = last_samples  # assumes this will be input but not sure this is best design choice
        self.mixer = mixer    # can you put an object in an object like this?

        # determine channels and gases
        id_gases = []
        gas_types = []
        total_channels = self.mixer.get_total_channels()
        for channel in total_channels:
            id_gas = mixer.get_channel_id_gas(channel)
            gas_type = mcq.mcq_utils.get_gas_type(id_gas)
            id_gases += id_gas
            gas_types += gas_type
        self.gas_dict = {gas_types[0]: id_gases[0], gas_types[1]: id_gases[1]}  # CHECK THIS OUTPUT

    def check_pH(self):
        if self.vessel == 'HA':
            if self.CDI_input[0] < physio_ranges['pH_lower']:
                total_flow = self.mixer.get_mainboard_total_flow()
                new_flow = total_flow + 10
                self.mixer.set_mainboard_total_flow(new_flow)
            elif self.CDI_input[0] > physio_ranges['pH_upper']:
                total_flow = self.mixer.get_mainboard_total_flow()
                new_flow = total_flow - 10
                self.mixer.set_mainboard_total_flow(new_flow)
        elif self.vessel == 'PV':
            if self.CDI_input[9] < physio_ranges['pH_lower']:
                total_flow = self.mixer.get_mainboard_total_flow()
                new_flow = total_flow + 10
                self.mixer.set_mainboard_total_flow(new_flow)
            elif self.CDI_input[9] > physio_ranges['pH_upper']:
                total_flow = self.mixer.get_mainboard_total_flow()
                new_flow = total_flow - 10
                self.mixer.set_mainboard_total_flow(new_flow)

    def check_CO2(self):
        if self.vessel == 'HA':
            if self.CDI_input[1] < physio_ranges['arterial_CO2_lower']:
                target_flow = self.mixer.get_channel_target_sccm(self.gas_dict['Carbon Dioxide'])
                new_target_flow = target_flow + 3
                self.mixer.set_channel_percent_value(self.gas_dict['Carbon Dioxide'], new_target_flow)
            elif self.CDI_input[1] > physio_ranges['arterial_CO2_upper']:
                target_flow = self.mixer.get_channel_target_sccm(self.gas_dict['Carbon Dioxide'])
                if target_flow > 0:
                    new_target_flow = target_flow - 3
                    self.mixer.set_channel_percent_value(self.gas_dict['Carbon Dioxide'], new_target_flow)