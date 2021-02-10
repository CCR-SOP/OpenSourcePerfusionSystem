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
        self.__thread = None
        self._event_halt = Event()
        self.__lock_buf = Lock()
        self._period_sampling_ms = period_sample_ms
        self._demo_amp = demo_amp
        self._demo_offset = demo_offset

        self.__queue_buffer = {}

        self.__epoch = 0
        self._time = 0

        self._read_period_ms = read_period_ms
        self.data_type = data_type
        self.buf_type = buf_type
        self.samples_per_read = int(self._read_period_ms / self._period_sampling_ms)

    @property
    def period_sampling_ms(self):
        return self._period_sampling_ms

    @property
    def start_time(self):
        return self.__epoch

    @property
    def buf_len(self):
        return self.samples_per_read

    def add_channel(self, channel_id):
        if channel_id in self.__queue_buffer.keys():
            print(f'{channel_id} already open')
        else:
            self.__queue_buffer[channel_id] = Queue(maxsize=100)

    def remove_channel(self, channel_id):
        if channel_id in self.__queue_buffer.keys():
            del self.__queue_buffer[channel_id]
            print(f'removing channel {channel_id}')

    def open(self):
        pass

    def close(self):
        self.stop()
        self.__queue_buffer.clear()

    def start(self):
        self.stop()
        self._event_halt.clear()
        self.__epoch = perf_counter()
        self.__thread = Thread(target=self.run)
        self.__thread.start()

    def stop(self):
        if self.__thread and self.__thread.is_alive():
            self._event_halt.set()
            self.__thread.join(2.0)
            self.__thread = None

    def run(self):
        while not self._event_halt.wait(self._read_period_ms / 1000.0):
            with self.__lock_buf:
                self._acq_samples()

    def get_data(self, ch_id):
        buf = None
        t = None
        if self.__thread and self.__thread.is_alive():
            if ch_id in self.__queue_buffer.keys():
                buf, t = self.__queue_buffer[ch_id].get(timeout=1.0)
        return buf, t

    def _acq_samples(self):
        sleep_time = self._read_period_ms / self._period_sampling_ms / 1000.0
        sleep(sleep_time)
        buffer_t = perf_counter()
        for ch in self.__queue_buffer.keys():
            val = self.data_type(np.random.random_sample() * self._demo_amp + self._demo_offset)
            buffer = np.ones(self.samples_per_read, dtype=self.data_type) * val
            print(f'putting {len(buffer)} samples in channel {ch}')
            self.__queue_buffer[ch].put((buffer, buffer_t))
