##
# @file 
# Modbus wrapper with read/write functions for Gas Blender 3000+ instruments
# 
import minimalmodbus
import configparser
from . import utils as mcq_utils
from . import modbus_helper as mb
from serial import PARITY_NONE

config = configparser.ConfigParser()
config.read('./mcqlib/config.ini')
# Serial Port configuration, taken from file config.ini
serial_port = str(config['DEFAULT']['SerialPort'])
serial_baud = int(config['DEFAULT']['SerialBaudrate'])
serial_timeout = int(config['DEFAULT']['SerialTimeout'])

instrument = minimalmodbus.Instrument(serial_port, 1, minimalmodbus.MODE_RTU, debug=False)
instrument.serial.baudrate = serial_baud
instrument.serial.bytesize = 8
instrument.serial.parity   = PARITY_NONE
instrument.serial.stopbits = 1
instrument.serial.timeout  = serial_timeout  # seconds


# READ : HOLDING REGISTERS (03H)
# MAINBOARD FUNCTIONS - READ

## Get Mainboard firmware version
#
# eg. 0109
def get_mainboard_fw_ver():
  address = 0  
  response = mb.read_holding_register(instrument, address)
  h = str(hex(response))
  h = h.replace("0x","")
  ver = h.rjust(4,"0")  
  return ver

## Get Mainboard hardware version
#
# eg. 0102
def get_mainboard_hw_ver():
  address = 1
  response = mb.read_holding_register(instrument, address)
  h = str(hex(response))
  h = h.replace("0x","")
  ver = h.rjust(4,"0")  
  return ver

## Get Mainboard status
#
#  @return an array with possible values:
#  - System ready
#  - System connected with PC
#  - Control ON - Gas flowing
#  - At least a gas channel present
def get_mainboard_status():
  address = 2
  response = mb.read_holding_register(instrument, address)
  arr = mcq_utils.mb_status(response)
  return arr

## Get Mainboard alerts
#
#  @return an array with possible values:
#  - Generic error
#  - Wrong Parameter
#  - Serial Number error
#  - Warranty error
def get_mainboard_alert():
  address = 3
  response = mb.read_holding_register(instrument, address)
  arr = mcq_utils.mb_alert(response)
  return arr

# #TODO fix
# def get_mainboard_temperature():
#   address = 4
#   response = mb.read_holding_register(instrument, address)
#   temp = response
#   return temp

## Get the number of channels available on the instrument
#
# @return number of channels (eg. 3)
def get_total_channels():
  address = 5
  response = mb.read_holding_register(instrument, address)
  value = response
  return value

## Get the balance channel
#
#  @return number of the current balance channel
def get_channel_balance():
  address = 6
  response = mb.read_holding_register(instrument, address)
  value = response
  return value

## Get mainboard total flow
#
#  @return SCCM
def get_mainboard_total_flow():
  address = 7
  response = mb.read_long(instrument, address)
  value = response
  return value

## Get instrument working status
#
#  @return a number with current status of instrument:
#  - 0 (Status ON)
#  - 1 (Status OFF)
def get_working_status():
  address = 9
  response = mb.read_holding_register(instrument, address)
  value = response
  return value


# MODULES FUNCTIONS - READ

def __get_channel_base_address(channel_nr):
	return ((channel_nr - 1) * 15) + 10


## Get channel firmware version
#
def get_channel_fw_ver(channel_nr):
  offset = 0
  address = __get_channel_base_address(channel_nr) + offset
  response = mb.read_holding_register(instrument, address)    
  return response

## Get channel hardware version
#
def get_channel_hw_ver(channel_nr):
  offset = 1
  address = __get_channel_base_address(channel_nr) + offset
  response = mb.read_holding_register(instrument, address)    
  return response


## Get channel alerts
#  @param channel_nr Channel number (1,2,3...)
#
#  @return Array with possible values:
#  - Generic error
#  - Calibration error
#  - Wrong address
#  - Sensor error
#  - Link error with this module
def get_channel_alert(channel_nr):
  offset = 2
  address = __get_channel_base_address(channel_nr) + offset
  response = mb.read_holding_register(instrument, address)
  arr = mcq_utils.channel_alert(response)
  return arr

## Get id gas - calibration
#  @param channel_nr Channel number (1,2,3...)
#
#  @return ID of gas used for calibration on specific channel
def get_channel_id_gas_calibration(channel_nr):
  offset = 3
  address = __get_channel_base_address(channel_nr) + offset
  response = mb.read_holding_register(instrument, address)    
  return response

## Get K-Factor - calibration
#  @param channel_nr Channel number (1,2,3...)
#
#  @return K-Factor of gas on specific channel
def get_channel_k_factor_calibration(channel_nr):
  offset = 4
  address = __get_channel_base_address(channel_nr) + offset
  response = mb.read_holding_register(instrument, address)
  value = response / 1000
  return value

## Get if the specified channel is enabled or disabled
#  @param channel_nr Channel number (1,2,3...)
#
#  @return Possible values:
#  - 0 (Channel disabled)
#  - 1 (Channel enabled)
def get_channel_enabled(channel_nr):
  offset = 5
  address = __get_channel_base_address(channel_nr) + offset
  response = mb.read_holding_register(instrument, address)    
  return response

## Get percentage value set on channel
#  @param channel_nr Channel number (1,2,3...)
#
#  @return % value (eg. 85)
def get_channel_percent_value(channel_nr):
  offset = 6
  address = __get_channel_base_address(channel_nr) + offset
  response = mb.read_holding_register(instrument, address)    
  value = response / 100
  return value

