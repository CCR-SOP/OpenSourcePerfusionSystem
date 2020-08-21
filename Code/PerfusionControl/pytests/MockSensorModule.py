from threading import Thread, Lock, Timer, Event
import time
import requests
from datetime import datetime

from SensorPktQueue import SensorPktQueue, TempSensor, CO2Sensor
from SplunkHEC import SplunkHEC, SplunkInstance


class MockAcqModule(Thread):
    """
    Base class for acquiring mock sensor data. Generates data from multiple MockSensors, generate JSON packets, and
    places those packets in a Queue

    ...

    Attributes
    ----------
    period_sampling_ms : int
        sampling period, in milliseconds, for all sensors

    Methods
    -------
    add_sensor(MockSensor)
        adds a MockSensor to the module
    halt_acq()
        halts the acquisition of mock sensor data
    """

    def __init__(self, pkt_queue):
        Thread.__init__(self)
        self._event_halt = Event()
        self.__sensor_lock = Lock()
        self.period_sampling_ms = 1000
        self.__epoch = time.perf_counter()
        self._time = 0
        self.__sensors = []
        self.__queue = pkt_queue

    def run(self):
        while not self._event_halt.wait(self.period_sampling_ms/1000.0):
            self._time = time.perf_counter() - self.__epoch
            with self.__sensor_lock:
                for sensor in self.__sensors:
                    self.__queue.add_pkt(sensor.sample)

    def halt(self):
        self._event_halt.set()
        with self.__sensor_lock:
            for sensor in self.__sensors:
                sensor.halt()

    def add_sensor(self, sensor):
        with self.__sensor_lock:
            self.__sensors.append(sensor)


class CommModule(Thread):
    """
    Module for sending JSON packets to external server using HTTPS PUT JSON.

    ...

    Attributes
    ----------
    comm_transfer_ms : int
        Periodic timer, in milliseconds, which send all available packets to server

    Methods
    -------
    pause_transfer()
        Pauses transfer of packets. Can be used to test comm failures and ability to store packets during
        comm failure periods
    resume_transfer()
        Resume transfer of queued packets. Will immediately send all queued packets.
    """

    def __init__(self, pkt_queue, module_id, splunk_instance):
        Thread.__init__(self)
        self._event_halt = Event()
        self.comm_transfer_ms = 1000
        self.__epoch = time.perf_counter()
        self._time = 0
        self.__queue = pkt_queue
        self.__server = SplunkHEC(module_id, splunk_instance)

    def run(self):
        while not self._event_halt.wait(self.comm_transfer_ms/1000.0):
            self._time = time.perf_counter() - self.__epoch
            while not self.__queue.empty():
                pkt = self.__queue.get_pkt()
                self.__server.post_json(pkt)

    def halt(self):
        self._event_halt.set()


class MockSensorModule():
    """
    Class to mock a sensor module

    ...

    Attributes
    ----------

    Methods
    -------
    """

    def __init__(self, id, splunk_instance):
        self.__id = id
        self.__queue = SensorPktQueue()
        self.__acq = MockAcqModule(self.__queue)
        self.__comm = CommModule(self.__queue, self.__id, splunk_instance)
        self.__acq.start()
        self.__comm.start()

    def __del__(self):
        self.__acq.halt()
        self.__comm.halt()

    def add_sensor(self, sensor):
        self.__acq.add_sensor(sensor)
        sensor.start()
