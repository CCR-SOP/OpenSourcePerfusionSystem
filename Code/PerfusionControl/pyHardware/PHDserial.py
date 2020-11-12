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
    infuse()
        begin infusion of syringe
    stop()
        stop infusion of syringe
    set_param(param, value)
        sets a syringe pump parameter (param) to (value)
    """
    def __init__(self):
        super().__init__()
        self.__addr = 0
        self._manufacturers = {}
        self._syringes = {}
        self._response = ''

    def open(self, port_name, baud, addr):
        super().open(port_name, baud)
        self.__addr = addr
        self._USBSerial__serial.xonxoff = True
        self.send('')
        self.send(f'address {self.__addr}\r')
        self.send('poll REMOTE\r')

    def send(self, str2send):
        super().send(str2send)
        self._response = self.get_response(max_bytes=1000)

    def infuse(self):
        self.send('irun\r')

    def stop(self):
        self.send('stop\r')

    def set_param(self, param, value):
        self.send(f'{param} {value}')

    def set_syringe_manufacturer_size_rate(self, manu_code, syringe_size, ml_min):
        self.set_param('syrm', '%s %d ml\r' % (manu_code, syringe_size))
        print('New Syringe Information:')
        self.get_syringe_info()
        self.set_param('irate', f'{ml_min} ml/min\r')
        print('Infusion rate set to :')
        self.get_infusion_rate()

    def set_infusion_rate(self, ml_min):  # can be changed mid-run
        self.set_param('irate', f'{ml_min} ml/min\r')
        print('Infusion rate set to :')
        self.get_infusion_rate()

    def reset_infusion_volume(self):
        self.send('civolume\r')
        print('Infusion volume reset to :')
        self.get_infused_volume()

    def get_syringe_info(self):
        self.send('syrm\r')
        print(self._response)

    def get_infusion_rate(self):
        self.send('irate\r')
        print(self._response)

    def get_infused_volume(self):
        self.send('ivolume\r')
        print(self._response)

    def get_syringe_manufacturers(self):
        self.send('syrmanu ?\r')
        response = self._response[1:-1].split('\n')  # First and last values of the string are '\n'; remove these, then separate by '\n'
        for i in range(len(response)):
            syringe_info = response[i]
            syringe_info_separation = syringe_info.split('  ')  # Double spaces separate manufacturing code from manufacturing information
            self._manufacturers[syringe_info_separation[0]] = syringe_info_separation[1]

    def get_syringe_types(self):
        for code in self._manufacturers.keys():
            self.send(f'syrmanu {code} ?\r')
            self._syringes[code] = self._response[1:-1].split('\n')  # First and last values of each syringe's volume string are '\n', remove these, then separate by '\n'

    def print_available_syringes(self):
        for code, name in self._manufacturers.items():
            print(f'{name} ({code})')
            syringes = self._syringes[code]
            for syringe in syringes:
                print(f'\t {syringe}')