## Get ID of gas selected on the channel
#  @param channel_nr Channel number (1,2,3...)
#
#  @return ID of gas (eg . 11)
def get_channel_id_gas(channel_nr):
  offset = 7
  address = __get_channel_base_address(channel_nr) + offset
  response = mb.read_holding_register(instrument, address)    
  return response

## Get K-Factor value on selected channel
#  @param channel_nr Channel number (1,2,3...)
#
#  @return K-Factor value (eg. 0.872)
def get_channel_k_factor_gas(channel_nr):
  offset = 8
  address = __get_channel_base_address(channel_nr) + offset
  response = mb.read_holding_register(instrument, address)    
  value = response / 1000
  return value

## Get SCCM for selected channel
#  @param channel_nr Channel number (1,2,3...)
#
#  @return SCCM value
def get_channel_sccm(channel_nr):
  offset = 9
  address = __get_channel_base_address(channel_nr) + offset
  response = mb.read_long(instrument, address)
  #valore registrato con 2 decimali
  value = response / 100
  return value

## Get target SCCM for selected channel
#  @param channel_nr Channel number (1,2,3...)
#
#  @return SCCM target value
def get_channel_target_sccm(channel_nr):
  offset = 11
  address = __get_channel_base_address(channel_nr) + offset
  response = mb.read_long(instrument, address)
  #valore registrato con 2 decimali
  value = response / 100
  return value



# WRITE: HOLDING REGISTERS (10H) #

# MAINBOARD

## Set mainboard balance channel
#  @param channel_nr Channel number (1,2,3...)
def set_balance_channel(channel_nr):
  address = 6  
  response = mb.write_register(instrument, address, channel_nr)
  return response

## Set mainboard total flow
#  @param total flow (SCCM) of instrument
def set_mainboard_total_flow(sccm):
  address = 7
  words = 2
  response = mb.write_long(instrument, address, sccm)
  return response


# def set_mainboard_working_status(value):
#   address = 9
#   response = mb.write_register(instrument, address, value)
#   return response

## Set mainboard working status as ON
def set_working_status_ON():
  address = 9
  response = mb.write_register(instrument, address, 1) #parametro 1
  return response

## Set mainboard working status as OFF
def set_working_status_OFF():
  address = 9
  response = mb.write_register(instrument, address, 0) #parametro 0
  return response


#MODULES

## Enable/disable selected channel
#  @param channel_nr Channel number (1,2,3...)
#  @param status Value 0 (disabled) or 1 (enabled)
def set_channel_enabled(channel_nr, status):  
  offset = 5
  address = __get_channel_base_address(channel_nr) + offset
  # value 0 / 1
  response = mb.write_register(instrument, address, status)
  return response

## Set percentage (%) flow on selected channel
#  @param channel_nr Channel number (1,2,3...)
#  @param percent Percent (%) value
def set_channel_percent_value(channel_nr, percent):
  offset = 6
  address = __get_channel_base_address(channel_nr) + offset
  percent = percent * 100
  response = mb.write_register(instrument, address, percent)
  return response



## Set Gas ID on selected channel. 
#  **Warning! This command doesn't modify the K-Factor!!**
#  @param channel_nr Channel number (1,2,3...)
#  @param id Gas ID (number)
def set_channel_id_gas_only(channel_nr, id):
  # cambia SOLO id gas(senza kfactor)
  offset = 7
  address = __get_channel_base_address(channel_nr) + offset
  response = mb.write_register(instrument, address, id)
  return response


## Set K-Factor on selected channel. 
#  @param channel_nr Channel number (1,2,3...)
#  @param kfactor K-Factor number (eg. 0.606)
def set_channel_k_factor_only(channel_nr, kfactor):
  # cambia SOLO kfactor  # es. 0.606
  offset = 8
  address = __get_channel_base_address(channel_nr) + offset
  # va moltiplicato per 1000
  kfactor = kfactor * 1000 
  response = mb.write_register(instrument, address, kfactor)
  return response

## Set Gas ID and K-Factor as defined in file Data.xml
#  @param channel_nr Channel number (1,2,3...)
#  @param gas_id Gas ID as registered in file Data.xml (eg. 11)
def set_gas_from_xml_file(channel_nr, gas_id):
  # cambia gas e kfactor, leggendolo dal file xml
  offset = 7
  address = __get_channel_base_address(channel_nr) + offset

  gas_dict = mcq_utils.get_gas_xml()

  gas_id = int(gas_id)
  gas_kfactor = int(gas_dict[gas_id] * 1000)
  values = [gas_id, gas_kfactor]

  response = mb.write_registers(instrument, address, values)
  return response


## Set custom Gas ID and K-factor as defined in file CustomData.xml
#  @param channel_nr Channel number (1,2,3...)
#  @param gas_id Gas ID as defined in file CustomData.xml (eg. 100)
def set_gas_custom_from_xml_file(channel_nr, gas_id):
  # cambia gas e kfactor, leggendolo dal file CustomData.xml
  offset = 7
  address = __get_channel_base_address(channel_nr) + offset

  gas_dict = mcq_utils.get_custom_gas_xml()

  gas_id = int(gas_id)
  gas_kfactor = int(gas_dict[gas_id] * 1000)
  values = [gas_id, gas_kfactor]

  response = mb.write_registers(instrument, address, values)
  return response


# # todo ?
# def set_custom_gas(channel_nr, gas_id, kfactor):
#   # cambia gas e kfactor, leggendolo dal file Data.xml
#   offset = 7
#   address = __get_channel_base_address(channel_nr) + offset  

#   gas_id = int(gas_id)
#   gas_kfactor = int(kfactor * 1000)
#   values = [gas_id, gas_kfactor]

#   response = mb.write_registers(instrument, address, values)
#   return response