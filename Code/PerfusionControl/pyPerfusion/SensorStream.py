import pathlib
import datetime
from threading import Thread, Event
from os import SEEK_END
import time

import numpy as np

DATA_VERSION = 1


class SensorStream(Thread):
    def __init__(self, name, unit_str, hw):
        Thread.__init__(self)
        self._unit_str = unit_str
        self._hw = hw
        self.__evt_halt = Event()
        self._fid = None
        self._fid_read = None
        self.data = None
        self._name = name
        self._project_path = pathlib.Path.cwd()
        self._filename = pathlib.Path(f'{self._name}.dat')
        self._study_path = None
        self._timestamp = None
        self.__end_of_header = 0
        self._last_idx = 0
        self.data = np.array(self._hw.buf_len, dtype=self._hw.data_type)

    @property
    def buf_len(self):
        return self._hw.buf_len

    def run(self):
        while not self.__evt_halt.wait(self._hw.period_sampling_ms / 1000.0):
            data_buf, t = self._hw.get_data()
            if data_buf is not None and self._fid is not None:
                buf_len = len(data_buf)
                self._write_to_file(data_buf, t)
                self._last_idx += buf_len
                self._fid.flush()

    def _write_to_file(self, data_buf, t):
        data_buf.tofile(self._fid)

    def start(self):
        super().start()
        self._hw.start()

    def open(self, project_path, study_path):
        if not isinstance(project_path, pathlib.Path):
            project_path = pathlib.Path(project_path)
        if not isinstance(study_path, pathlib.Path):
            project_path = pathlib.Path(study_path)
        self._project_path = project_path
        self._study_path = study_path
        self._project_path.mkdir(parents=True, exist_ok=True)
        tmp_path = self._project_path / self._study_path
        tmp_path.mkdir(parents=True, exist_ok=True)
        self._timestamp = datetime.datetime.now()
        if self._fid:
            self._fid.close()
            self._fid = None
        full_path = self._project_path / self._study_path / self._filename
        self._fid = open(full_path, 'wb')

        self.print_header()
        self._fid.flush()
        # self._fid.close()
        # reopen as binary for data
        # self._fid.open(full_path, 'wb')
        # self._fid.seek(0, SEEK_END)
        self.__end_of_header = self._fid.tell()
        self._fid.flush()
        self._fid_read = open(full_path, 'rb')
        self._fid_read.seek(self.__end_of_header)

    def stop(self):
        self._hw.halt()
        self.__evt_halt.set()
        # JWK, probably need a join here to ensure data collection stops before file closed
        # self.data.close()
        # self.__fid.close()
        self._fid = None

    def print_header(self):
        stamp_str = self._timestamp.strftime('%Y-%m-%d_%H:%M')
        header = [f'File Format: {DATA_VERSION}',
                  f'Sensor: {self._name}',
                  f'Unit: {self._unit_str}',
                  f'Data Format: {str(np.dtype(self._hw.data_type))}',
                  f'Sampling Period (ms): {self._hw.period_sampling_ms}',
                  f'Start of Acquisition: {stamp_str}'
                  ]
        end_of_line = '\n'
        hdr_str = f'{end_of_line.join(header)}{end_of_line}'
        self._fid.write(hdr_str.encode())

    def get_data(self, last_ms, samples_needed):
        if last_ms == 0:
            self._fid_read.seek(self.__end_of_header)
            total_samples = -1
        else:
            total_samples = int(last_ms / self._hw.period_sampling_ms)
            bytes_to_read = total_samples * np.dtype(self._hw.data_type).itemsize
            try:
                if self._fid_read.tell() <= bytes_to_read:
                    self._fid_read.seek(self.__end_of_header)
                else:
                    self._fid_read.seek(-bytes_to_read, 2)
            except OSError:
                # probably occurred by reading past beginning of file
                print("Error seeking file")
                self._fid_read.seek(self.__end_of_header)
            except AttributeError:
                # read fid not valid
                print("ERROR: Read FID is not valid")
        data = np.fromfile(self._fid_read, dtype=self._hw.data_type, count=total_samples)
        idx = np.linspace(0, len(data) - 1, samples_needed, dtype='int')
        time_start = (self._last_idx - len(data)) * self._hw.period_sampling_ms / 1000.0 + self._hw.start_time
        data_time = (idx * self._hw.period_sampling_ms / 1000.0) + time_start
        try:
            data = data[idx]
        except IndexError:
            data = None
        return data_time, data
