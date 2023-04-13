# -*- coding: utf-8 -*-
""" Strategy for reading/writing data to a file

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
import pathlib
import logging
import struct
from os import SEEK_CUR, SEEK_END, SEEK_SET
from dataclasses import dataclass, asdict
from datetime import datetime

import numpy as np

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils


if TYPE_CHECKING:
    from pyPerfusion.Sensor import Sensor


@dataclass
class WriterConfig:
    algorithm: str = "WriterStream"


@dataclass
class WriterPointsConfig:
    algorithm: str = "WriterPoints"
    bytes_per_timestamp: int = 4
    samples_per_timestamp: int = 1


class Reader:
    def __init__(self, fqpn: pathlib.Path, cfg: WriterConfig, sensor: Sensor):
        self.name = 'Reader'
        self._lgr = utils.get_object_logger(__name__, self.name)
        self._version = 1
        self.fqpn = fqpn
        self.cfg = cfg
        self.sensor = sensor
        self._last_idx = 0
        self._read_last_idx = 0

    @property
    def data_dtype(self):
        return self.sensor.hw.data_dtype

    def _open_read(self):
        fid = open(self.fqpn, 'rb')
        return fid

    def _open_mmap(self):
        fid = self._open_read()
        try:
            data = np.memmap(fid, dtype=self.data_dtype, mode='r')
        except ValueError as e:
            # cannot mmap an empty file
            # this can happen if attempting to read a file before the first data was written
            # ignore the error and continue processing
            data = None
        return fid, data

    def get_file_size_in_bytes(self, fid):
        cur_pos = fid.tell()
        fid.seek(0, SEEK_END)
        file_size = int(fid.tell())
        fid.seek(cur_pos, SEEK_SET)
        return file_size

    def retrieve_buffer(self, last_ms, samples_needed):
        if self.sensor.hw is None:
            return [], []
        period = self.sensor.hw.sampling_period_ms
        fid, data = self._open_mmap()

        if data is None:
            return [], []

        file_size_in_samples = int(self.get_file_size_in_bytes(fid) / self.data_dtype.itemsize)
        if last_ms == 0:
            # if last x samples requested, no timestamps are returned
            data = data[-samples_needed:]
            start_idx = file_size_in_samples - len(data)
        else:
            if last_ms > 0:
                data_size = int(last_ms / period)
                if samples_needed > data_size:
                    samples_needed = data_size
                start_idx = file_size_in_samples - data_size
                if start_idx < 0:
                    start_idx = 0
            else:
                start_idx = 0
            samples_needed = min(file_size_in_samples, samples_needed)
            idx = np.linspace(start_idx, file_size_in_samples - 1, samples_needed, dtype=np.uint64)
            data = data[idx]

        start_t = start_idx * period / 1000.0
        stop_t = file_size_in_samples * period / 1000.0
        data_time = np.linspace(start_t, stop_t, samples_needed, dtype=np.uint64)

        fid.close()
        return data_time, data

    def get_data_from_last_read(self, samples: int):
        period = self.sensor.hw.sampling_period_ms
        fid, data = self._open_mmap()
        if self._read_last_idx + samples > self.get_file_size_in_bytes(fid):
            return None, None
        data = data[self._read_last_idx:self._read_last_idx + samples]
        end_idx = self._read_last_idx + len(data) - 1
        data_time = np.linspace(self._read_last_idx * period, end_idx * period,
                                samples, dtype=np.uint64)
        self._read_last_idx = end_idx
        fid.close()
        return data_time, data


class ReaderPoints(Reader):
    def __init__(self, fqpn: pathlib.Path, cfg: WriterPointsConfig, sensor: Sensor):
        self.name = "ReaderPoints"
        self._lgr = utils.get_object_logger(__name__, self.name)
        super().__init__(fqpn, cfg, sensor)
        self._version = 1
        self.fqpn = fqpn
        self.cfg = cfg
        self._last_idx = 0

    @property
    def bytes_per_chunk(self):
        bytes_per_chunk = self.cfg.bytes_per_timestamp + (
                self.cfg.samples_per_timestamp * self.data_dtype.itemsize)
        return bytes_per_chunk

    def read_chunk(self, fid):

        chunk = fid.read(self.cfg.bytes_per_timestamp)
        # self._lgr.debug(f'bpt={self.cfg.bytes_per_timestamp}')
        # self._lgr.debug(f'chunk={chunk}')
        if chunk:
            ts, = struct.unpack('!Q', chunk)
            data_chunk = np.fromfile(fid, dtype=self.data_dtype, count=self.cfg.samples_per_timestamp)
        else:
            ts = None
            data_chunk = None
        return ts, data_chunk

    def retrieve_buffer(self, last_ms, samples_needed, index: int = None):
        data_time = []
        data = []

        fid = open(self.fqpn, 'rb')
        fid.seek(0)
        cur_time = utils.get_epoch_ms()
        while True:
            chunk = fid.read(self.cfg.bytes_per_timestamp)
            if chunk and (len(chunk) == self.cfg.bytes_per_timestamp):
                ts, = struct.unpack('!Q', chunk)
                diff_t = cur_time - ts
                if diff_t <= last_ms:
                    data_chunk = np.fromfile(fid, dtype=self.data_dtype,
                                             count=self.cfg.samples_per_timestamp)
                    if index is None:
                        data.append(data_chunk)
                    else:
                        data.append(data_chunk[index])
                    data_time.append((ts - self.sensor.hw.get_acq_start_ms()) / 1000.0)
                else:
                    fid.seek(self.bytes_per_chunk-self.cfg.bytes_per_timestamp, SEEK_CUR)

            else:
                break

        inc = int(len(data) / samples_needed)
        if inc > 0:
            data = data[0:-1:inc]
            data_time = data_time[0:-1:inc]
        fid.close()
        return data_time, data

    def get_data_from_last_read(self, chunks_needed: int, index: int = None):
        fid = self._open_read()
        file_size = self.get_file_size_in_bytes(fid)

        if not fid or file_size == 0:
            return None, None

        fid.seek(self._last_idx, SEEK_SET)
        # do not assume a full chunk has been written to the file
        total_chunks = file_size // self.bytes_per_chunk
        timestamps = []
        chunks = []
        if chunks_needed < total_chunks:
            total_chunks = chunks_needed
        for chunk_idx in range(total_chunks):
            ts, chunk = self.read_chunk(fid)
            if chunk is not None:
                if index is not None and index < len(chunk):
                    chunk = chunk[index]
                timestamps.append((ts - self.sensor.hw.get_acq_start_ms()) / 1000.0)
                chunks.append(chunk)

        self._last_idx = fid.tell()

        return timestamps, chunks

    def get_last_acq(self, index: int = None):
        fid = self._open_read()
        file_size = self.get_file_size_in_bytes(fid)
        if not fid or file_size == 0:
            return None, None

        # do not assume a full chunk has been written to the file
        start_of_last_chunk = ((file_size // self.bytes_per_chunk) - 1) * self.bytes_per_chunk
        if start_of_last_chunk < 0:
            return None, None
        fid.seek(start_of_last_chunk)
        ts, data_chunk = self.read_chunk(fid)
        if index is not None and index < len(data_chunk):
            data_chunk = data_chunk[index]
        fid.close()
        ts = (ts - self.sensor.hw.get_acq_start_ms()) / 1000.0
        return ts, data_chunk


class WriterStream:
    def __init__(self, name: str):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.cfg = WriterConfig
        self._ext = '.dat'
        self._ext_hdr = '.txt'
        self._last_idx = 0
        self._fid = None
        self._base_path = pathlib.Path.cwd()
        self._filename = pathlib.Path(f'{self.name}')
        self.cfg.version = 1
        self._acq_start_ms = 0
        self.sensor = None
        self.data_dtype = np.dtype(np.float64)

        self._processed_buffer = None


    @classmethod
    def get_config_type(cls):
        return WriterConfig

    @property
    def fqpn(self):
        return self._base_path / self._filename.with_suffix(self._ext)

    def get_reader(self):
        return Reader(self.fqpn, self.cfg, self.sensor)

    def _open_write(self):
        self._lgr.info(f'opening for write: {self.fqpn}')
        self._fid = open(self.fqpn, 'w+b')

    def _write_to_file(self, data_buf, t=None):
        # self._lgr.debug(f'_write_to_file is being called and data_buf = {data_buf}')
        if self._fid:
            try:
                data_buf.tofile(self._fid)
            except OSError as e:
                self._lgr.error(f'{self.name}: {e}')
            self._fid.flush()
            self._last_idx += len(data_buf)

    def _get_stream_info(self):
        # all_params = {**self._params, **self._sensor_params}
        all_params = asdict(self.cfg)
        all_params['Data Type'] = str(self.data_dtype)
        hdr_str = [f'{k}: {v}\n' for k, v in all_params.items()]
        return ''.join(hdr_str)

    def _print_stream_info(self):
        hdr_str = self._get_stream_info()
        # print header info in a separate txt file to simply
        # reads using memory-mapped files
        fid = open(self.fqpn.with_suffix('').with_suffix('.txt'), 'wt')
        fid.write(hdr_str)
        if self.sensor.hw is not None:
            timestamp = datetime.utcfromtimestamp(self.sensor.hw.get_acq_start_ms() / 1_000)
            fid.write(f'Start of Acquisition: {timestamp}')
        else:
            self._lgr.error(f'Hardware has not been attached')
        fid.close()

    def open(self, sensor: Sensor = None):
        self._base_path = PerfusionConfig.get_date_folder()
        self._filename = pathlib.Path(f'{sensor.name}_{self.name}')
        self.sensor = sensor
        self.data_dtype = sensor.hw.data_dtype

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
            self._processed_buffer = np.zeros(len(buffer), dtype=buffer.dtype)
        self._process(buffer, t)
        self._write_to_file(self._processed_buffer, t)
        return self._processed_buffer, t


class WriterPoints(WriterStream):
    def __init__(self, name: str):
        super().__init__(name)
        self._lgr = utils.get_object_logger(__name__, self.name)

    @classmethod
    def get_config_type(cls):
        return WriterPointsConfig

    def get_reader(self):
        return ReaderPoints(self.fqpn, self.cfg, self.sensor)

    def _write_to_file(self, data_buf, t=None):
        ts_bytes = struct.pack('!Q', t)
        self._fid.write(ts_bytes)
        data_buf.tofile(self._fid)
