import mcqlib_GB100.mcqlib.main as main
import mcqlib_GB100.mcqlib.utils as utils
import logging
import pathlib
import datetime
from time import perf_counter
import numpy as np
import struct

DATA_VERSION = 5

GAS_TYPES = {'Air': 1, 'Nitrogen': 2, 'Oxygen': 3, 'Carbon Dioxide': 4}

class GB100:

    """
    Class for serial communication over USB using GB100+ command set
    ...

    Methods
    -------
    open_stream(full_path)
        creates .txt and .dat files for recording GB100 data
    start_stream()
        starts thread for writing streamed data from mixer to file
    change_gas_mix()
        changes chosen parameters on gas mixer
    record_change()
        records changes to gas mixer in .dat file
    set_gas_types()
        sets gas for each channel
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
        self._datapoints_per_ts = 6
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
        self._write_to_file(np.array([0]), np.array([0]), np.array([0]), np.array([0]), np.array([0]), np.array([0]), np.array([0]))
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
                  f'Data Format: {str(np.dtype(np.float32))}',
                  f'Datapoints per Timestamp: {self._datapoints_per_ts} (Gas 1 ID, Gas 2 ID, Gas 1 Percentage, Gas 2 Percentage, Total Flow (ml/min), Working Status (O for OFF, 1 for ON)',
                  f'Bytes Per Timestamp: {self._bytes_per_ts}',
                  f'Start of Acquisition: {stamp_str, self._timestamp_perf}'
                  ]
        end_of_line = '\n'
        hdr_str = f'{end_of_line.join(header)}{end_of_line}'
        return hdr_str

    def start_stream(self):
        pass

    def record_change(self, gas_1_percentage, gas_2_percentage, total_flow, working_status):
        gas_1_ID = self.get_channel_id_gas(1)
        gas_2_ID = self.get_channel_id_gas(2)
        gas_1_ID_buffer = np.ones(1, dtype=np.float32) * np.float32(gas_1_ID)
        gas_2_ID_buffer = np.ones(1, dtype=np.float32) * np.float32(gas_2_ID)
        gas_1_percentage_buffer = np.ones(1, dtype=np.float32) * np.float32(gas_1_percentage)
        gas_2_percentage_buffer = np.ones(1, dtype=np.float32) * np.float32(gas_2_percentage)
        total_flow_buffer = np.ones(1, dtype=np.float32) * np.float32(total_flow)
        working_status_buffer = np.ones(1, dtype=np.float32) * np.float32(working_status)
        t = perf_counter()
        buf_len = len(gas_1_ID_buffer) + len(gas_2_ID_buffer) + len(gas_1_percentage_buffer) + len(gas_2_percentage_buffer) + len(total_flow_buffer) + len(working_status_buffer)
        self._write_to_file(gas_1_ID_buffer, gas_2_ID_buffer, gas_1_percentage_buffer, gas_2_percentage_buffer, total_flow_buffer, working_status_buffer, t)
        self._last_idx += buf_len
        self._fid_write.flush()

    def change_gas_mix(self, gas_1_percentage, gas_2_percentage, total_flow, working_status, gas1=None, gas2=None, balance_channel=None):
        if gas1 is not None and gas2 is not None:
            self.set_gas_types(gas1, gas2)
        if balance_channel is not None:
            self.set_balance_channel(balance_channel)
        self.set_mainboard_total_flow(total_flow)
        self.set_channel_percent_value(1, gas_1_percentage)
        self.set_channel_percent_value(2, gas_2_percentage)
        if working_status:  # If you want to start the gas flow
            if not self.get_working_status():  # Only start if mixer is currently off; or else this is redundant
                self.set_working_status_ON()
        else:
            if self.get_working_status():  # If you want to turn off the mixer, only do so if it is already on
                self.set_working_status_OFF()
            else:  # If the mixer is already off and will remain off, don't record the changes to gases / flows, as the system isn't actually seeing these changes
                return
        self.record_change(gas_1_percentage, gas_2_percentage, total_flow, working_status)

    def _write_to_file(self, gas_1_ID_buffer, gas_2_ID_buffer, gas_1_percentage_buffer, gas_2_percentage_buffer, total_flow_buffer, working_status_buffer, t):
        ts_bytes = struct.pack('i', int(t * 1000.0))
        self._fid_write.write(ts_bytes)
        gas_1_ID_buffer.tofile(self._fid_write)
        gas_2_ID_buffer.tofile(self._fid_write)
        gas_1_percentage_buffer.tofile(self._fid_write)
        gas_2_percentage_buffer.tofile(self._fid_write)
        total_flow_buffer.tofile(self._fid_write)
        working_status_buffer.tofile(self._fid_write)

    def set_gas_types(self, gas1, gas2):
        self.set_gas_from_xml_file(1, gas1)
        self.set_gas_from_xml_file(2, gas2)

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

    def get_working_status(self):  # Gives ON/OFF status of instrument
        response = main.get_working_status()
        return response

    def get_mainboard_total_flow(self):
        response = main.get_mainboard_total_flow()
        return response

    def get_channel_id_gas(self, channel):
        response = main.get_channel_id_gas(channel)
        return response

    def get_channel_k_factor_gas(self, channel):
        response = main.get_channel_k_factor_gas(channel)
        return response

    def get_gas_type(self, gasID):  # Returns gas name from gas ID
        response = utils.get_gas_type(gasID)
        return response

    def get_gas_ID(self, gas_name):
        return GAS_TYPES[gas_name]

    def get_channel_balance(self):  # Gives channel that automatically changes
        response = main.get_channel_balance()
        return response

    def get_channel_target_sccm(self, channel):  # Gives calculated flow
        response = main.get_channel_target_sccm(channel)
        return response

    def get_channel_sccm(self, channel):  # Gives actual flow
        response = main.get_channel_sccm(channel)
        return response

    def get_channel_percent_value(self, channel):
        response = main.get_channel_percent_value(channel)
        return response

    def set_working_status_ON(self):  # Start gas flow
        main.set_working_status_ON()

    def set_working_status_OFF(self):  # Stop gas flow
        main.set_working_status_OFF()

    def set_mainboard_total_flow(self, flow):
        main.set_mainboard_total_flow(flow)

    def set_channel_enabled(self, channel, status):  # Set channel ON (1) or OFF (2)
        main.set_channel_enabled(channel, status)

    def set_balance_channel(self, channel):
        main.set_balance_channel(channel)

    def set_gas_from_xml_file(self, channel, gasID):
        main.set_gas_from_xml_file(channel, gasID)

    def set_channel_percent_value(self, channel, percent):
        main.set_channel_percent_value(channel, percent)

    def setup_work(self, ch_balance, total_flow, perc_value=[]):  # Sets balance channel, total flow, and percent values for each channel
        total_channels = main.get_total_channels()
        # reset ch balance == 100
        main.set_balance_channel(ch_balance)
        main.set_channel_percent_value(ch_balance, 100.0)
        # set perc_value
        for i in range(len(perc_value)):
            if i + 1 != ch_balance and i < total_channels:
                main.set_channel_percent_value(i + 1, perc_value[i])
        # set flow
        main.set_mainboard_total_flow(total_flow)
        return 0
