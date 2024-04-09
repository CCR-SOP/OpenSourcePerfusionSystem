# -*- coding: utf-8 -*-
""" Strategy for reading/writing data to a file

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import pathlib
import struct
import os
from os import SEEK_CUR, SEEK_END, SEEK_SET
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

import numpy as np

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils


# raw Writer does not have any parameters, but create a config class
# for consistency
@dataclass
class WriterConfig:
    pass


@dataclass
class WriterPointsConfig:
    bytes_per_timestamp: int = 4
    samples_per_timestamp: int = 1


@dataclass
class ReaderStreamSensor:
    data_dtype: np.dtype = np.dtype('float64')
    acq_start_ms: int = 0
    sampling_period_ms: int = 0

    def get_acq_start_ms(self):
        return self.acq_start_ms


@dataclass
class ReaderPointsSensor:
    data_dtype: np.dtype = np.dtype('float64')
    acq_start_ms: int = 0

    def get_acq_start_ms(self):
        return self.acq_start_ms


def read_file(filename):

    if 'points' in str(filename).lower():
        sensor = ReaderPointsSensor()
        reader = ReaderPoints('Reader', filename, WriterPointsConfig(), sensor)
    else:
        sensor = ReaderStreamSensor()
        reader = Reader('Reader', filename, WriterConfig(), sensor)

    reader.read_settings()

    return reader


def convert_to_csv(reader):
    logging.getLogger().debug('getting all data')
    ts, data = reader.get_all()
    logging.getLogger().debug('done')
    array_data = True
    if type(reader) == Reader:
        array_data = False
        start_ts = reader.sensor.get_acq_start_ms()
    else:
        data = data.reshape(-1, reader.sensor.samples_per_timestamp)
        start_ts = 0
    csv = ''
    logging.getLogger().debug('converting all data')
    for t, d in zip(ts, data):
        if array_data:
            data_str = ','.join(map(str, d))
        # else:
        #     data_str = f'{d}'

        csv += f'{datetime.fromtimestamp((start_ts) / 1000.0)}, {data_str}\n'

    return csv


def get_standard_filename(date_str, sensor_name, output_type):
    base_folder = PerfusionConfig.ACTIVE_CONFIG.basepath / \
                  PerfusionConfig.ACTIVE_CONFIG.get_data_folder(date_str)

    fqpn = base_folder / f'{sensor_name}_{output_type}.dat'
    return fqpn


def save_to_csv(filename):
    reader = read_file(filename)

    ts, data = reader.get_all()

    array_data = True
    if type(reader) == Reader:
        array_data = False
        start_ts = reader.sensor.get_acq_start_ms()
    else:
        data = data.reshape(-1, reader.sensor.samples_per_timestamp)
        start_ts = 0

    with open(reader.fqpn.with_suffix('.csv'), 'wt') as csv_file:
        for t, d in zip(ts, data):
            if array_data:
                data_str = ','.join(map(str, d))
            else:
                data_str = f'{d}'
            csv = f'{datetime.fromtimestamp(start_ts + t/ 1000.0)}, {data_str}\n'
            csv_file.write(csv)


class Reader:
    def __init__(self, name: str, fqpn: pathlib.Path, cfg: WriterConfig, sensor):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)
        self._version = 1
        self.fqpn = fqpn
        self.cfg = cfg
        self.sensor = sensor
        self._last_idx = 0
        self._read_last_idx = 0

    @property
    def data_dtype(self):
        return self.sensor.data_dtype

    def read_settings(self):
        settings_file = self.fqpn.with_suffix('.txt')
        with open(settings_file) as reader:
            for line in reader:
                key, value = line.strip().split(': ')
                if key == 'Data Type':
                    self.sensor.data_dtype = np.dtype(value)
                elif key == 'Start of Acquisition':
                    if value == '1970-01-01 00:00:00':
                        # some dat files did not record correct date and is missing milliseconds
                        # update date and assume start at midnight to force conversion
                        value = f'{pathlib.PurePath(self.fqpn).parent.name} 00:00:00.00'
                    start_ts = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
                    self.sensor.acq_start_ms = start_ts.timestamp() * 1000
                elif key == 'Sampling Period (ms)':
                    self.sensor.sampling_period_ms = int(value)
        # error in some dat files did not include sampling period
        if self.sensor.sampling_period_ms == 0:
            self.sensor.sampling_period_ms = 100

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
        period = self.sensor.sampling_period_ms
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
            idx = np.linspace(start_idx, len(data) - 1, samples_needed, dtype=np.uint64)
            try:
                data = data[idx]
            except IndexError :
                self._lgr.exception(f'filesize = {file_size_in_samples},'
                                    f'len(data) = {len(data)},'
                                    f'samples_needed = {samples_needed}')
                return None, None

        data_time = np.linspace(start_idx * period, file_size_in_samples * period,
                                samples_needed, dtype=np.uint64)

        fid.close()
        return data_time, data

    def get_data_from_last_read(self, samples: int):
        period = self.sensor.sampling_period_ms
        fid, data = self._open_mmap()
        if self._read_last_idx + samples > self.get_file_size_in_bytes(fid):
            return None, None
        data = data[self._read_last_idx:self._read_last_idx + samples]
        end_idx = self._read_last_idx + len(data) - 1
        data_time = np.linspace(self._read_last_idx * period, end_idx * period,
                                samples, dtype=np.uint64)
        self._read_last_idx = end_idx + 1
        fid.close()
        return data_time, data

    def get_last_acq(self):
        fid, data = self._open_mmap()
        file_size_in_samples = int(self.get_file_size_in_bytes(fid) / self.data_dtype.itemsize)
        data = data[-1]
        data_time = file_size_in_samples * self.sensor.sampling_period_ms
        fid.close()
        return data_time, data

    def get_all(self):
        self._lgr.debug('in get_all')
        period = self.sensor.sampling_period_ms
        self._lgr.debug('opening mmap')
        fid, data = self._open_mmap()

        if data is None:
            return [], []

        file_size_in_samples = int(self.get_file_size_in_bytes(fid) / self.data_dtype.itemsize)
        self._lgr.debug(f'filesize is {file_size_in_samples}')
        data_time = np.linspace(0, file_size_in_samples * period,
                                num=file_size_in_samples, dtype=np.uint64)
        self._lgr.debug('created linspace')
        fid.close()
        return data_time, data


class ReaderPoints(Reader):
    def __init__(self, name: str, fqpn: pathlib.Path, cfg: WriterPointsConfig, sensor: ReaderPointsSensor):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)
        super().__init__(name, fqpn, cfg, sensor)
        self._version = 1
        self.fqpn = fqpn
        self.cfg = cfg
        self._last_idx = 0

    @property
    def bytes_per_chunk(self):
        bytes_per_chunk = self.cfg.bytes_per_timestamp + (
                self.cfg.samples_per_timestamp * self.data_dtype.itemsize)
        return bytes_per_chunk

    def read_settings(self):
        settings_file = self.fqpn.with_suffix('.txt')
        with open(settings_file) as reader:
            for line in reader:
                key, value = line.strip().split(': ')
                if key == 'Data Type':
                    self.sensor.data_dtype = np.dtype(value)
                elif key == 'Start of Acquisition':
                    if value.startswith('1970-01-01 00:00:00'):
                        # some dat files did not record correct date and is missing milliseconds
                        # update date and assume start at midnight to force conversion
                        value = f'{pathlib.PurePath(self.fqpn).parent.name} 00:00:00.00'
                    start_ts = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
                    self.sensor.acq_start_ms = start_ts.timestamp() * 1000
                elif key == 'samples_per_timestamp':
                    self.sensor.samples_per_timestamp = int(value)
                    self.cfg.samples_per_timestamp = int(value)
                elif key == 'bytes_per_timestamp':
                    self.sensor.bytes_per_timestamp = int(value)
                    self.cfg.bytes_per_timestamp = int(value)

    def read_chunk(self, fid):
        dtype = np.dtype({'names': ('time', 'data'), 'formats': (np.uint64, np.float64)})
        data = np.fromfile(fid, dtype=dtype)
        ts = data['time']
        data_chunk = data['data']
        # chunk = fid.read(self.cfg.bytes_per_timestamp)
        # if chunk:
            # ts, = struct.unpack('!Q', chunk)
            #data_chunk = np.fromfile(fid, dtype=self.data_dtype, count=self.cfg.samples_per_timestamp)
        # else:
        #     ts = None
        #     data_chunk = None
        return ts, data_chunk

    def retrieve_buffer(self, last_ms, samples_needed, index: int = None):
        data_time = np.zeros(0, dtype=self.data_dtype)
        data = np.zeros(0, dtype=self.data_dtype)

        fid = open(self.fqpn, 'rb')
        fid.seek(0)
        cur_time = utils.get_epoch_ms()
        chunks_read = 0
        while True:
            chunk = fid.read(self.cfg.bytes_per_timestamp)
            if chunk and (len(chunk) == self.cfg.bytes_per_timestamp):
                chunks_read += 1
                ts, = struct.unpack('!Q', chunk)
                diff_t = cur_time - ts
                if diff_t <= last_ms:
                    data_chunk = np.fromfile(fid, dtype=self.data_dtype,
                                             count=self.cfg.samples_per_timestamp)
                    if index is None:
                        data = np.append(data, data_chunk)
                    else:
                        data = np.append(data, data_chunk[index])
                    data_time = np.append(data_time, ts - self.sensor.get_acq_start_ms())
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
                timestamps.append((ts - self.sensor.get_acq_start_ms()) / 1000.0)
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
        return ts, data_chunk

    def get_all(self, index: int = None):
        fid = self._open_read()
        file_size = self.get_file_size_in_bytes(fid)

        total_chunks = file_size/self.bytes_per_chunk
        fid.seek(0)

        dtype = np.dtype({'names': ('time', 'data'), 'formats': (np.uint64, np.float64)})
        all_data = np.fromfile(fid, dtype=dtype)
        data_time = [struct.unpack('!Q', chunk)[0] for chunk in all_data['time']]
        data = all_data['data']
        fid.close()
        return data_time, data


class WriterStream:
    def __init__(self, name: str):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.cfg = WriterConfig()
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
        self._wrote_header = False


    @classmethod
    def get_config_type(cls):
        return WriterConfig

    @property
    def fqpn(self):
        return self._base_path / self._filename.with_suffix(self._ext)

    def get_reader(self):
        return Reader(self.name, self.fqpn, self.cfg, self.sensor)

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
        all_params = {}
        all_params['Sensor Name'] = self.sensor.name
        all_params['Output Type'] = self.name
        all_params['Data Type'] = str(self.data_dtype)
        all_params['Sampling Period (ms)'] = str(self.sensor.sampling_period_ms)
        all_params.update(asdict(self.cfg))
        hdr_str = [f'{k}: {v}\n' for k, v in all_params.items()]
        return ''.join(hdr_str)

    def _print_stream_info(self):
        hdr_str = self._get_stream_info()
        # print header info in a separate txt file to simply
        # reads using memory-mapped files
        fid = open(self.fqpn.with_suffix('').with_suffix('.txt'), 'wt')
        fid.write(hdr_str)
        timestamp = datetime.utcfromtimestamp(self.sensor.get_acq_start_ms() / 1_000)
        fid.write(f'Start of Acquisition: {timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")}')

        fid.close()

    def open(self, sensor = None):
        self._base_path = PerfusionConfig.get_date_folder()
        self._filename = pathlib.Path(f'{sensor.name}_{self.name}')
        self.sensor = sensor

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
        self.cfg = WriterPointsConfig()

    @classmethod
    def get_config_type(cls):
        return WriterPointsConfig

    def _get_stream_info(self):
        all_params = {}
        all_params['Sensor Name'] = self.sensor.name
        all_params['Output Type'] = self.name
        all_params['Data Type'] = str(self.data_dtype)
        all_params.update(asdict(self.cfg))

        hdr_str = [f'{k}: {v}\n' for k, v in all_params.items()]
        return ''.join(hdr_str)

    def get_reader(self):
        return ReaderPoints(self.name, self.fqpn, self.cfg, self.sensor)

    def _write_to_file(self, data_buf, t=None):
        ts_bytes = struct.pack('!Q', t)
        self._fid.write(ts_bytes)
        data_buf.tofile(self._fid)
