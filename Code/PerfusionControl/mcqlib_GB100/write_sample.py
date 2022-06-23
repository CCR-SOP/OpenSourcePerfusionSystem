import sys, time
sys.path.append("/mcqlib")
import mcqlib_GB100.mcqlib.main as mcq


print("Start Script")
print("Read Channel 3 gas...")

idGas = mcq.get_channel_id_gas(3)
kFactor = mcq.get_channel_k_factor_gas(3)
gasType = mcq.mcq_utils.get_gas_type(idGas)

channel_info = "Channel {0} - Gas Id: {1}, Gas: {2}, K-Factor: {3}".format(3, idGas, gasType, kFactor)

print(channel_info)

time.sleep(2)


print("Set Argon on Channel 3")

mcq.set_gas_from_xml_file(3, 7)

time.sleep(2)

idGas = mcq.get_channel_id_gas(3)
kFactor = mcq.get_channel_k_factor_gas(3)
gasType = mcq.mcq_utils.get_gas_type(idGas)

channel_info = "Channel {0} - Gas Id: {1}, Gas: {2}, K-Factor: {3}".format(3, idGas, gasType, kFactor)

print(channel_info)

time.sleep(2)

print("End Script")
