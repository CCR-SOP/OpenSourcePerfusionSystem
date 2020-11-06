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

    def open(self, port_name, baud, addr):
        super().open(port_name, baud)
        self.__addr = addr
        self._USBSerial__serial.xonxoff = True
        self.send('')
        self.send(f'address {self.__addr}')
        self.send('poll REMOTE\r')
        # self.send('ascale 100\r')

    def infuse(self):
        self.send('poll REMOTE\r')
        self.send('irun\r')

    def stop(self):
        self.send('poll REMOTE\r')
        self.send('stop\r')

    def set_param(self, param, value):
        self.send('poll OFF\r')
        self.send(f'{param} {value}')
        self.send('poll REMOTE\r')

    def set_syringe_manufacturer_size_rate(self, manu_code, syringe_size, ml_min):
        # rate can be changed mid run
        # BD_plastic_dictionary = {1: 4.699, 3: 8.585, 5: 11.989, 10: 14.427, 20: 19.05, 30: 21.59, 50: 26.594, 60: 26.594}
        self.send('poll OFF\r')
        self.set_param(f'syrm', '%s %d ml' % (manu_code, syringe_size))
        print('New Syringe Information:')
        self.get_syringe_info()
        self.send('poll REMOTE\r')
        self.send('poll OFF\r')
        self.set_param('irate', f'{ml_min} ml/min\r')
        print('Infusion rate set to :')
        self.get_infusion_rate()
        self.send('poll REMOTE\r')

    def set_infusion_rate(self, ml_min):  # can be changed mid-run
        self.send('poll OFF\r')
        self.set_param('irate', f'{ml_min} ml/min\r')
        print('Infusion rate set to :')
        self.get_infusion_rate()
        self.send('poll REMOTE\r')

    def reset_infusion_volume(self):
        self.send('poll OFF\r')
        self.send('civolume\r')
        print('Infusion volume reset to :')
        self.get_infused_volume()
        self.send('poll REMOTE\r')

    def get_syringe_info(self):
        self.send('poll OFF\r')
        self.send('syrm\r')
        valid_manu = True
        while valid_manu:
            response = self.get_response(max_bytes=1000)
            if response == '':
                valid_manu = False
            else:
                ends = []
                for i in range(len(response)):
                    if response[i] == ':' or response[i] == '>':
                        ends.append(i)
                response = response[ends[-2]+1:ends[-1]-1]
                print(response)

        # restore polling
        self.send('poll REMOTE\r')

    def get_infusion_rate(self):
        self.send('poll OFF\r')
        self.send('irate\r')
        valid_manu = True
        while valid_manu:
            response = self.get_response(max_bytes=1000)
            if response == '':
                valid_manu = False
            else:
                ends = []
                for i in range(len(response)):
                    if response[i] == ':' or response[i] == '>':
                        ends.append(i)
                response = response[ends[-2]+1:ends[-1]-1]
                print(response)

        # restore polling
        self.send('poll REMOTE\r')

    def get_infused_volume(self):
        self.send('poll OFF\r')
        self.send('ivolume\r')
        valid_manu = True
        while valid_manu:
            response = self.get_response(max_bytes=1000)
            if response == '':
                valid_manu = False
            else:
                ends = []
                for i in range(len(response)):
                    if response[i] == ':' or response[i] == '>':
                        ends.append(i)
                response = response[ends[-2] + 1:ends[-1] - 1]
                print(response)

        # restore polling
        self.send('poll REMOTE\r')

    def get_syringe_manufacturers(self):
        # make sure polling is off to get a response
        # make sure polling is remote before turning polling off so that semicolons will flank response string
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
        # make sure polling is off to get a response
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
