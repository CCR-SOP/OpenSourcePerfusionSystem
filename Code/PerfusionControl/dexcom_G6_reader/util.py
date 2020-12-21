if __package__ in {None, ''}:
    import constants
else:
    import constants
import datetime
import platform
import sys
import serial.tools.list_ports

def Ord(byte):
  if isinstance(byte, int):
    return byte
  elif isinstance(byte, str):
    return ord(byte)
  elif isinstance(byte, bytes):
    return int(byte[0])
  else:
    raise TypeError("unexpected class when changing to bytes: {class_name}".format(
        class_name=str(byte.__class__)
      )
    )

def python3():
  return sys.version_info[0] == 3

def to_bytes(iterable):
  return bytes(map(Ord, iterable))

def ReceiverTimeToTime(rtime):
  return constants.BASE_TIME + datetime.timedelta(seconds=rtime)

def windows_find_usbserial(vendor, product):
  ports = list(serial.tools.list_ports.comports())
  for p in ports:
    try:
      vid_pid_keyval = p.hwid.split()[1]
      vid_pid_val = vid_pid_keyval.split('=')[1]
      vid, pid = vid_pid_val.split(':')

      if vid.lower() != vendor.lower():
        continue
      if pid.lower() != product.lower():
        continue

      return p.device
    except (IndexError, ValueError) as e:
      continue

def find_usbserial(vendor, product):
  """Find the tty device for a given usbserial devices identifiers.

  Args:
     vendor: (int) something like 0x0000
     product: (int) something like 0x0000

  Returns:
     String, like /dev/ttyACM0 or /dev/tty.usb...
  """
  if platform.system() == 'Windows':
    vendor, product = [('%04x' % x).strip() for x in (vendor, product)]
    return windows_find_usbserial(vendor, product)
  else:
    raise NotImplementedError('Cannot find serial ports on %s'
                              % platform.system())

if __name__ == '__main__':
    vendor = constants.DEXCOM_USB_VENDOR
    product = constants.DEXCOM_USB_PRODUCT
    if len(sys.argv) > 1:
        vendor = int(sys.argv[1], 16)
    if len(sys.argv) > 2:
        product = int(sys.argv[2], 16)
    print(find_usbserial(vendor, product))
