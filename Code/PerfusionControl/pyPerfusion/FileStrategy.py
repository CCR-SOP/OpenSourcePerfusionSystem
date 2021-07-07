# -*- coding: utf-8 -*-
"""Strategy for reading/writing data to a file

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import pathlib
import datetime

import numpy as np

from pyPerfusion.ProcessingStrategy import ProcessingStrategy


class StreamToFile(ProcessingStrategy):
    def __init__(self, name, window_len, expected_buffer_len):
        super().__init__(name, window_len, expected_buffer_len)
        self._version = 1
        self._ext = '.dat'
        self._ext_hdr = '.txt'
        self._timestamp = None
        self._last_idx = 0
        self._fid = None
        self._sensor_params = {}
        self._base_path = pathlib.Path.cwd()
        self._filename = pathlib.Path(f'{self._name}')
        # don't update Algorithm param as we want to pass through
        # whatever any previous algorithm named used
        self._params['File Format'] = f'{self._version}'

    @property
    def fqpn(self, hdr=False):
        ext = self._ext_hdr if hdr else self._ext
        return self._base_path / self._filename.with_suffix(ext)

    def _open_write(self):
        self._logger.info(f'opening for write: {self.fqpn}')
        self._fid = open(self.fqpn, 'w+b')

    def _open_read(self):
        _fid = open(self.fqpn, 'rb')
        data_type = np.dtype(self._sensor_params['Data Format'])
        try:
            data = np.memmap(_fid, dtype=data_type, mode='r')
        except ValueError:
            # cannot mmap an empty file
            data = []
        return _fid, data

    def _write_to_file(self, data_buf):
        buf_len = len(data_buf)
        if self._fid:
            data_buf.tofile(self._fid)
            self._fid.flush()
            self._last_idx += buf_len

    def _get_stream_info(self):
        all_params = {**self._params, **self._sensor_params}
        hdr_str = [f'{k}: {v}\n' for k, v in all_params.items()]
        return ''.join(hdr_str)

    def _print_stream_info(self):
        hdr_str = self._get_stream_info()
        # print header info in a separate txt file to simply
        # reads using memory-mapped files
        fid = open(self.fqpn.with_suffix('').with_suffix('.txt'), 'wt')
        fid.write(hdr_str)
        fid.close()

    def open(self, base_path=None, filename=None, sensor_params=None):
        self._filename = pathlib.Path(filename)
        self._sensor_params = sensor_params
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

    def retrieve_buffer(self, last_ms, samples_needed):
        _fid, data = self._open_read()
        if not _fid:
            return [], []
        file_size = len(data)
        period = self._sensor_params['Sampling Period (ms)']
        data_type = self._sensor_params['Data Format']
        if last_ms == 0:
            data = data[-samples_needed:]
            data_time = None
        else:
            if last_ms > 0:
                data_size = int(last_ms / period)
                if samples_needed > data_size:
                    samples_needed = data_size
                start_idx = file_size - data_size
                if start_idx < 0:
                    start_idx = 0
            else:
                start_idx = 0
            idx = np.linspace(start_idx, file_size-1, samples_needed,
                              dtype=np.int32)
            data = data[idx]

            start_t = start_idx * period / 1000.0
            stop_t = file_size * period / 1000.0
            data_time = np.linspace(start_t, stop_t, samples_needed,
                                    dtype=data_type)
        _fid.close()

        return data_time, data
