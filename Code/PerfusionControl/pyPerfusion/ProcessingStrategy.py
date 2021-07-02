# -*- coding: utf-8 -*-
"""Base class for processing stream data


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import pathlib
import datetime
import logging
from os import SEEK_END

import numpy as np


class ProcessingStrategy:
    def __init__(self, name, window_len, expected_buffer_len):
        self._logger = logging.getLogger(__name__)
        self._name = name
        self._data_type = np.float32
        self._win_len = window_len
        self._window_buffer = np.zeros(self._win_len, dtype=self._data_type)
        self._processed_buffer = np.zeros(expected_buffer_len, dtype=np.float32)

    def process_buffer(self, buffer):
        idx = 0
        for sample in buffer:
            front = self._window_buffer[0]
            self._window_buffer = np.roll(self._window_buffer, -1)
            self._window_buffer[-1] = sample
            self._processed_buffer = np.roll(self._processed_buffer, -1)
            self._processed_buffer[-1] = sample
            idx += 1
        return self._processed_buffer

    def reset(self):
        self._processed_buffer = np.zeros_like(self._window_buffer)

    def close(self):
        pass


class SaveStreamToFile(ProcessingStrategy):
    def __init__(self, name, window_len, expected_buffer_len):
        super().__init__(name, window_len, expected_buffer_len)
        self._version = 1
        self._ext = '.dat'
        self._timestamp = None
        self._last_idx = 0
        self._fid = None
        self._params = {}
        self._base_path = pathlib.Path.cwd()
        self._filename = pathlib.Path(f'{self._name}')
        self._header = {'File Format': f'{self._version}',
                        'Algorithm': f'{self._name}',
                        'Window Length': f'{self._win_len}'}

    @property
    def fqpn(self):
        return self._base_path / self._filename.with_suffix(self._ext)

    def _open_write(self):
        self._logger.info(f'opening for write: {self.fqpn}')
        self._fid = open(self.fqpn, 'a+b')

    def _write_to_file(self, data_buf):
        buf_len = len(data_buf)
        if self._fid:
            data_buf.tofile(self._fid)
            self._fid.flush()
            self._last_idx += buf_len

    def _get_stream_info(self):
        all_params = {**self._header, **self._params}
        hdr_str = [f'{k}: {v}\n' for k, v in all_params.items()]
        return ''.join(hdr_str)

    def _print_stream_info(self):
        hdr_str = self._get_stream_info()
        # print header info in a separate txt file to simply
        # reads using memory-mapped files
        fid = open(self.fqpn.with_suffix('').with_suffix('.txt'), 'wt')
        fid.write(hdr_str)
        fid.close()

    def open(self, base_path, sensor_params):
        self._params = sensor_params
        if not isinstance(base_path, pathlib.Path):
            base_path = pathlib.Path(base_path)
        self._base_path = base_path
        if not self._base_path.exists():
            self._base_path.mkdir(parents=True, exist_ok=True)
        self._timestamp = datetime.datetime.now()
        if self._fid:
            self._fid.close()
            self._fid = None

        self._print_stream_info()
        self._open_write()

    def close(self):
        self._fid.close()

    def process_buffer(self, buffer):
        self._write_to_file(buffer)
        return buffer


class RMSStrategy(ProcessingStrategy):
    def __init__(self, name, window_len, expected_buffer_len):
        super().__init__(name,window_len, expected_buffer_len)
        self._sum = 0

    def process_buffer(self, buffer):
        idx = 0
        for sample in buffer:
            sqr = sample * sample
            front = self._window_buffer[0]
            self._window_buffer = np.roll(self._window_buffer, -1)
            self._window_buffer[-1] = sqr
            self._sum += sqr - front
            rms = np.sqrt(self._sum / self._win_len)
            self._processed_buffer = np.roll(self._processed_buffer, -1)
            self._processed_buffer[-1] = rms
            idx += 1

        return self._processed_buffer

    def reset(self):
        super().reset()
        self._sum = 0
