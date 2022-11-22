##
# @file 
# Modbus wrapper with read/write functions for Gas Blender 3000+ instruments
# 
import minimalmodbus, configparser
from . import utils as mcq_utils
from . import modbus_helper as mb
from serial import PARITY_NONE
import pyPerfusion.PerfusionConfig as PerfusionConfig

# config = configparser.ConfigParser()
# config.read('./mcqlib_GB100/mcqlib/config.ini')
# Serial Port configuration, taken from file config.ini
# serial_port = str(config['DEFAULT']['SerialPort'])
# serial_baud = int(config['DEFAULT']['SerialBaudrate'])
# serial_timeout = int(config['DEFAULT']['SerialTimeout'])

class Main:
  def __init__(self, name):
      self.name = name

      section = PerfusionConfig.read_section('hardware', self.name)
      com = str(section['commport'])
      baud = int(section['baudrate'])
      timeout = int(section['timeout'])

      self.instrument = minimalmodbus.Instrument(com, 1, minimalmodbus.MODE_RTU, debug=False)
      self.instrument.serial.baudrate = baud
      self.instrument.serial.bytesize = 8
      self.instrument.serial.parity   = PARITY_NONE
      self.instrument.serial.stopbits = 1
      self.instrument.serial.timeout  = timeout  # seconds

  def get_mainboard_fw_ver(self):
    address = 0
    response = mb.read_holding_register(self.instrument, address)
    h = str(hex(response))
    h = h.replace("0x", "")
    ver = h.rjust(4, "0")
    return ver

  ## Get Mainboard hardware version
  #
  # eg. 0102
  def get_mainboard_hw_ver(self):
    address = 1
    response = mb.read_holding_register(self.instrument, address)
    h = str(hex(response))
    h = h.replace("0x", "")
    ver = h.rjust(4, "0")
    return ver

  ## Get Mainboard status
  #
  #  @return an array with possible values:
  #  - System ready
  #  - System connected with PC
  #  - Control ON - Gas flowing
  #  - At least a gas channel present
  def get_mainboard_status(self):
    address = 2
    response = mb.read_holding_register(self.instrument, address)
    arr = mcq_utils.mb_status(response)
    return arr

  ## Get Mainboard alerts
  #
  #  @return an array with possible values:
  #  - Generic error
  #  - Wrong Parameter
  #  - Serial Number error
  #  - Warranty error
  def get_mainboard_alert(self):
    address = 3
    response = mb.read_holding_register(self.instrument, address)
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
  def get_total_channels(self):
    address = 5
    response = mb.read_holding_register(self.instrument, address)
    value = response
    return value

  ## Get the balance channel
  #
  #  @return number of the current balance channel
  def get_channel_balance(self):
    address = 6
    response = mb.read_holding_register(self.instrument, address)
    value = response
    return value

  ## Get mainboard total flow
  #
  #  @return SCCM
  def get_mainboard_total_flow(self):
    address = 7
    response = mb.read_long(self.instrument, address)
    value = response
    return value

  ## Get instrument working status
  #
  #  @return a number with current status of instrument:
  #  - 0 (Status ON)
  #  - 1 (Status OFF)
  def get_working_status(self):
    address = 9
    response = mb.read_holding_register(self.instrument, address)
    value = response
    return value

  # MODULES FUNCTIONS - READ

  def __get_channel_base_address(self, channel_nr):
    return ((channel_nr - 1) * 15) + 10

  ## Get channel firmware version
  #
  def get_channel_fw_ver(self, channel_nr):
    offset = 0
    address = self.__get_channel_base_address(channel_nr) + offset
    response = mb.read_holding_register(self.instrument, address)
    return response

  ## Get channel hardware version
  #
  def get_channel_hw_ver(self, channel_nr):
    offset = 1
    address = self.__get_channel_base_address(channel_nr) + offset
    response = mb.read_holding_register(self.instrument, address)
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
  def get_channel_alert(self, channel_nr):
    offset = 2
    address = self.__get_channel_base_address(channel_nr) + offset
    response = mb.read_holding_register(self.instrument, address)
    arr = mcq_utils.channel_alert(response)
    return arr

  ## Get id gas - calibration
  #  @param channel_nr Channel number (1,2,3...)
  #
  #  @return ID of gas used for calibration on specific channel
  def get_channel_id_gas_calibration(self, channel_nr):
    offset = 3
    address = self.__get_channel_base_address(channel_nr) + offset
    response = mb.read_holding_register(self.instrument, address)
    return response

  ## Get K-Factor - calibration
  #  @param channel_nr Channel number (1,2,3...)
  #
  #  @return K-Factor of gas on specific channel
  def get_channel_k_factor_calibration(self, channel_nr):
    offset = 4
    address = self.__get_channel_base_address(channel_nr) + offset
    response = mb.read_holding_register(self.instrument, address)
    value = response / 1000
    return value

  ## Get if the specified channel is enabled or disabled
  #  @param channel_nr Channel number (1,2,3...)
  #
  #  @return Possible values:
  #  - 0 (Channel disabled)
  #  - 1 (Channel enabled)
  def get_channel_enabled(self, channel_nr):
    offset = 5
    address = self.__get_channel_base_address(channel_nr) + offset
    response = mb.read_holding_register(self.instrument, address)
    return response

  ## Get percentage value set on channel
  #  @param channel_nr Channel number (1,2,3...)
  #
  #  @return % value (eg. 85)
  def get_channel_percent_value(self, channel_nr):
    offset = 6
    address = self.__get_channel_base_address(channel_nr) + offset
    response = mb.read_holding_register(self.instrument, address)
    value = response / 100
    return value

  ## Get ID of gas selected on the channel
  #  @param channel_nr Channel number (1,2,3...)
  #
  #  @return ID of gas (eg . 11)
  def get_channel_id_gas(self, channel_nr):
    offset = 7
    address = self.__get_channel_base_address(channel_nr) + offset
    response = mb.read_holding_register(self.instrument, address)
    return response

  ## Get K-Factor value on selected channel
  #  @param channel_nr Channel number (1,2,3...)
  #
  #  @return K-Factor value (eg. 0.872)
  def get_channel_k_factor_gas(self, channel_nr):
    offset = 8
    address = self.__get_channel_base_address(channel_nr) + offset
    response = mb.read_holding_register(self.instrument, address)
    value = response / 1000
    return value

  ## Get SCCM for selected channel
  #  @param channel_nr Channel number (1,2,3...)
  #
  #  @return SCCM value
  def get_channel_sccm(self, channel_nr):
    offset = 9
    address = self.__get_channel_base_address(channel_nr) + offset
    response = mb.read_long(self.instrument, address)
    # valore registrato con 2 decimali
    value = response / 100
    return value

  ## Get target SCCM for selected channel
  #  @param channel_nr Channel number (1,2,3...)
  #
  #  @return SCCM target value
  def get_channel_target_sccm(self, channel_nr):
    offset = 11
    address = self.__get_channel_base_address(channel_nr) + offset
    response = mb.read_long(self.instrument, address)
    # valore registrato con 2 decimali
    value = response / 100
    return value

  ## Get SCCM_AV for selected channel
  #  @param channel_nr Channel number (1,2,3...)
  #
  #  @return SCCM value
  def get_channel_sccm_av(self, channel_nr):
    offset = 13
    address = self.__get_channel_base_address(channel_nr) + offset
    response = mb.read_long(self.instrument, address)
    # valore registrato con 2 decimali
    value = response / 100
    return value

  # WRITE: HOLDING REGISTERS (10H) #

  # MAINBOARD

  ## Set mainboard balance channel
  #  @param channel_nr Channel number (1,2,3...)
  def set_balance_channel(self, channel_nr):
    address = 6
    response = mb.write_register(self.instrument, address, channel_nr)
    return response

  ## Set mainboard total flow
  #  @param total flow (SCCM) of instrument
  def set_mainboard_total_flow(self, sccm):
    address = 7
    words = 2
    response = mb.write_long(self.instrument, address, sccm)
    return response

  # def set_mainboard_working_status(value):
  #   address = 9
  #   response = mb.write_register(instrument, address, value)
  #   return response

  ## Set mainboard working status as ON
  def set_working_status_ON(self):
    address = 9
    response = mb.write_register(self.instrument, address, 1)  # parametro 1
    return response

  ## Set mainboard working status as OFF
  def set_working_status_OFF(self):
    address = 9
    response = mb.write_register(self.instrument, address, 0)  # parametro 0
    return response

  # MODULES

  ## Enable/disable selected channel
  #  @param channel_nr Channel number (1,2,3...)
  #  @param status Value 0 (disabled) or 1 (enabled)
  def set_channel_enabled(self, channel_nr, status):
    offset = 5
    address = self.__get_channel_base_address(channel_nr) + offset
    # value 0 / 1
    response = mb.write_register(self.instrument, address, status)
    return response

  ## Set percentage (%) flow on selected channel
  #  @param channel_nr Channel number (1,2,3...)
  #  @param percent Percent (%) value
  def set_channel_percent_value(self, channel_nr, percent):
    offset = 6
    address = self.__get_channel_base_address(channel_nr) + offset
    percent = percent * 100
    response = mb.write_register(self.instrument, address, percent)
    return response

  ## Set Gas ID on selected channel.
  #  **Warning! This command doesn't modify the K-Factor!!**
  #  @param channel_nr Channel number (1,2,3...)
  #  @param id Gas ID (number)
  def set_channel_id_gas_only(self, channel_nr, id):
    # cambia SOLO id gas(senza kfactor)
    offset = 7
    address = self.__get_channel_base_address(channel_nr) + offset
    response = mb.write_register(self.instrument, address, id)
    return response

  ## Set K-Factor on selected channel.
  #  @param channel_nr Channel number (1,2,3...)
  #  @param kfactor K-Factor number (eg. 0.606)
  def set_channel_k_factor_only(self, channel_nr, kfactor):
    # cambia SOLO kfactor  # es. 0.606
    offset = 8
    address = self.__get_channel_base_address(channel_nr) + offset
    # va moltiplicato per 1000
    kfactor = kfactor * 1000
    response = mb.write_register(self.instrument, address, kfactor)
    return response

  ## Set Gas ID and K-Factor as defined in file Data.xml
  #  @param channel_nr Channel number (1,2,3...)
  #  @param gas_id Gas ID as registered in file Data.xml (eg. 11)
  def set_gas_from_xml_file(self, channel_nr, gas_id):
    # cambia gas e kfactor, leggendolo dal file xml
    offset = 7
    address = self.__get_channel_base_address(channel_nr) + offset

    gas_dict = mcq_utils.get_gas_xml()

    gas_id = int(gas_id)
    gas_kfactor = int(gas_dict[gas_id] * 1000)
    values = [gas_id, gas_kfactor]

    response = mb.write_registers(self.instrument, address, values)
    return response

  ## Set custom Gas ID and K-factor as defined in file CustomData.xml
  #  @param channel_nr Channel number (1,2,3...)
  #  @param gas_id Gas ID as defined in file CustomData.xml (eg. 100)
  def set_gas_custom_from_xml_file(self, channel_nr, gas_id):
    # cambia gas e kfactor, leggendolo dal file CustomData.xml
    offset = 7
    address = self.__get_channel_base_address(channel_nr) + offset

    gas_dict = mcq_utils.get_custom_gas_xml()

    gas_id = int(gas_id)
    gas_kfactor = int(gas_dict[gas_id] * 1000)
    values = [gas_id, gas_kfactor]

    response = mb.write_registers(self.instrument, address, values)
    return response

  def setup_work(self, ch_balance, total_flow, perc_value=[]):  # Sets balance channel, total flow, and percent values for each channel
    total_channels = self.get_total_channels()
    # reset ch balance == 100
    self.set_balance_channel(ch_balance)
    self.set_channel_percent_value(ch_balance, 100.0)
    # set perc_value
    for i in range(len(perc_value)):
      if i + 1 != ch_balance and i < total_channels:
        self.set_channel_percent_value(i + 1, perc_value[i])
    # set flow
    self.set_mainboard_total_flow(total_flow)

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

# READ : HOLDING REGISTERS (03H)
      # MAINBOARD FUNCTIONS - READ

      ## Get Mainboard firmware version
      #
      # eg. 0109
