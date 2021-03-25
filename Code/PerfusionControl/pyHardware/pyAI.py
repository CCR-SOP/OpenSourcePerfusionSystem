from threading import Thread, Lock, Event
from time import perf_counter, sleep
from queue import Queue, Empty
import logging

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

    def __init__(self, period_sample_ms, buf_type=np.uint16, data_type=np.float32, read_period_ms=500):
        self._logger = logging.getLogger(__name__)
        self.__thread = None
        self._event_halt = Event()
        self.__lock_buf = Lock()
        self._period_sampling_ms = period_sample_ms
        self._demo_amp = {}
        self._demo_offset = {}

        self._queue_buffer = {}

        self.__epoch = 0
        self._time = 0

        self._read_period_ms = read_period_ms
        self.data_type = data_type
        self.buf_type = buf_type
        self.samples_per_read = int(self._read_period_ms / self._period_sampling_ms)

        self._calibration = {}

    @property
    def period_sampling_ms(self):
        return self._period_sampling_ms

    @property
    def start_time(self):
        return self.__epoch

    @property
    def buf_len(self):
        return self.samples_per_read

    def set_demo_properties(self, ch, demo_amp, demo_offset):
        self._demo_amp[ch] = demo_amp
        self._demo_offset[ch] = demo_offset

    def set_read_period_ms(self, period_ms):
        self._read_period_ms = period_ms
        self.samples_per_read = int(self._read_period_ms / self._period_sampling_ms)

    def set_calibration(self, ch, low_pt, low_read, high_pt, high_read):
        self._calibration[ch] = [low_pt, low_read, high_pt, high_read]

    def active_channels(self):
        return len(self._queue_buffer) > 0

    def get_ids(self):
        return sorted(self._queue_buffer.keys())

    def add_channel(self, channel_id):
        if channel_id in self._queue_buffer.keys():
            self._logger.warning(f'{channel_id} already open')
        else:
            self.stop()
            with self.__lock_buf:
                self._queue_buffer[channel_id] = Queue(maxsize=100)
                self._demo_amp[channel_id] = 0
                self._demo_offset[channel_id] = 0
                if channel_id in self._calibration.keys():  # If a calibration has already been performed for this channel, retain it
                    pass
                else:
                    self._calibration[channel_id] = []
            self.reopen()
            self.start()

    def remove_channel(self, channel_id):
        if channel_id in self._queue_buffer.keys():
            self.stop()
            with self.__lock_buf:
                del self._queue_buffer[channel_id]
            self.reopen()
            self.start()

    def open(self):
        pass

    def reopen(self):
        pass

    def close(self):
        self.stop()
        self._queue_buffer.clear()

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
            if ch_id in self._queue_buffer.keys():
                try:
                    buf, t = self._queue_buffer[ch_id].get(timeout=1.0)
                except Empty:
                    pass
        return buf, t

    def _acq_samples(self):
        sleep_time = self._read_period_ms / self._period_sampling_ms / 1000.0
        sleep(sleep_time)
        buffer_t = perf_counter()
        for ch in self._queue_buffer.keys():
            val = self.data_type(np.random.random_sample() * self._demo_amp[ch] + self._demo_offset[ch])
            buffer = np.ones(self.samples_per_read, dtype=self.data_type) * val
            self._queue_buffer[ch].put((buffer, buffer_t))

    def _convert_to_units(self, buffer, channel):
        data = np.zeros_like(buffer)
        for i in range(len(buffer)):
            data[i] = (((buffer[i] - self._calibration[channel][1]) * (
                        self._calibration[channel][2] - self._calibration[channel][0]))
                       / (self._calibration[channel][3] - self._calibration[channel][1])) + self._calibration[channel][
                          0]
        #    print(f'Convert {buffer[i]} to {data[i]}')
        return data