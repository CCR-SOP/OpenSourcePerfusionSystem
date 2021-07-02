import pathlib
import datetime
from threading import Thread, Event
import logging
import time

import numpy as np

from pyPerfusion.ProcessingStrategy import ProcessingStrategy, SaveStreamToFile


DATA_VERSION = 1


class SensorStream:
    def __init__(self, name, unit_str, hw, valid_range=None):
        self._logger = logging.getLogger(__name__)
        self._logger.info(f'Creating SensorStream object {name}')
        self.__thread = None
        self._unit_str = unit_str
        self._valid_range = valid_range
        self.hw = hw
        self._ch_id = None
        self.__evt_halt = Event()
        self.data = None
        self.name = name
        self._timestamp = None
        self.data = np.array(self.hw.buf_len, dtype=self.hw.data_type)
        self._strategies = []
        self._params = {'Sensor': self.name,
                        'Unit': self._unit_str,
                        'Data Format': str(np.dtype(self.hw.data_type)),
                        'Sampling Period (ms)': self.hw.period_sampling_ms,
                        'Start of Acquisition': 0
                        }

    @property
    def buf_len(self):
        return self.hw.buf_len

    @property
    def unit_str(self):
        return self._unit_str

    @property
    def valid_range(self):
        return self._valid_range

    @property
    def ch_id(self):
        return self._ch_id

    def add_strategy(self, strategy: ProcessingStrategy):
        self._strategies.append(strategy)

    def run(self):
        next_t = time.time()
        offset = 0
        while not self.__evt_halt.is_set():
            next_t += offset + self.hw.period_sampling_ms / 1000.0
            delay = next_t - time.time()
            if delay > 0:
                time.sleep(delay)
                offset = 0
            else:
                offset = -delay
            data_buf, t = self.hw.get_data(self._ch_id)
            if data_buf is not None:
                buf = data_buf

                for strategy in self._strategies:
                    buf = strategy.process_buffer(buf)

    def _open_read(self):
        # Assumes first strategy is the raw data strategy
        _fid = open(self._strategies[0].fqpn, 'rb')
        data = np.memmap(_fid, dtype=self.hw.data_type, mode='r')
        return _fid, data

    def start(self):
        if self.__thread:
            self.__thread.start()

    def set_ch_id(self, ch_id):
        self._ch_id = ch_id

    def open(self, full_path):
        self._timestamp = datetime.datetime.now()
        self._params['Start of Acquisition'] = self._timestamp.strftime('%Y-%m-%d_%H:%M')
        # TODO, how to handle start of acq?
        self.__thread = Thread(target=self.run)
        self.__thread.name = f'SensorStream ({self.name})'

    def stop(self):
        self.__evt_halt.set()
        if self.__thread:
            self.__thread.join(2.0)
        for strategy in self._strategies:
            strategy.close()

    def get_data(self, last_ms, samples_needed):
        _fid, data = self._open_read()
        file_size = len(data)
        if last_ms > 0:
            data_size = int(last_ms / self.hw.period_sampling_ms)
            if samples_needed > data_size:
                samples_needed = data_size
            start_idx = file_size - data_size
            if start_idx < 0:
                start_idx = 0
        else:
            start_idx = 0
        idx = np.linspace(start_idx, file_size-1, samples_needed, dtype=np.int)
        data = data[idx]

        start_t = start_idx * self.hw.period_sampling_ms / 1000.0
        stop_t = file_size * self.hw.period_sampling_ms / 1000.0
        data_time = np.linspace(start_t, stop_t, samples_needed, dtype=np.float32)
        _fid.close()

        return data_time, data

    def get_current(self):
        _fid, data = self._open_read()
        val = data[-1]
        _fid.close()

        return val

    def get_latest(self, readings):
        _fid, data = self._open_read()
        val = data[-readings:]
        _fid.close()

        return val
