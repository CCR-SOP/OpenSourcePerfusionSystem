"""Test program to control GB_100 Gas Mixer (configured for HA)
Tests classes provided by mcq

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""

import mcqlib_GB100.mcqlib.main as mcq
import time

mixer = mcq.Main('Arterial Gas Mixer')
total_channels = mixer.get_total_channels()

# mixer.set_working_status_ON()
# mixer.set_working_status_OFF()

mixer.set_mainboard_total_flow(100)
totalFlow = mixer.get_mainboard_total_flow()
print(f'Total flow is {totalFlow}')

# update for gas mix calibration experiment
mixer.set_channel_percent_value(1, 49)
mixer.set_channel_percent_value(2, 51)

for channel in range(total_channels):
    channel_nr = channel + 1

    idGas = mixer.get_channel_id_gas(channel_nr)
    kFactor = mixer.get_channel_k_factor_gas(channel_nr)
    gasType = mcq.mcq_utils.get_gas_type(idGas)
    targetFlow = mixer.get_channel_target_sccm(channel_nr)
    actualFlow = mixer.get_channel_sccm_av(channel_nr)

    channel_info = "Channel {0} - Gas Id: {1}, Gas: {2}, K-Factor: {3}, Target Flow: {4}, " \
                   "Actual Flow: {5}".format(channel_nr, idGas, gasType, kFactor, targetFlow,  actualFlow)

    print(channel_info)

    time.sleep(1)