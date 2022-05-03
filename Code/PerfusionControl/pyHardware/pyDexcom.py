import pathlib
import datetime
import logging
from time import perf_counter
from threading import Thread, Event
import struct

import numpy as np

DATA_VERSION = 6

class DexcomSensor:

    """
       Class for serial communication with Dexcom Receiver over USB
       ...
       Methods
       -------
       open_stream(full_path)
           creates .txt and .dat files for recording Dexcom Sensor data
       start_stream()
           starts thread for writing streamed data from Dexcom sensor to file
       stop_stream()
           stops recording of data
       close_stream()
           closes file
       get_latest()
           returns latest glucose reading
       """

    def __init__(self, name, unit, receiver):
        self._logger = logging.getLogger(__name__)
        self.name = name
        self.receiver = receiver
        self.unit = unit
        self._fid_write = None
        self._full_path = pathlib.Path.cwd()
        self._filename = pathlib.Path(f'{self.name}')
        self._ext = '.dat'
        self._timestamp = None
        self._timestamp_perf = None
        self._end_of_header = 0
        self._last_idx = 0
        self._datapoints_per_ts = 1
        self._bytes_per_ts = 4

        self.__thread_streaming = None
        self.__evt_halt_streaming = Event()

        self.old_time = None

    @property
    def full_path(self):
        return self._full_path / self._filename.with_suffix(self._ext)

    def open(self):
        pass

    def open_stream(self, full_path):
        if not isinstance(full_path, pathlib.Path):
            full_path = pathlib.Path(full_path)
        self._full_path = full_path
        if not self._full_path.exists():
            self._full_path.mkdir(parents=True, exist_ok=True)
        self._timestamp = datetime.datetime.now()
        self._timestamp_perf = perf_counter() * 1000
        if self._fid_write:
            self._fid_write.close()
            self._fid_write = None

        self._open_write()
        self._write_to_file(np.array([0]), np.array([0]))
        self._fid_write.seek(0)

        self.print_stream_info()

    def _open_write(self):
        self._logger.info(f'opening {self.full_path}')
        self._fid_write = open(self.full_path, 'w+b')

    def print_stream_info(self):
        hdr_str = self._get_stream_info()
        filename = self.full_path.with_suffix('.txt')
        self._logger.debug(f"printing stream info to {filename}")
        fid = open(filename, 'wt')
        fid.write(hdr_str)
        fid.close()

    def _get_stream_info(self):
        stamp_str = self._timestamp.strftime('%Y-%m-%d_%H:%M')
        header = [f'File Format: {DATA_VERSION}',
                  f'Sensor: {self.name}',
                  f'Unit: {self.unit}',
                  f'Data Format: {str(np.dtype(np.float32))}',
                  f'Datapoints Per Timestamp: {self._datapoints_per_ts}',
                  f'Bytes Per Sample: {self._bytes_per_ts}',
                  f'Start of Acquisition: {stamp_str, self._timestamp_perf}'
                  ]
        end_of_line = '\n'
        hdr_str = f'{end_of_line.join(header)}{end_of_line}'
        return hdr_str

    def _write_to_file(self, data_buf, ts_bytes):
        self._fid_write.write(ts_bytes)
        data_buf.tofile(self._fid_write)

    def start_stream(self):
        self.__evt_halt_streaming.clear()
        self.__thread_streaming = Thread(target=self.OnStreaming)
        self.__thread_streaming.start()

    def OnStreaming(self):  ###
        while not self.__evt_halt_streaming.wait(1.5):  # Attempt to read new data every 60 seconds
            self.stream()

    def stream(self):
        data, new_time = self.receiver.get_data()
        if not data or self.old_time == new_time:
            return
        else:
            ts_bytes = struct.pack('i', int(perf_counter() * 1000.0))
            data_buf = np.ones(1, dtype=np.float32) * np.float32(data)
            buf_len = len(data_buf)
            self._write_to_file(data_buf, ts_bytes)
            self._last_idx += buf_len
            self._fid_write.flush()
            self.old_time = new_time

    def stop_stream(self):
        if self.__thread_streaming and self.__thread_streaming.is_alive():
            self.__evt_halt_streaming.set()
            self.__thread_streaming.join(2.0)
            self.__thread_streaming = None

    def close_stream(self):
        if self._fid_write:
            self._fid_write.close()
        self._fid_write = None

    def get_data(self):
        _fid, tmp = self._open_read()
        _fid.seek(0)
        chunk = [1]
        data_time = []
        data = []
        while chunk[0]:
            chunk, ts = self.__read_chunk(_fid)
            if type(chunk) is list:
                break
            elif chunk.any():
                data.append(chunk)
                data_time.append(ts / 1000.0)
        _fid.close()
        return data_time, data

    def _open_read(self):
        _fid = open(self.full_path, 'rb')
        data = np.memmap(_fid, dtype=np.float32, mode='r')
        return _fid, data

    def __read_chunk(self, _fid):
        ts = 0
        data_buf = []
        ts_bytes = _fid.read(self._bytes_per_ts)
        if len(ts_bytes) == 4:
            ts, = struct.unpack('i', ts_bytes)
            data_buf = np.fromfile(_fid, dtype=np.float32, count=self._datapoints_per_ts)
        return data_buf, ts

    def get_latest(self):
        data_time, data = self.get_data()
        time = data_time[-1]
        data = data[-1]
        return time, data
