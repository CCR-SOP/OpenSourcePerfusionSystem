import mcqlib_GB100.mcqlib.main as mcq
import time

mixer = mcq.Main('Arterial Gas Mixer')
total_channels = mixer.get_total_channels()

totalFlow = mixer.get_mainboard_total_flow()
print(f'Total flow is {totalFlow}')

for channel in range(total_channels):
    channel_nr = channel + 1

    idGas = mixer.get_channel_id_gas(channel_nr)
    kFactor = mixer.get_channel_k_factor_gas(channel_nr)
    gasType = mcq.mcq_utils.get_gas_type(idGas)
    channelPercentage = mixer.get_channel_percent_value(channel_nr)

    channel_info = "Channel {0} - Gas Id: {1}, Gas: {2}, K-Factor: {3}, Channel Percentage {4}".format(channel_nr, idGas, gasType, kFactor, channelPercentage)

    print(channel_info)

    time.sleep(1)