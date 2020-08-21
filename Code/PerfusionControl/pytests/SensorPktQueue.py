from queue import Queue
from datetime import datetime

from MockOscSensor import MockOscSensor
from MockRampSensor import MockRampSensor


class TempSensor(MockOscSensor):
    def __init__(self, id, minval, maxval, period):
        super().__init__(minval, maxval, period)
        self.pkt = {'id': id, 'sensor_type': 'temperature', 'units': 'C', 'timestamp': None, 'value': None}

    @property
    def sample(self):
        self.pkt['value'] = self.get_sample()
        self.pkt['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.pkt


class CO2Sensor(MockRampSensor):
    def __init__(self, id, minval, maxval, rise, fall):
        super().__init__(minval, maxval, rise, fall)
        self.pkt = {'id': id, 'sensor_type': 'CO2', 'units': '%', 'timestamp': None, 'value': None}

    @property
    def sample(self):
        self.pkt['value'] = self.get_sample()
        self.pkt['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.pkt


class SensorPktQueue(Queue):
    """
    Queue of JSON packet for sensor data

    ...

    Attributes
    ----------

    Methods
    -------
    add_pkt(pkt)
        adds JSON Packet to queue
    get_pkt()
        returns JSON Packet from queue
    """

    def __init__(self):
        super().__init__(maxsize=100)

    def get_pkt(self):
        pkt = self.get()
        return pkt

    def add_pkt(self, pkt):
        self.put(pkt)