# -*- coding: utf-8 -*-
""" Strategy for reading/writing data to a file

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
from dataclasses import dataclass, asdict

import numpy as np

import pyPerfusion.PerfusionConfig as PerfusionConfig


@dataclass
class WriterConfig:
    name: str = ''
    algorithm: str = "WriterStream"
    data_type = np.float64
    sampling_period_ms: int = 0


@dataclass
class WriterPointsConfig:
    name: str = ''
    algorithm: str = "WriterPoints"
    data_type = np.float64
    bytes_per_timestamp: int = 4
    samples_per_timestamp: int = 1


class Reader:
    def __init__(self, fqpn: pathlib.Path, cfg: WriterConfig):
        self._lgr = logging.getLogger(__name__)
        self._version = 1
        self.fqpn = fqpn
        self.cfg = cfg
        self._last_idx = 0

    @property
    def name(self):
        return self.cfg.name

    def _open_read(self, data_type):
        fid = None
        data = []
        try:
            fid = open(self.fqpn, 'rb')
            data = np.memmap(fid, dtype=data_type, mode='r')
        except ValueError as e:
            # cannot mmap an empty file
            # this can happen if attempting to read a file before the first data was written
            # ignore the error and continue processing
            pass
        return fid, data

    def retrieve_buffer(self, last_ms, samples_needed):
        period = self.cfg.sampling_period_ms
        _fid, data = self._open_read(self.cfg.data_type)
        file_size = len(data)
        if not _fid or file_size == 0:
            return [], []
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
        data_time = np.linspace(start_t, stop_t, samples_needed, dtype=self.cfg.data_type)
        _fid.close()
        return data_time, data


class ReaderPoints(Reader):
    def __init__(self, fqpn: pathlib.Path, cfg: WriterPointsConfig):
        self._lgr = logging.getLogger(__name__)
        super().__init__(fqpn, cfg)
        self._version = 1
        self.fqpn = fqpn
        self.cfg = cfg
        self._last_idx = 0

    def _read_chunk(self, _fid):
        ts = 0
        data_buf = []
        ts_bytes = _fid.read(self.cfg.bytes_per_timestamp)
        if len(ts_bytes) == 4:
            ts, = struct.unpack('i', ts_bytes)
            data_buf = np.fromfile(_fid, dtype=self.cfg.data_type, count=self.cfg.samples_per_timestamp)

        return data_buf, ts

    def retrieve_buffer(self, last_ms, samples_needed):
        self._lgr.debug(f'samples_needed={samples_needed}, last_ms = {last_ms}')
        _fid, tmp = self._open_read(self.cfg.data_type)
        _fid.seek(0)
        chunk = [1]
        data_time = []
        data = []
        final_ts = None
        bytes_per_chunk = self.cfg.bytes_per_timestamp + (self.cfg.samples_per_timestamp * self.cfg.data_type(1).itemsize)
        # start by assuming file contains only full chunks
        expected_chunks = 10
        jump_back = bytes_per_chunk * expected_chunks*2
        try:
            _fid.seek(-jump_back, SEEK_END)
        except OSError:
            _fid.seek(0)
        while len(chunk) > 0:
            chunk, ts = self._read_chunk(_fid)
            if final_ts is None:
                final_ts = ts
            if chunk is not None and (final_ts - ts < last_ms or last_ms == 0 or last_ms == -1):
                data.append(chunk)
                data_time.append(ts / 1000.0)
        inc = int(len(data) / samples_needed)
        if inc > 0:
            data = data[0:-1:inc]
        _fid.close()
        self._lgr.debug(f'data_time is {data_time}')
        return data_time, data

    def get_last_acq(self):
        _fid, tmp = self._open_read()
        bytes_per_chunk = self.cfg.bytes_per_timestamp + (self.cfg.samples_per_timestamp * np.dtype(self.cfg.data_type))
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
        bytes_per_chunk = self.cfg.bytes_per_timestamp + (self.cfg.samples_per_timestamp * np.dtype(self.cfg.data_type))
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


class WriterStream:
    def __init__(self, cfg: WriterConfig):
        self._lgr = logging.getLogger(__name__)
        self.cfg = cfg
        self._ext = '.dat'
        self._ext_hdr = '.txt'
        self._timestamp = None
        self._last_idx = 0
        self._fid = None
        self._base_path = pathlib.Path.cwd()
        self._filename = pathlib.Path(f'{self.cfg.name}')
        self.cfg.version = 1

        self._processed_buffer = None


    @classmethod
    def get_config_type(cls):
        return WriterConfig

    @property
    def fqpn(self):
        return self._base_path / self._filename.with_suffix(self._ext)

    def get_reader(self):
        return Reader(self.fqpn, self.cfg)

    def _open_write(self):
        self._lgr.info(f'opening for write: {self.fqpn}')
        self._fid = open(self.fqpn, 'w+b')

    def _write_to_file(self, data_buf, t=None):
        if self._fid:
            try:
                data_buf.tofile(self._fid)
            except OSError as e:
                self._lgr.error(f'{self.cfg.name}: {e}')
            self._fid.flush()
            self._last_idx += len(data_buf)

    def _get_stream_info(self):
        # all_params = {**self._params, **self._sensor_params}
        all_params = asdict(self.cfg)
        hdr_str = [f'{k}: {v}\n' for k, v in all_params.items()]
        return ''.join(hdr_str)

    def _print_stream_info(self):
        hdr_str = self._get_stream_info()
        # print header info in a separate txt file to simply
        # reads using memory-mapped files
        fid = open(self.fqpn.with_suffix('').with_suffix('.txt'), 'wt')
        fid.write(hdr_str)
        fid.close()

    def open(self, sensor_name: str = None):
        self._base_path = PerfusionConfig.get_date_folder()
        self._filename = pathlib.Path(f'{sensor_name}_{self.cfg.name}')
        self._timestamp = datetime.now()
        if self._fid:
            self._fid.close()
            self._fid = None

        self._print_stream_info()
        self._open_write()

    def close(self):
        self._fid.close()

    def _process(self, buffer, t=None):
        # the default WriterStream doesn't alter the data
        # this is a bit inefficient as it requires a needless copying of data
        # but in the general usage, the data will be altered
        self._processed_buffer = buffer

    def process_buffer(self, buffer, t=None):
        # In derived classes, do not override this method, override _process
        if self._processed_buffer is None:
            self._lgr.debug(f'{self.cfg.name}: creating process buffer of {buffer.dtype}')
            self._processed_buffer = np.zeros(len(buffer), dtype=buffer.dtype)
        self._process(buffer, t)
        self._write_to_file(self._processed_buffer, t)
        return self._processed_buffer, t


class WriterPoints(WriterStream):
    def __init__(self, cfg: WriterPointsConfig):
        super().__init__(cfg)
        self._lgr = logging.getLogger(__name__)

    @classmethod
    def get_config_type(cls):
        return WriterPointsConfig

    def get_reader(self):
        return ReaderPoints(self.fqpn, self.cfg)

    def _write_to_file(self, data_buf, t=None):
        ts_bytes = struct.pack('i', int(t * 1000.0))
        # self._lgr.debug(f'{self.cfg.name}: writing to file {t}')
        self._fid.write(ts_bytes)
        data_buf.tofile(self._fid)
