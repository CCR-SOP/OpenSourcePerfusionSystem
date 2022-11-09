import mcqlib_GB100.mcqlib.main as mcq
import time

mixer = mcq.Main('Arterial Gas Mixer')
total_channels = mixer.get_total_channels()

# mixer.set_working_status_ON()
# mixer.set_working_status_OFF()

mixer.set_mainboard_total_flow(100)
totalFlow = mixer.get_mainboard_total_flow()
print(f'Total flow is {totalFlow}')

for channel in range(total_channels):
    channel_nr = channel + 1

    idGas = mixer.get_channel_id_gas(channel_nr)
    kFactor = mixer.get_channel_k_factor_gas(channel_nr)
    gasType = mcq.mcq_utils.get_gas_type(idGas)
    mixer.set_channel_percent_value(channel_nr, 50)  # set to 50%
    channelPercentage = mixer.get_channel_percent_value(channel_nr)
    targetFlow = mixer.get_channel_target_sccm(channel_nr)
    actualFlow = mixer.get_channel_sccm_av(channel_nr)

    channel_info = "Channel {0} - Gas Id: {1}, Gas: {2}, K-Factor: {3}, Channel Percentage: {4}, Target Flow: {5}, " \
                   "Actual Flow: {6}".format(channel_nr, idGas, gasType, kFactor, channelPercentage, targetFlow,  actualFlow)

    print(channel_info)

    time.sleep(1)