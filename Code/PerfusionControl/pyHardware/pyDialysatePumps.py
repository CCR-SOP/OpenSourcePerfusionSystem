import logging
import pathlib
import datetime
from time import perf_counter
import numpy as np
import struct

DATA_VERSION = 7

class DialysatePumps:

    """
    Class for logging data from automation of inflow or outflow dialysate pumps
    ...

    Methods
    -------
    open_stream(full_path)
        creates .txt and .dat files for recording data
    record()
        records changes to inflow and/or outflow rates in .dat file
    stop_stream()
        stops recording of data
    close_stream()
        closes file
    """

    def __init__(self, name):
        self._logger = logging.getLogger(__name__)
        self.name = name
        self._fid_write = None
        self._full_path = pathlib.Path.cwd()
        self._filename = pathlib.Path(f'{self.name}')
        self._ext = '.dat'
        self._timestamp = None
        self._timestamp_perf = None
        self._end_of_header = 0
        self._last_idx = 0
        self._datapoints_per_ts = 3
        self._bytes_per_ts = 4

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
        self._write_to_file(np.array([0]), np.array([0]), np.array([0]), np.array([0]))
        self._fid_write.seek(0)

        self.print_stream_info()

    def _open_write(self):
        self._logger.debug(f'opening {self.full_path}')
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
                  f'Data Source: {self.name}',
                  f'Data Format: {str(np.dtype(np.float32))}',
                  f'Datapoints per Timestamp: {self._datapoints_per_ts} (Dialysate inflow rate (ml/min), dialysate outflow rate (ml/min), and working status (0 for off, 1 for on))',
                  f'Bytes Per Timestamp: {self._bytes_per_ts}',
                  f'Start of Acquisition: {stamp_str, self._timestamp_perf}'
                  ]
        end_of_line = '\n'
        hdr_str = f'{end_of_line.join(header)}{end_of_line}'
        return hdr_str

    def start_stream(self):
        pass

    def record(self, inflow_rate, outflow_rate, working_status):
        inflow_rate_buffer = np.ones(1, dtype=np.float32) * np.float32(inflow_rate)
        outflow_rate_buffer = np.ones(1, dtype=np.float32) * np.float32(outflow_rate)
        working_status_buffer = np.ones(1, dtype=np.float32) * np.float32(working_status)
        t = perf_counter()
        buf_len = len(inflow_rate_buffer) + len(outflow_rate_buffer) + len(working_status_buffer)
        self._write_to_file(inflow_rate_buffer, outflow_rate_buffer, working_status_buffer, t)
        self._last_idx += buf_len
        self._fid_write.flush()

    def _write_to_file(self, inflow_rate_buffer, outflow_rate_buffer, working_status_buffer, t):
        ts_bytes = struct.pack('i', int(t * 1000.0))
        self._fid_write.write(ts_bytes)
        inflow_rate_buffer.tofile(self._fid_write)
        outflow_rate_buffer.tofile(self._fid_write)
        working_status_buffer.tofile(self._fid_write)

    def stop_stream(self):
        pass

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
                data_time.append(ts)
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
