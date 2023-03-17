# -*- coding: utf-8 -*-
"""Panel class for plotting data real-time

Based on wx.Panel, this plots data real-time using SensorStream
and/or SensorPoint objects; and/or data from TSMSerial

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
import matplotlib.figure
import numpy as np

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig


class SensorPlot:
    def __init__(self, sensor, axes, readout=True):
        self._lgr = logging.getLogger(__name__)
        self._sensor = sensor
        self._reader = None
        self._axes = axes
        self._line = None
        self._invalid = None
        self._display = None
        self._color = None
        self._with_readout = readout

    @property
    def name(self):
        return self._reader.name if self._reader else ''

    @property
    def full_name(self):
        return f'{self._sensor.name}: {self._reader.name}'

    def plot(self, frame_ms, plot_len):
        readout_color = 'black'
        if not self._reader:
            return
        try:
            data_time, data = self._reader.retrieve_buffer(frame_ms, plot_len)
        except ValueError:
            # this can happen if no data has been collected, so don't print a message
            # as it can flood the logs
            data = None
            data_time = None

        if data is None or len(data) == 0:
            return

        readout = data[-1]
        if self._sensor.cfg.valid_range is not None:
            low_range = self._axes.fill_between(data_time, data, self._sensor.cfg.valid_range[0],
                                                where=data < self._sensor.cfg.valid_range[0], color='r')
            high_range = self._axes.fill_between(data_time, data, self._sensor.cfg.valid_range[1],
                                                 where=data > self._sensor.cfg.valid_range[1], color='r')
            self._invalid = [low_range, high_range]

            if self._with_readout:
                if readout < self._sensor.cfg.valid_range[0]:
                    readout_color = 'orange'
                elif readout > self._sensor.cfg.valid_range[1]:
                    readout_color = 'red'

        if self._line is None:
            self._line, = self._axes.plot(data_time, data, color=self._color)
            self._line.set_label(self._reader.name)
        else:
            self._line.set_data(data_time, data)

        if self._with_readout:
            self._line.set_label(f'{self._reader.name}: {readout:.2f} {self._sensor.cfg.units}')
            leg = self._axes.get_legend()
            if leg is not None:
                leg_texts = leg.get_texts()
                for txt in leg_texts:
                    txt.set_color(readout_color)
                    txt.set_fontsize('large')
                    # self._display.set_color(readout_color)


    def set_reader(self, reader, color=None, keep_old_title=False):
        self._reader = reader
        self._line = None
        self._color = color
        if self._sensor.cfg.valid_range is not None:
            rng = self._sensor.cfg.valid_range
            self._axes.axhspan(rng[0], rng[1], color='g', alpha=0.2)
        if not keep_old_title:
            self._axes.set_title(f'{self._sensor.name}\n')
            self._axes.set_ylabel(self._sensor.cfg.units)


class EventPlot(SensorPlot):
    def __init__(self, sensor, axes, readout=True):
        super().__init__(sensor, axes, readout)
        self._line = self._axes.vlines([], ymin=0, ymax=100, color=self._color)
        self._line.set_label(self.name)

    def plot(self, frame_ms, plot_len):
        if not self._reader:
            return
        data_time, data = self._reader.retrieve_buffer(frame_ms, plot_len)
        # self._lgr.debug(f'{self._sensor.cfg.name}: data_time is {data_time}')
        if data is None or len(data) == 0:
            return

        # del self._line
        if not self._line:
            self._line = self._axes.vlines(data_time, ymin=0, ymax=100, color=self._color)
            self._line.set_label(self._sensor.name)
        else:
            seg_new = [np.array([[t, 0], [t, 100]]) for t in data_time]
            self._line.set_segments(seg_new)


class PanelPlotting(wx.Panel):
    def __init__(self, parent, with_readout=True):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.__parent = parent
        self.__sensors = []
        self._with_readout = with_readout

        self.__plot_len = 200
        self._plot_frame_ms = 5_000

        self.fig = matplotlib.figure.Figure()
        self.fig.set_tight_layout(True)
        self._axes = self.fig.add_subplot(111)
        self.canvas = FigureCanvasWxAgg(self, wx.ID_ANY, self.fig)

        self._plots = []
        self._leg = []
        self.list_readers = wx.ListBox(self, wx.ID_ANY)

        self.__do_layout()
        self.__set_bindings()

        self.timer_plot = wx.Timer(self)
        self.timer_plot.Start(200, wx.TIMER_CONTINUOUS)

    @property
    def axes(self):
        return self._axes

    @property
    def plot_frame_ms(self):
        return self._plot_frame_ms

    @plot_frame_ms.setter
    def plot_frame_ms(self, ms):
        self._plot_frame_ms = ms

    def __do_layout(self):
        self.canvas.SetMinSize(wx.Size(1, 1))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.TOP | wx.LEFT | wx.GROW, border=1)
        sizer.Add(self.list_readers, 1, wx.ALL)
        self.list_readers.Hide()

        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.Bind(wx.EVT_TIMER, self.OnTimer)

    def plot(self):
        for plot in self._plots:
            plot.plot(self._plot_frame_ms, self.__plot_len)
        self.show_legend()
        # use relim and autoscale_view to ensure the streaming plot update the axes correctly
        self._axes.relim()
        self._axes.autoscale_view()
        self.canvas.draw()

    def OnTimer(self, event):
        if event.GetId() == self.timer_plot.GetId():
            self.plot()

    def show_legend(self):
        total_plots = len(self._plots)
        ncols = total_plots if total_plots % 2 == 0 else total_plots + 1
        if self._axes.lines:
            self._axes.legend(loc='lower right', bbox_to_anchor=(0.0, 1.01, 1.0, .102), ncol=ncols, mode="expand",
                              borderaxespad=0, framealpha=0.0, fontsize='x-small')

    def add_plot(self, plot):
        self._plots.append(plot)
        self.Fit()
        self.__parent.Fit()


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
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()
    app = MyTestApp(0)
    app.MainLoop()
