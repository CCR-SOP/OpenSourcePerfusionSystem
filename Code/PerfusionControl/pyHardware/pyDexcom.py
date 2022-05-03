import pathlib
import datetime
import logging
from time import perf_counter
from threading import Thread, Event
import struct

import numpy as np

import wx
import matplotlib as mpl
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as LP_CFG

DATA_VERSION = 6

class DexcomSensor:

    """
       Class for serial communication with Dexcom Receiver over USB
       ...
       Methods
       -------
       open() ###
           UPDATE
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

    def __init__(self, name, sensor, COM):
        self._logger = logging.getLogger(__name__)
        self.name = name
        self.sensor = sensor(COM)  ###
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

    def open(self):  ###
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
                  f'Unit: mg/dL',
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
        data, new_time = self.sensor.get_data()
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

class PanelPlotting(wx.Panel):
    def __init__(self, parent, with_readout=True):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.__parent = parent
        self.__sensors = []
        self._with_readout = with_readout

        self.__plot_len = 200
        self._valid_range = None
        self._plot_frame_ms = 5_000

        self.fig = mpl.figure.Figure()
        self.canvas = FigureCanvasWxAgg(self, wx.ID_ANY, self.fig)
        self.canvas.SetMinSize(wx.Size(1, 1))
        self.fig.tight_layout()

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.__do_layout()
        self.__set_bindings()
        self.axes = self.fig.add_subplot(111)
        self.__line = {}
        self.__line_range = {}
        self._shaded = {}
        self.__line_invalid = {}
        self.__colors = {}
        self.__val_display = {}

        self.timer_plot = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer_plot.Start(200, wx.TIMER_CONTINUOUS)

    @property
    def plot_frame_ms(self):
        return self._plot_frame_ms

    @plot_frame_ms.setter
    def plot_frame_ms(self, ms):
        self._plot_frame_ms = ms

    def __do_layout(self):
        self.sizer.Add(self.canvas, 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(self.sizer)
        self.Fit()
        self.Layout()

    def __set_bindings(self):
        pass

    def plot(self):
        for sensor in self.__sensors:
            self._plot(self.__line[sensor.name], sensor)

        self.axes.relim()
        self.axes.autoscale_view()
        self.canvas.draw()

    def _plot(self, line, sensor):
        color = 'black'
        data_time, data = sensor.get_data(self._plot_frame_ms, self.__plot_len)
        if data is not None and len(data) > 0:
            readout = data[-1]
            if type(sensor) is DexcomPoint and data_time is not None:  # DexcomPoint.get_data returns 'None' for data_time if DexcomPoint thread is not running
                readout = float(readout[-1])
                if readout == 5000:  # Signifies end of run
                    self.timer_plot.Stop()
                    self.axes.set_xlabel('End of Sensor Run: Replace Sensor Now!')
                    text = 'End'
                    color = 'red'
                elif readout == 0.10000000149011612:  # Due to storage of data in file, 0.1 becomes this value after extraction and conversion to float
                    self.axes.plot_date(data_time, readout, color='white', marker='o', xdate=True)
                    text = 'N/A'
                    color = 'black'
                elif readout > self._valid_range[1]:
                    self.axes.plot_date(data_time, readout, color='red', marker='o', xdate=True)
                    text = f'{readout:.0f}'
                    color = 'red'
                elif readout < self._valid_range[0]:
                    self.axes.plot_date(data_time, readout, color='orange', marker='o', xdate=True)
                    text = f'{readout:.0f}'
                    color = 'orange'
                else:
                    self.axes.plot_date(data_time, readout, color='black', marker='o', xdate=True)
                    text = f'{readout:.0f}'
                    color = 'black'
                if type(self) is not PanelPlotLT:
                    self.__val_display[sensor.name].set_text(text)
                    self.__val_display[sensor.name].set_color(color)
                    labels = self.axes.get_xticklabels()
                    if len(labels) >= 12:
                        self.axes.set_xlim(left=labels[-12].get_text(), right=data_time)

    def OnTimer(self, event):
        if event.GetId() == self.timer_plot.GetId():
            self.plot()

    def add_sensor(self, sensor, color='r'):
        assert isinstance(sensor, SensorStream)
        self.__sensors.append(sensor)
        if type(sensor) is DexcomPoint:
            self.__line[sensor.name] = None
            self.__line_invalid[sensor.name] = self.axes.fill_between([0, 1], [0, 0], [0, 0])
            if self._with_readout:
                self.__val_display[sensor.name] = self.axes.text(1.06, 0.5, '0',
                                                                 transform=self.axes.transAxes,
                                                                 fontsize=18, ha='center')
                self.axes.text(1.06, 0.4, sensor.unit_str, transform=self.axes.transAxes, fontsize=8, ha='center')
            if sensor.valid_range is not None:
                rng = sensor.valid_range
                self._shaded['normal'] = self.axes.axhspan(rng[0], rng[1], color='g', alpha=0.2)
                self._valid_range = rng
            self._configure_plot(sensor)

    def _configure_plot(self, sensor):
        self.axes.set_title(sensor.name)
        self.axes.set_ylabel(sensor.unit_str)
        self.show_legend()

    def show_legend(self):
        self.axes.legend(loc='lower left', bbox_to_anchor=(0.0, 1.01, 1.0, .102), ncol=2, mode="expand",
                         borderaxespad=0, framealpha=0.0, fontsize='x-small')


class PanelPlotLT(PanelPlotting):
    def __init__(self, parent):
        PanelPlotting.__init__(self, parent, with_readout=False)

    def _configure_plot(self, sensor):
        self.axes.set_yticklabels([])
        self.axes.set_xticklabels([])


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelPlotting(self)


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    LP_CFG.set_base(basepath='~/Documents/LPTEST')
    LP_CFG.update_stream_folder()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()
    app = MyTestApp(0)
    app.MainLoop()


