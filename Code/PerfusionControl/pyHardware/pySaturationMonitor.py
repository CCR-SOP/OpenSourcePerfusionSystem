from pyHardware.pyUSBSerial import USBSerial
import logging
import pathlib
import datetime
from time import perf_counter
import struct
import numpy as np
from threading import Thread, Event

DATA_VERSION = 4

class TSMSerial(USBSerial):

    """
    Class for serial communication over USB using Terumo CDI500 Saturation Monitor (TSM) command set
    ...

    Methods
    -------
    open(port_name, baud, bytesize, parity, stopbits)
        opens USB port of given name with the specified baud rate, bytesize, parity, and stopbits which correspond to the TSM
    open_stream(full_path)
        creates .txt and .dat files for recording CDI data
    start_stream()
        starts thread for writing streamed data from CDI monitor to file
    stop_stream()
        stops thread and recording of data
    """

    def __init__(self, name):
        super().__init__()
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
        self._datapoints_per_ts = 1
        self._bytes_per_ts = 101

        self.__thread_streaming = None
        self.__evt_halt_streaming = Event()

    @property
    def full_path(self):
        return self._full_path / self._filename.with_suffix(self._ext)

    def open(self, port_name, baud, bytesize, parity, stopbits):
        super().open(port_name, baud)
        self._USBSerial__serial.bytesize = bytesize
        self._USBSerial__serial.parity = parity
        self._USBSerial__serial.stopbits = stopbits

    def open_stream(self, full_path):
        if not isinstance(full_path, pathlib.Path):
            full_path = pathlib.Path(full_path)
        self._full_path = full_path
        if not self._full_path.exists():
            self._full_path.mkdir(parents=True, exist_ok=True)
        self._timestamp = datetime.datetime.now()
        self._timestamp_perf = perf_counter()
        if self._fid_write:
            self._fid_write.close()
            self._fid_write = None

        self._open_write()
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
                  f'Instrument: {self.name}',
                  f'Data Format: {str(np.dtype(np.byte))}',
                  f'Datapoints Per Timestamp: {self._datapoints_per_ts} (Every Datapoint contains: Header, Time, Arterial pH, Arterial pCO2 (mmHg), Arterial pO2 (mmHg), Arterial Temperature (Celsius), Arterial HCO3- (mEq/L), Arterial Base Excess (mEq/L), Calculated O2 Sat, K (mmol/L), VO2 (Oxygen Consumption; ml/min), Pump Flow (L/min), BSA (m^2), Venous pH, Venous pCO2 (mmHg), Venous pO2 (mmHg), Venous Temperature (Celsius), Measured O2 Sat, Hct, Hb (g/dl))'
                  f'Bytes Per Timestamp: {self._bytes_per_ts}',
                  f'Start of Acquisition: {stamp_str, self._timestamp_perf}'
                  ]
        end_of_line = '\n'
        hdr_str = f'{end_of_line.join(header)}{end_of_line}'
        return hdr_str

    def _write_to_file(self, data_buf, t):
        ts_bytes = struct.pack('i', int(t * 1000.0))
        self._fid_write.write(ts_bytes)
        self._fid_write.write(data_buf)

    def start_stream(self):
        self._USBSerial__serial.flushInput()
        self._USBSerial__serial.flushOutput()
        self.__evt_halt_streaming.clear()
        self.__thread_streaming = Thread(target=self.OnStreaming)
        self.__thread_streaming.start()

    def OnStreaming(self):
        while not self.__evt_halt_streaming.wait(25):
            self.stream()

    def stream(self):
        if self._USBSerial__serial.inWaiting() > 0:
            t = perf_counter()
            data_raw = self._USBSerial__serial.readline()
            buf_len = len(data_raw)
            self._write_to_file(data_raw, t)
            self._last_idx += buf_len
            self._fid_write.flush()
            self._USBSerial__serial.flushInput()
            self._USBSerial__serial.flushOutput()
        else:
            pass

    def stop_stream(self):
        if self.__thread_streaming and self.__thread_streaming.is_alive():
            self.__evt_halt_streaming.set()
            self.__thread_streaming.join(2.0)
            self.__thread_streaming = None
        self._USBSerial__serial.flushInput()
        self._USBSerial__serial.flushOutput()
        if self._fid_write:
            self._fid_write.close()
        self._fid_write = None