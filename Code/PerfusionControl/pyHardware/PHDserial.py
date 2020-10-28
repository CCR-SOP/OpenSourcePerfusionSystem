from pyHardware.pyUSBSerial import USBSerial

class PHDserial(USBSerial):
    """
    Class for serial communication over USB using PHD (Pump 11 Elite) command set

    ...

    Attributes
    ----------


    Methods
    -------
    open(port_name, baud, addr)
        opens USB port of given name with the specified baud rate using given syringe pump address
    set_param(param, value)
        sets a syringe pump parameter (param) to (value)
    infuse()
        begin infusion of syringe
    withdraw()
        being withdrawal of syringe

    """
    def __init__(self):
        super().__init__()
        self.__addr = 0

    def open(self, port_name, baud, addr):
        super().open(port_name, baud)
        self.__addr = addr
        self.__port.xonxoff = True
        self.send('poll REMOTE')
        self.send(f'address {self.__addr}')
        self.send('ascale 100')

    def set_param(self, param, value):
        self.send(f'{param} {value}')

    def infuse(self):
        self.send('irun')

    def withdraw(self):
        self.withdraw('wrun')

    def set_infusion_rate(self, ml_sec):
        self.set_param('irate', f'{ml_sec} ml/sec')

    def set_syringe_diameter(self, diameter):
        self.set_param('diameter', f'{diameter}')

    def set_syringe_volume(self, volume_ml):
        self.set_param('svolume', f'{volume_ml} ml')

    def set_syringe_manufacturer(self, manu_code):
        self.set_param('syrm', f'{manu_code}')

