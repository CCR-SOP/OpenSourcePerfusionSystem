import logging
import serial



class USBSerial:
    """
    Base class for serial communication over USB


    Attributes
    ----------
    _port_name : basestring
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
        self._logger = logging.getLogger(__name__)
        self._port_name = None
        self._baud = None
        self.__serial = serial.Serial()

    @property
    def port_name(self):
        return self._port_name

    @property
    def baud(self):
        return self._baud

    def open(self, port_name, baud):
        self._port_name = port_name
        self._baud = baud
        if self.__serial.is_open:
            self.__serial.close()

        self.__serial.port = self._port_name
        self.__serial.baudrate = self._baud
        self.__serial.open()

    def close(self):
        self.__serial.close()

    def send(self, str2send):
        if self.__serial.is_open:
            self.__serial.write(str2send.encode('UTF-8'))
            self.__serial.flush()

    def get_response(self, max_bytes=1, eol='\r', timeout=1.0):
        response = ''
        if self.__serial.is_open:
            self.__serial.timeout = timeout
            response = self.__serial.read_until(eol, size=max_bytes).decode('UTF-8')
            #
        return response

    def recv(self, expected_bytes, timeout=0):
        if self.__serial.is_open:
            self.__serial.timeout = timeout
            bytes = self.__serial.read(expected_bytes)
            return bytes
