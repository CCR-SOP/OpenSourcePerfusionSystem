from pyHardware.pyUSBSerial import USBSerial
import pathlib
import datetime
import numpy as np
import struct
from time import perf_counter

DATA_VERSION = 3

class PHDserial(USBSerial):

    """
    Class for serial communication over USB using PHD (Pump 11 Elite) command set; class also records data about syringe infusions to a .dat file
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
        begin infusion of syringe; non-targeted (i.e. for an "infinite" infusion)
    target_infuse(infusion_volume, infusion_rate)
        begin infusion of syringe; targeted (i.e. will terminate after a certain infusion volume is reached)
    stop()
        stop infusion of syringe
    stop_stream()
        stops recording of syringe data
    set_param(param, value)
        sets a syringe pump parameter (param) to (value)
    """

    def __init__(self, name):
        super().__init__()
        self.__addr = 0
        self._manufacturers = {}
        self._syringes = {}
        self._response = ''
        self.reset = True
        self.cooldown = False

        self.name = name
        self._fid_write = None
        self._full_path = pathlib.Path.cwd()
        self._filename = pathlib.Path(f'{self.name}')
        self._ext = '.dat'
        self._timestamp = None
        self._end_of_header = 0
        self._last_idx = 0
        self._datapoints_per_ts = 2
        self._bytes_per_ts = 8

    @property
    def full_path(self):
        return self._full_path / self._filename.with_suffix(self._ext)

    @property
    def manufacturers(self):
        return self._manufacturers

    @manufacturers.setter
    def manufacturers(self, codes):
        self._manufacturers = codes

    @property
    def syringes(self):
        return self._syringes

    @syringes.setter
    def syringes(self, syringes):
        self._syringes = syringes

    def open(self, port_name, baud, addr=0):
        super().open(port_name, baud)
        self.__addr = addr
        self._USBSerial__serial.xonxoff = True
        self.send('')
        self.send(f'address {self.__addr}\r')
        self.send('poll REMOTE\r')

    def open_stream(self, full_path):
        if not isinstance(full_path, pathlib.Path):
            full_path = pathlib.Path(full_path)
        self._full_path = full_path
        if not self._full_path.exists():
            self._full_path.mkdir(parents=True, exist_ok=True)
        self._timestamp = datetime.datetime.now()
        if self._fid_write:
            self._fid_write.close()
            self._fid_write = None

        self._open_write()
        self._write_to_file(np.array([0]), np.array([0]), np.array([0]))
        self._fid_write.seek(0)
        # self._open_read()

        self.print_stream_info()

    def _open_write(self):
        print(f'opening {self.full_path}')
        self._fid_write = open(self.full_path, 'w+b')

    def _write_to_file(self, data_buf_vol, data_buf_rate, t):
        ts_bytes = struct.pack('i', int(t * 1000.0))
        self._fid_write.write(ts_bytes)
        data_buf_vol.tofile(self._fid_write)
        data_buf_rate.tofile(self._fid_write)

    def print_stream_info(self):
        hdr_str = self._get_stream_info()
        filename = self.full_path.with_suffix('.txt')
        print(f"printing stream info to {filename}")
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
                  f'Start of Acquisition: {stamp_str}'
                  ]
        end_of_line = '\n'
        hdr_str = f'{end_of_line.join(header)}{end_of_line}'
        return hdr_str

    def start_stream(self):
        pass

    def target_infuse(self, infusion_volume, infusion_rate):
        self.send('irun\r')
        volume_buffer = np.ones(1, dtype=np.float32) * np.float32(infusion_volume)
        rate_buffer = np.ones(1, dtype=np.float32) * np.float32(infusion_rate)
        t = perf_counter()
        if volume_buffer is not None and rate_buffer is not None and self._fid_write is not None:
            buf_len = len(volume_buffer) + len(rate_buffer)
            self._write_to_file(volume_buffer, rate_buffer, t)
            self._last_idx += buf_len
            self._fid_write.flush()

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
        while chunk:
            chunk, ts = self.__read_chunk(_fid)
            if chunk and (cur_time - ts < last_ms or last_ms == 0):
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
        if len(ts_bytes) == 8:
            ts, = struct.unpack('i', ts_bytes)
            data_buf = np.fromfile(_fid, dtype=np.float32, count=self._datapoints_per_ts)
        return data_buf, ts

    def send(self, str2send):
        super().send(str2send)
        self._response = self.get_response(max_bytes=1000)

    def infuse(self):
        self.send('irun\r')

    def stop(self):
        self.send('stop\r')

    def set_param(self, param, value):
        self.send(f'{param} {value}')

    def set_syringe_manufacturer_size(self, manu_code, syringe_size):
        self.set_param('syrm', f'{manu_code} {syringe_size}\r')
       # print('New Syringe Information:')
       # self.get_syringe_info()

    def set_infusion_rate(self, rate, unit_str):  # can be changed mid-run
        self.set_param('irate', f'{rate} {unit_str}\r')
        # print('Infusion rate set to :')
       # self.get_infusion_rate()

    def reset_infusion_volume(self):
        self.send('civolume\r')
        # print('Infusion volume reset to :')
        # self.get_infused_volume()

    def set_target_volume(self, volume, volume_units):
        self.set_param('tvolume', f'{volume} {volume_units}\r')
        # print('Target volume set to %s' % volume + ' ' + volume_units)

    def get_target_volume(self):
        self.send('tvolume\r')
        print(self._response)

    def reset_target_volume(self):
        self.send('ctvolume\r')
        # print('Target volume cleared')

    def get_syringe_info(self):
        self.send('syrm\r')
        print(self._response)

    def get_infusion_rate(self):
        self.send('irate\r')
        print(self._response)
        return self._response

    def get_infused_volume(self):
        self.send('ivolume\r')
        print(self._response)
        return self._response

    def ResetSyringe(self):
        self.reset_infusion_volume()
        self.reset_target_volume()

    def syringe_configuration(self):
        self.set_syringe_manufacturer_size('bdp', '60 ml')
        self.set_infusion_rate(30, 'ml/min')

    def update_syringe_manufacturers(self):
        self.send('syrmanu ?\r')
        if self._response:
            response = self._response[1:-1].split('\n')  # First and last values of the string are '\n'; remove these, then separate by '\n'
            for i in range(len(response)):
                syringe_info = response[i]
                syringe_info_separation = syringe_info.split('  ')  # Double spaces separate manufacturing code from manufacturing information
                self._manufacturers[syringe_info_separation[0]] = syringe_info_separation[1]

    def update_syringe_types(self):
        for code in self._manufacturers.keys():
            self.send(f'syrmanu {code} ?\r')
            self._syringes[code] = self._response[1:-1].split('\n')  # First and last values of each syringe's volume string are '\n', remove these, then separate by '\n'

    def print_available_syringes(self):
        for code, name in self._manufacturers.items():
            print(f'{name} ({code})')
            syringes = self._syringes[code]
            for syringe in syringes:
                print(f'\t {syringe}')
