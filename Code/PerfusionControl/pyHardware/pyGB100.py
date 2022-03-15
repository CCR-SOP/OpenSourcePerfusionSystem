import logging

import sys, time
import mcqlib_GB100.mcqlib.main as mcq
import pathlib
import datetime
import numpy as np
import struct
from time import perf_counter

sys.path.append("/mcqlib_GB100/mcqlib")

GAS_IDS = {'Air': 1, 'Nitrogen': 2, 'Oxygen': 3, 'Carbon Dioxide': 4}

class GB100(mcq):

    """
    Class for controlling GB100+ gas mixers using USB/RS485 communication; class also records data about gas mix to a .dat file
    ...

    Attributes
    ----------


    Methods
    -------
    open(port_name, baud, addr)
        opens USB port of given name with the specified baud rate using given syringe pump address
    open_stream(full_path)
        creates .txt and .dat files for recording syringe data
    infuse()
        begin infusion of syringe; for both continuous ('infinite') and targeted (will terminate after a certain infusion volume is reached) infusions
    stop()
        stop infusion of syringe
    record_infusion()
        record details of latest syringe infusion
    stop_stream()
        stops recording of syringe data
    set_param(param, value)
        sets a syringe pump parameter (param) to (value)
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
        self._datapoints_per_ts = 2 ##
        self._bytes_per_ts = 4

    def set_gas(self, channel, gas):
        gas_number = GAS_IDS[gas]
        mcq.set_channel_id_gas_only(channel, gas)

    def get_total_flow(self):
            flow = mcq.get_mainboard_total_flow()
            return flow

    def set_total_flow(self, flow):
            mcq.set_mainboard_total_flow(flow)

    def get_channel_percentages(self):
            mcq.get_channel_percent_value(channel): Gives
            percent
            mix
            for each channel

    mcq.get_channel_sccm(channel_nr): Gives
    actual
    gas
    flow
    from channel
    mcq.get_channel_target_sccm(channel_nr): Gives
    target
    gas
    flow
    from channel
    mcq.set_mainboard_total_flow(flow): Set
    total
    gas
    flow
    rate
    mcq.set_channel_percent_value(channel_nr, percentage): Sets
    certain
    percentage
    for that channel; MAKE SURE YOU SET THIS FOR THE CHANNEL THAT ISN'T BEING BALANCED















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
        self._timestamp_perf = perf_counter()
        if self._fid_write:
            self._fid_write.close()
            self._fid_write = None

        self._open_write()
        self._write_to_file(np.array([0]), np.array([0]), np.array([0]))
        self._fid_write.seek(0)
        # self._open_read()

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
                  f'Syringe: {self.name}',
                  f'Volume Unit: ml',
                  f'Rate Unit: ml/min',
                  f'Data Format: {str(np.dtype(np.float32))}',
                  f'Datapoints Per Timestamp: {self._datapoints_per_ts} (Infusion Volume and Infusion Rate)',
                  f'Bytes Per Timestamp: {self._bytes_per_ts}',
                  f'Start of Acquisition: {stamp_str, self._timestamp_perf}'
                  ]
        end_of_line = '\n'
        hdr_str = f'{end_of_line.join(header)}{end_of_line}'
        return hdr_str

    def start_stream(self):
        pass

    def get_stream_info(self):
        infuse_rate = self.get_infusion_rate().split(' ')[0]
        infuse_unit = self.get_infusion_rate().split(' ')[1]
        volume_unit = self.get_target_volume().split(' ')[1]
        ml_min_rate = True
        ml_volume = True
        if 'ul' in infuse_unit:
            ml_min_rate = False
        if 'ul' in volume_unit:
            ml_volume = False
        return infuse_rate, ml_min_rate, ml_volume

    def infuse(self, infusion_volume, infusion_rate, ml_volume, ml_min_rate):
        self.send('irun\r')
        infusion_rate = float(infusion_rate)
        if not ml_volume:
            if infusion_volume == -2:
                pass
            else:
                infusion_volume = infusion_volume / 1000
        if not ml_min_rate:
            infusion_rate = infusion_rate / 1000
        self.record_infusion(infusion_volume, infusion_rate)

    def stop(self, infusion_volume, infusion_rate, ml_volume, ml_min_rate):
        self.send('stop\r')
        infusion_rate = float(infusion_rate)
        if not ml_volume:
            if infusion_volume == -1:
                pass
            else:
                infusion_volume = infusion_volume / 1000
        if not ml_min_rate:
            infusion_rate = infusion_rate / 1000
        self.record_infusion(infusion_volume, infusion_rate)

    def record_infusion(self, infusion_volume, infusion_rate):
        volume_buffer = np.ones(1, dtype=np.float32) * np.float32(infusion_volume)
        rate_buffer = np.ones(1, dtype=np.float32) * np.float32(infusion_rate)
        t = perf_counter()
        if volume_buffer is not None and rate_buffer is not None and self._fid_write is not None:
            buf_len = len(volume_buffer) + len(rate_buffer)
            self._write_to_file(volume_buffer, rate_buffer, t)
            self._last_idx += buf_len
            self._fid_write.flush()

    def _write_to_file(self, data_buf_vol, data_buf_rate, t):
        ts_bytes = struct.pack('i', int(t * 1000.0))
        self._fid_write.write(ts_bytes)
        data_buf_vol.tofile(self._fid_write)
        data_buf_rate.tofile(self._fid_write)

    def stop_stream(self):
        if self._fid_write:
            self._fid_write.close()
        self._fid_write = None

    def get_data(self, last_ms, samples_needed):
        _fid, tmp = self._open_read()
        cur_time = int(perf_counter() * 1000)
        _fid.seek(0)
        chunk = [1]
        data_time = []
        data = []
        while chunk[0]:
            chunk, ts = self.__read_chunk(_fid)
            if type(chunk) is list:
                break
            if chunk.any() and (cur_time - ts < last_ms or last_ms == 0):
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
