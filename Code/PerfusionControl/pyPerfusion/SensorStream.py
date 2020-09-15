import mmap
import pathlib
import datetime
from threading import Thread, Event
import numpy as np

from pyPerfusion.SensorAcq import SensorAcq
from pyPerfusion.HWAcq import HWAcq

DATA_VERSION = 1


class SensorStream(Thread):
    def __init__(self, name, unit_str, hw):
        Thread.__init__(self)
        self.__unit_str = unit_str
        self.__hw = hw
        self.__evt_halt = Event()
        self.__fid = None
        self.data = None
        self.__name = name
        self._project_path = pathlib.Path.cwd()
        self._filename = pathlib.Path(f'{self.__name}.dat')
        self._study_path = None
        self.__timestamp = None
        self.__end_of_header = 0
        self.__last_idx = 0
        self.__mmap_len = 100

        self.data = np.array(100, dtype=np.float32)
    def run(self):
        while not self.__evt_halt.wait(self.__hw.period_sampling_ms / 1000.0):
            data_buf = self.__hw.get_data()
            if data_buf is not None:
                buf_len = len(data_buf)
                self.__fid.write(data_buf.tobytes())
                self.__last_idx += buf_len

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
        print(f'Data Format: float32', file=self.__fid)
        print(f'Start of Acquisition: {stamp_str}', file=self.__fid)
        self.__end_of_header = self.__fid.tell()
        self.__fid.close()
        self.__fid = open(full_path, 'rb+')
        self.__fid.seek(0, 2)  # seek to end of file

    def get_data(self, last_ms, samples_needed):
        from_start = datetime.datetime.now() - self.__timestamp
        delta = from_start.total_seconds()
        total_samples = delta / self._sample_period

        return self.data[-total_samples::total_samples/samples_needed]


