import pyserial


class USBSerial:
    """
    Base class for serial communication over USB

    ...

    Attributes
    ----------
    _port : basestring
            Name of serial port (e.g. 'COM4')
    _baud : number
            Baud rate to be used (e.g. 115_200)

    Methods
    -------
    open(port_name, baud)
        opens USB port of given name with the specified baud rate
    close()
        close the USB port
    send(str)
        sends a string of data over the port
    recv()
        retrieves a string of data over the port

    """

    def __init__(self):
        self._port_name = None
        self._baud = None
        self.__port = None

    @property
    def port_name(self):
        return self._port_name

    @property
    def baud(self):
        return self._baud

    def open(self, port_name, baud):
        self._port_name = port_name
        self._baud = baud
        if self.__port and self.__port.is_open:
            self.close()
            self.__port = pyserial.open(self._port_name, self._baud)

    def close(self):
        self.__port.close()

    def send(self, str2send):
        if self.__port.is_open:
            self.__port.write(str2send.encode('UTF-8'))
            self.__port.flush()

    def recv(self, expected_bytes, timeout=0):
        if self.__port.is_open:
            bytes = self.__port.read(expected_bytes, timeout)
            return bytes
