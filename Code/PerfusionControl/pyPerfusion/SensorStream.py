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
        self.__unit_str = unit_str
        self.__hw = hw
        self.__evt_halt = Event()
        self.__fid = None
        self.__fid_read = None
        self.data = None
        self.__name = name
        self._project_path = pathlib.Path.cwd()
        self._filename = pathlib.Path(f'{self.__name}.dat')
        self._study_path = None
        self.__timestamp = None
        self.__end_of_header = 0
        self.__last_idx = 0
        self.__mmap_len = 100
        self.data = np.array(100, dtype=self.__hw.datatype)

    def run(self):
        while not self.__evt_halt.wait(self.__hw.period_sampling_ms / 1000.0):
            data_buf = self.__hw.get_data()
            if data_buf is not None and self.__fid is not None:
                buf_len = len(data_buf)
                data_buf.tofile(self.__fid)
                self.__last_idx += buf_len
                self.__fid.flush()

    def start(self):
        super().start()
        self.__hw.start()

    def open(self, project_path, study_path):
        if not isinstance(project_path, pathlib.Path):
            project_path = pathlib.Path(project_path)
        if not isinstance(study_path, pathlib.Path):
            project_path = pathlib.Path(study_path)
        self._project_path = project_path
        self._study_path = study_path
        self._project_path.mkdir(parents=True, exist_ok=True)
        self._study_path.mkdir(parents=True, exist_ok=True)
        self.__timestamp = datetime.datetime.now()
        self.print_header()

    def stop(self):
        self.__hw.halt()
        self.__evt_halt.set()
        # JWK, probably need a join here to ensure data collection stops before file closed
        # self.data.close()
        # self.__fid.close()
        self.__fid = None

    def print_header(self):
        if self.__fid:
            self.__fid.close()
            self.__fid = None
        full_path = self._project_path / self._study_path / self._filename
        self.__fid = open(full_path, 'wt')
        stamp_str = self.__timestamp.strftime('%Y-%m-%d_%H:%M')

        print(f'Data Format: {DATA_VERSION}', file=self.__fid)
        print(f'Sensor: {self.__name}', file=self.__fid)
        print(f'Unit: {self.__unit_str}', file=self.__fid)
        print(f'Data Format: {str(np.dtype(self.__hw.datatype))}', file=self.__fid)
        print(f'Start of Acquisition: {stamp_str}', file=self.__fid)
        self.__end_of_header = self.__fid.tell()

        self.__fid.flush()
        self.__fid_read = open(full_path, 'rb')
        self.__fid_read.seek(self.__end_of_header)

    def get_data(self, last_ms, samples_needed):

        if last_ms == 0:
            self.__fid_read.seek(self.__end_of_header)
            total_samples = -1
        else:
            total_samples = int(last_ms / self.__hw.period_sampling_ms)
            bytes_to_read = total_samples * np.dtype(self.__hw.datatype).itemsize
            try:
                if self.__fid_read.tell() <= bytes_to_read:
                    self.__fid_read.seek(self.__end_of_header)
                else:
                    self.__fid_read.seek(-bytes_to_read, 2)
            except OSError:
                # probably occurred by reading past beginning of file
                print("Error seeking file")
                self.__fid_read.seek(self.__end_of_header)
        data = np.fromfile(self.__fid_read, dtype=self.__hw.datatype, count=total_samples)
        idx = np.linspace(0, len(data) - 1, samples_needed, dtype='int')
        time_start = (self.__last_idx - len(data)) * self.__hw.period_sampling_ms/1000.0 + self.__hw.start_time
        data_time = (idx * self.__hw.period_sampling_ms/1000.0) + time_start
        try:
            data = data[idx]
        except IndexError:
            data = None
        return data_time, data
