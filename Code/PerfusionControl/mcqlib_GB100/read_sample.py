import sys, time

# use mcqlib package folder
sys.path.append("/mcqlib")

import mcqlib_GB100+.mcqlib.main as mcq

print("Script Start")

print("fw ver", mcq.get_mainboard_fw_ver())
print("hw ver", mcq.get_mainboard_hw_ver())

print("Reading Channels Values...")
time.sleep(2)

total_channels = mcq.get_total_channels()

for channel in range(total_channels):
  channel_nr = channel + 1

  idGas = mcq.get_channel_id_gas(channel_nr)
  kFactor = mcq.get_channel_k_factor_gas(channel_nr)
  gasType = mcq.mcq_utils.get_gas_type(idGas)

  channel_info = "Channel {0} - Gas Id: {1}, Gas: {2}, K-Factor: {3}".format(channel_nr, idGas, gasType, kFactor)
  
  print(channel_info)
  
  time.sleep(1)

print("Script End")