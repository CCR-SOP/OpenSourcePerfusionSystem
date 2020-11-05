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
        self._manufacturers = {}
        self._syringes = {}

    def open(self, port_name, baud, addr):
        super().open(port_name, baud)
        self.__addr = addr
        self._USBSerial__serial.xonxoff = True
        self.send('')
        self.send('poll REMOTE\r')
        self.send(f'address {self.__addr}')
        # self.send('ascale 100\r')

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

    def get_syringe_manufacturers(self):
        # turn polling off to get a response
        self.send('poll OFF\r')
        self.send('poll REMOTE\r')
        self.send('poll OFF\r')
        self.send('syrmanu ?\r')
        valid_manu = True
        while valid_manu:
            response = self.get_response(max_bytes=1000)
            if response == '':
                valid_manu = False
            else:
                ends = []
                for i in range(len(response)):
                    if response[i] == ':':
                        ends.append(i)
                response = response[(ends[-2]+2):(ends[-1]-2)].split('\r\n')
                for i in range(len(response)):
                    syringe_info = response[i]
                    syringe_info_separation = syringe_info.split('  ')
                    self._manufacturers[syringe_info_separation[0]] = syringe_info_separation[1]
        # restore polling
        self.send('poll REMOTE\r')

    def get_syringe_types(self):
        # turn polling off to get a response
        self.send('poll OFF\r')
        for code in self._manufacturers.keys():
            self.send(f'syrmanu {code} ?\r')
            valid_type = True
            syringes = []
            while valid_type:
                response = self.get_response(max_bytes=100)
                if response == '':
                    valid_type = False
                else:
                    response = response.replace(':', '')
                    response = response.replace('\n\n\n', '\n')
                    # expected response is ":{volume} {unit}"
                    syringes.append(response)
            self._syringes[code] = syringes

        # restore polling
        self.send('poll REMOTE\r')

    def print_available_syringes(self):
        for code, name in self._manufacturers.items():
            print(f'{name} ({code})')
            syringes = self._syringes[code]
            print(f'{syringes[0]}')
