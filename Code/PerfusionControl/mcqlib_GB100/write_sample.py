import sys
import time
import mcqlib_GB100.mcqlib.main as mcq

sys.path.append("/mcqlib_GB100/mcqlib")


print("Start Script")
print("Read Channel 2 gas...")

idGas = mcq.get_channel_id_gas(2)
kFactor = mcq.get_channel_k_factor_gas(2)
gasType = mcq.mcq_utils.get_gas_type(idGas)

channel_info = "Channel {0} - Gas Id: {1}, Gas: {2}, K-Factor: {3}".format(2, idGas, gasType, kFactor)

print(channel_info)

time.sleep(2)


print("Set Argon on Channel 2")

mcq.set_gas_from_xml_file(2, 7)

time.sleep(2)

idGas = mcq.get_channel_id_gas(2)
kFactor = mcq.get_channel_k_factor_gas(2)
gasType = mcq.mcq_utils.get_gas_type(idGas)

channel_info = "Channel {0} - Gas Id: {1}, Gas: {2}, K-Factor: {3}".format(2, idGas, gasType, kFactor)

print(channel_info)

time.sleep(2)

print("End Script")
