import pathlib
import datetime
from threading import Thread, Event
from os import SEEK_END
import time

import numpy as np

DATA_VERSION = 1


class SensorStream:
    def __init__(self, name, unit_str, hw, valid_range=None):
        self.__thread = None
        self._unit_str = unit_str
        self._valid_range = valid_range
        self.hw = hw
        self._ch_id = None
        self.__evt_halt = Event()
        self._fid_write = None
        self.data = None
        self.name = name
        self._full_path = pathlib.Path.cwd()
        self._filename = pathlib.Path(f'{self.name}')
        self._ext = '.dat'
        self._timestamp = None
        self._end_of_header = 0
        self._last_idx = 0
        self.data = np.array(self.hw.buf_len, dtype=self.hw.data_type)

    @property
    def buf_len(self):
        return self.hw.buf_len

    @property
    def full_path(self):
        return self._full_path / self._filename.with_suffix(self._ext)

    @property
    def unit_str(self):
        return self._unit_str

    @property
    def valid_range(self):
        return self._valid_range

    def run(self):
        # JWK, need better wait timeout
        while not self.__evt_halt.wait(self.hw.period_sampling_ms / 1000.0 / 10.0):
            data_buf, t = self.hw.get_data(self._ch_id)
            if data_buf is not None and self._fid_write is not None:
                buf_len = len(data_buf)
                self._write_to_file(data_buf, t)
                self._last_idx += buf_len
                self._fid_write.flush()

    def _write_to_file(self, data_buf, t):
        data_buf.tofile(self._fid_write)

    def _open_read(self):
        _fid = open(self.full_path, 'rb')
        data = np.memmap(_fid, dtype=self.hw.data_type, mode='r')
        return _fid, data

    def _open_write(self):
        print(f'opening {self.full_path}')
        self._fid_write = open(self.full_path, 'w+b')

    def start(self):
        if self.__thread:
            self.__thread.start()

    def open(self, ch_id, full_path):
        self._ch_id = ch_id
        if not isinstance(full_path, pathlib.Path):
            full_path = pathlib.Path(full_path)
        self._full_path = full_path
        if not self._full_path.exists():
            self._full_path.mkdir(parents=True, exist_ok=True)
        self._timestamp = datetime.datetime.now()
        if self._fid_write:
            self._fid_write.close()
            self._fid_write = None

        # write file handle should be opened first as the memory mapped read handle needs
        # a file with data in it
        self._open_write()
        self._write_to_file(np.array([0]), np.array([0]))
        # reset file point to start to overwrite the dummy value with valid data when it arrives
        self._fid_write.seek(0)
        # self._open_read()

        self.print_stream_info()
        self.__thread = Thread(target=self.run)

    def stop(self):
        self.__evt_halt.set()
        if self.__thread:
            self.__thread.join(2.0)
        if self._fid_write:
            self._fid_write.close()
        self._fid_write = None

    def _get_stream_info(self):
        stamp_str = self._timestamp.strftime('%Y-%m-%d_%H:%M')
        header = [f'File Format: {DATA_VERSION}',
                  f'Sensor: {self.name}',
                  f'Unit: {self._unit_str}',
                  f'Data Format: {str(np.dtype(self.hw.data_type))}',
                  f'Sampling Period (ms): {self.hw.period_sampling_ms}',
                  f'Start of Acquisition: {stamp_str}'
                  ]
        end_of_line = '\n'
        hdr_str = f'{end_of_line.join(header)}{end_of_line}'
        return hdr_str

    def print_stream_info(self):
        hdr_str = self._get_stream_info()
        filename = self.full_path.with_suffix('.txt')
        print(f"printing stream info to {filename}")
        fid = open(filename, 'wt')
        fid.write(hdr_str)
        fid.close()

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