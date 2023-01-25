# -*- coding: utf-8 -*-
"""Strategy for reading/writing data to a file

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import pathlib
import datetime
import logging
import struct
from time import perf_counter
from os import SEEK_END
from collections import deque
from datetime import datetime

import numpy as np

from pyPerfusion.ProcessingStrategy import ProcessingStrategy
import pyPerfusion.PerfusionConfig as PerfusionConfig


class StreamToFile(ProcessingStrategy):
    def __init__(self, name, window_len, expected_buffer_len):
        super().__init__(name, window_len, expected_buffer_len)
        self._lgr = logging.getLogger(__name__)
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
        self._lgr.info(f'opening for write: {self.fqpn}')
        self._fid = open(self.fqpn, 'w+b')

    def _open_read(self):
        try:
            _fid = open(self.fqpn, 'rb')
        except FileNotFoundError as e:
            logging.exception(e)
            return None, None
        data_type = np.dtype(self._sensor_params['Data Format'])
        try:
            data = np.memmap(_fid, dtype=data_type, mode='r')
        except ValueError as e:
            # cannot mmap an empty file
            # self._lgr.debug(f'in StreamToFile:_open_read: attempt to read from empty file: {e}')
            data = []
        return _fid, data

    def _write_to_file(self, data_buf, t=None):
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

    def open(self, sensor=None):
        if sensor is None:
            self._lgr.error(f'FileStrategy:open requires a sensor as a parameter')
            return
        self._base_path = PerfusionConfig.get_date_folder()
        self._filename = pathlib.Path(f'{sensor.name}_{self._name}')
        self._sensor_params = sensor.params
        self._timestamp = datetime.now()
        if self._fid:
            self._fid.close()
            self._fid = None

        self._print_stream_info()
        self._open_write()

    def close(self):
        self._fid.close()

    def process_buffer(self, buffer, t=None):
        self._write_to_file(buffer, t)
        return buffer

    def retrieve_buffer(self, last_ms, samples_needed):
        _fid, data = self._open_read()
        file_size = len(data)
        if not _fid or file_size == 0:
            return [], []

        period = self._sensor_params['Sampling Period (ms)']
        data_type = self._sensor_params['Data Format']
        if last_ms == 0:
            # if last x samples requested, no timestamps are returned
            data = data[-samples_needed:]
            start_idx = file_size - len(data)
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


class PointsToFile(StreamToFile):
    def __init__(self, name, window_len, expected_buffer_len):
        super().__init__(name, window_len, expected_buffer_len)
        self._lgr = logging.getLogger(__name__)
        self._name = name
        self._version = 2
        self._ext = '.dat'
        self._ext_hdr = '.txt'
        self._timestamp = None
        self._last_idx = 0
        self._fid = None
        self._sensor_params = {}
        self._base_path = pathlib.Path.cwd()
        self._filename = pathlib.Path(f'{self._name}')
        self._bytes_per_ts = 4
        # don't update Algorithm param as we want to pass through
        # whatever any previous algorithm named used
        self._params['File Format'] = f'{self._version}'

    def _write_to_file(self, data_buf, t=None):
        ts_bytes = struct.pack('i', int(t * 1000.0))
        self._fid.write(ts_bytes)
        data_buf.tofile(self._fid)

    def _read_chunk(self, _fid):
        ts = 0
        data_buf = []
        ts_bytes = _fid.read(self._bytes_per_ts)
        data_type = self._sensor_params['Data Format']
        samples_per_ts = self._sensor_params['Samples Per Timestamp']
        if len(ts_bytes) == 4:
            ts, = struct.unpack('i', ts_bytes)
            data_buf = np.fromfile(_fid, dtype=data_type, count=samples_per_ts)

        return data_buf, ts

    def retrieve_buffer(self, last_ms, samples_needed):
        _fid, tmp = self._open_read()
        cur_time = int(perf_counter() * 1000)
        _fid.seek(0)
        chunk = [1]
        data_time = []
        data = []
        first_time = None
        samples_per_ts = self._sensor_params['Samples Per Timestamp']
        bytes_per_chunk = self._bytes_per_ts + (samples_per_ts * self._data_type(1).itemsize)

        # start by assuming file contains only full chunks
        sampling_period_ms = self._sensor_params['Sampling Period (ms)']
        expected_chunks = int(last_ms / sampling_period_ms)
        jump_back = bytes_per_chunk * expected_chunks*2
        try:
            _fid.seek(-jump_back, SEEK_END)
        except OSError:
            _fid.seek(0)
        while len(chunk) > 0:
            chunk, ts = self._read_chunk(_fid)
            if not first_time:
                first_time = ts
            if chunk is not None and (cur_time - ts < last_ms or last_ms == 0 or last_ms == -1):
                data.append(chunk)
                data_time.append((ts - first_time) / 1000.0)
        inc = int(len(data) / samples_needed)
        data = data[0:-1:inc]
        _fid.close()
        return data_time, data

    def get_last_acq(self):
        _fid, tmp = self._open_read()
        samples_per_ts = self._sensor_params['Samples Per Timestamp']
        bytes_per_chunk = self._bytes_per_ts + (samples_per_ts * self._data_type(1).itemsize)
        try:
            _fid.seek(-bytes_per_chunk, SEEK_END)
            chunk, ts = self._read_chunk(_fid)
        except OSError as e:
            logging.exception(e)
            chunk = None
            ts = None

        _fid.close()
        return ts, chunk

    def get_current(self):
        ts, chunk = self.get_last_acq()
        if chunk is not None:
            avg = np.mean(chunk)
        else:
            avg = None
        return avg

    def get_data_from_last_read(self, timestamp):
        _fid, tmp = self._open_read()
        samples_per_ts = self._sensor_params['Samples Per Timestamp']
        bytes_per_chunk = self._bytes_per_ts + (samples_per_ts * np.dtype(self._data_type).itemsize)
        ts = timestamp + 1
        data = deque()
        data_t = deque()
        _fid.seek(0, SEEK_END)
        loops = 0
        while ts > timestamp:
            loops += 1
            offset = bytes_per_chunk * loops
            try:
                _fid.seek(-offset, SEEK_END)
            except OSError as e:
                # attempt to read before beginning of file
                self._lgr.warning(f'Attempted to read from before beginning of file with offset {offset}')
                break
            else:
                chunk, ts = self._read_chunk(_fid)
                if ts and ts > timestamp:
                    data_t.extendleft([ts])
                    data.extendleft(chunk)
        _fid.close()
        return data_t, data


class MultiVarToFile(PointsToFile):
    def _write_to_file(self, data_buf, t=None):
        data = data_buf.get_array()
        buf = np.array(data, dtype=np.float32)

        # h = int(ts[0:2])
        # m = int(ts[3:5])
        # s = int(ts[6:8])
        # timestamp = datetime.strptime(f'{h:02d}:{m:02d}:{s:02d}', '%H:%M:%S').replace(year=self._timestamp.year,
        #                                                                               month=self._timestamp.month,
        #                                                                               day=self._timestamp.day)
        # ts = (timestamp - self._timestamp).total_seconds() * 1000
        # ts_bytes = struct.pack('i', int(ts* 1000.0))
        # self._fid.write(ts_bytes)
        # buf.tofile(self._fid)
        super()._write_to_file(buf, t)


class MultiVarFromFile(PointsToFile):
    def __init__(self, name, window_len, expected_buffer_len, index):
        super().__init__(name, window_len, expected_buffer_len)
        self._index = index

        self._bytes_per_ts = 4

    def run(self):
        pass
