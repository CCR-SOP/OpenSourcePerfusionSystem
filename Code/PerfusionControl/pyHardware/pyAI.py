from threading import Thread, Lock, Event
from time import perf_counter, sleep
from queue import Queue
import numpy as np


class AI:
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

    def __init__(self, period_sample_ms, buf_type=np.uint16, data_type=np.float32, demo_amp=70, demo_offset=10, read_period_ms=500):
        self._period_sampling_ms = period_sample_ms
        self._demo_amp = demo_amp
        self._demo_offset = demo_offset
        self.__queue_buffer = Queue(maxsize=100)
        self.__thread = None

        self.buffer_t = 0
        self._event_halt = Event()
        self.__lock_buf = Lock()
        self.__epoch = 0
        self._time = 0

        self._read_period_ms = read_period_ms
        self.data_type = data_type
        self.buf_type = buf_type
        self.samples_per_read = int(self._read_period_ms / self._period_sampling_ms)
        self._buffer = np.zeros(self.samples_per_read, dtype=self.buf_type)

    @property
    def period_sampling_ms(self):
        return self._period_sampling_ms

    @property
    def start_time(self):
        return self.__epoch

    @property
    def buf_len(self):
        return len(self._buffer)

    def open(self):
        if self.__thread:
            self.halt()
            self.__thread.join(timeout=2.0)
        self.__thread = Thread(target=self.run)

    def start(self):
        self.__epoch = perf_counter()
        if self.__thread:
            print('starting thread')
            self.__thread.start()

    def run(self):
        while not self._event_halt.wait(self._read_period_ms / 1000.0):
            with self.__lock_buf:
                self._acq_samples()
                data = self._convert_to_units()

                self.__queue_buffer.put((data, self.buffer_t))

    def close(self):
        pass

    def halt(self):
        self._event_halt.set()
        self.__thread.join(2.0)
        self.close()

    def get_data(self):
        buf = None
        t = None
        if self.__thread and self.__thread.is_alive():
            if not self.__queue_buffer.empty():
                buf, t = self.__queue_buffer.get(timeout=1.0)
        return buf, t

    def _convert_to_units(self):
        return self._buffer * 1.0 + 0.0

    def _acq_samples(self):

        sleep_time = self._read_period_ms / self._period_sampling_ms / 1000.0
        sleep(sleep_time)
        self.buffer_t = perf_counter()
        val = self.data_type(np.random.random_sample() * self._demo_amp + self._demo_offset)
        self._buffer = np.ones(self.samples_per_read, dtype=self.data_type) * val
