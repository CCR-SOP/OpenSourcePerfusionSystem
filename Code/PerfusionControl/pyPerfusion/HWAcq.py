from threading import Thread, Lock, Event
import time
from queue import Queue
import numpy as np


class HWAcq(Thread):
    """
    Base class for streaming data from sensors and saving to file

    ...

    Attributes
    ----------
    _period_sampling_ms : int
        sampling period, in milliseconds, for all sensors

    Methods
    -------
    start()
        starts the acquisition of sensor data
    halt()
        halts the acquisition of  sensor data

    """

    def __init__(self, period_sample_ms):

        Thread.__init__(self)
        self.__queue_buffer = Queue(maxsize=100)
        self.__buffer = np.zeros(100, dtype=np.uint16)
        self._event_halt = Event()
        self.__lock_buf = Lock()
        self.__epoch = time.perf_counter()
        self._time = 0
        self._period_sampling_ms = period_sample_ms
        self.datatype = np.uint32

    @property
    def period_sampling_ms(self):
        return self._period_sampling_ms

    def run(self):
        while not self._event_halt.wait(self._period_sampling_ms / 1000.0):
            with self.__lock_buf:
                self._time = time.perf_counter() - self.__epoch
                self._acq_samples()
                data = self.__buffer  #   * 1.0 + 0.0
                self.__queue_buffer.put(data)

    def halt(self):
        self._event_halt.set()

    def _acq_samples(self):
        sleep_time = 100 * self._period_sampling_ms / 1000.0
        time.sleep(sleep_time)
        val = np.random.randint(70, 80, size=1, dtype=self.datatype)
        print(f'value is {val}')
        self.__buffer = np.ones(100, dtype=self.datatype) * val

    def get_data(self):
        buf = None
        if self.is_alive():
            if not self.__queue_buffer.empty():
                buf = self.__queue_buffer.get(timeout=1.0)
        return buf

    def adc_to_units(self, sample):
        return sample * 1.0 + 0.0
