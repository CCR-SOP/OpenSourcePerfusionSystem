#!/usr/bin/env python
import socket
#import mcq_utils
import time, random, os, sys
import minimalmodbus

debug_mode = False

def read_holding_register(instrument, starting_address, quantity = 1, number_of_decimals = 0):
  for attempt in range(5):
    try:      
      response = instrument.read_register(starting_address, number_of_decimals)
      return response
    except Exception as e:
      handle_exc(attempt, e)
    else:
      break
  else:
    # we failed all the attempts - deal with the consequences.
    print("failed all the attempts")
    return False


def read_long(instrument, starting_address):
  for attempt in range(5):
    try:      
      response = instrument.read_long(starting_address)
      return response
    except Exception as e:
      handle_exc(attempt, e)
    else:
      break
  else:
    # we failed all the attempts - deal with the consequences.
    print("failed all the attempts")
    return False

# write_long(registeraddress, value, signed=False, byteorder=0)
def write_long(instrument, starting_address, value):
  for attempt in range(5):
    try:      
      response = instrument.write_long(starting_address, value)
      return response
    except Exception as e:
      handle_exc(attempt, e)
    else:
      break
  else:
    # we failed all the attempts - deal with the consequences.
    print("failed all the attempts")
    return False


#write_register(registeraddress, value, number_of_decimals=0, functioncode=16, signed=False)
def write_register(instrument, starting_address, value):
  for attempt in range(5):
    try:      
      response = instrument.write_register(starting_address, value)
      return response
    except Exception as e:
      handle_exc(attempt, e)
    else:
      break
  else:
    # we failed all the attempts - deal with the consequences.
    print("failed all the attempts")
    return False


#write_registers(registeraddress, values)
def write_registers(instrument, starting_address, values):
  for attempt in range(5):
    try:      
      response = instrument.write_registers(starting_address, values)
      return response
    except Exception as e:
      handle_exc(attempt, e)
    else:
      break
  else:
    # we failed all the attempts - deal with the consequences.
    print("failed all the attempts")
    return False

def handle_exc(attempt, exception):
  if debug_mode:
    print("Error reading value... retrying", attempt+1, "of 5.", exception)
  # attendi...
  time.sleep(0.5)