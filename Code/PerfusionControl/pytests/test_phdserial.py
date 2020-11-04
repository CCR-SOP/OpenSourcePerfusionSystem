from pyHardware.PHDserial import PHDserial

port_name = 'COM6'
baud = 9600

syringe = PHDserial()
syringe.open(port_name=port_name, baud=baud, addr=0)

syringe.get_syringe_manufacturers()
syringe.get_syringe_types()

syringe.print_available_syringes()