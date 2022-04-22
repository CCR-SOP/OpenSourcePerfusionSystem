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
import matplotlib as mpl
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
import matplotlib.transforms as mtransforms
import numpy as np

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as LP_CFG


class SensorPlot:
    def __init__(self, sensor, axes, readout=True):
        self._lgr = logging.getLogger(__name__)
        self._sensor = sensor
        self._strategy = None
        self._axes = axes
        self._line = None
        self._invalid = None
        self._display = None
        self._color = None
        self._with_readout = readout

    @property
    def name(self):
        return self._strategy.name if self._strategy else ''

    @property
    def full_name(self):
        return f'{self._sensor.name}: {self._strategy.name}'

    def plot(self, frame_ms, plot_len):
        readout_color = 'black'
        if not self._strategy:
            return
        data_time, data = self._strategy.retrieve_buffer(frame_ms, plot_len)
        if data is None or len(data) == 0:
            return

        readout = data[-1]
        if self._sensor.valid_range is not None:
            low_range = self._axes.fill_between(data_time, data, self._sensor.valid_range[0],
                                                where=data < self._sensor.valid_range[0], color='r')
            high_range = self._axes.fill_between(data_time, data, self._sensor.valid_range[1],
                                                 where=data > self._sensor.valid_range[1], color='r')
            self._invalid = [low_range, high_range]

            if self._with_readout:
                if readout < self._sensor.valid_range[0]:
                    readout_color = 'orange'
                elif readout > self._sensor.valid_range[1]:
                    readout_color = 'red'

        if self._line is None:
            self._line, = self._axes.plot(data_time, data, color=self._color)
            self._line.set_label(self._strategy.name)
        else:
            self._line.set_data(data_time, data)

        if self._with_readout:
            self._line.set_label(f'{self._strategy.name}: {readout:.2f} {self._sensor.unit_str}')
            leg = self._axes.get_legend()
            if leg is not None:
                leg_texts = leg.get_texts()
                for txt in leg_texts:
                    txt.set_color(readout_color)
                    txt.set_fontsize('large')
                    # self._display.set_color(readout_color)

        try:
            self._axes.collections.remove(self._invalid)
        except ValueError:
            pass

    def set_strategy(self, strategy, color=None, keep_old_title=False):
        self._strategy = strategy
        self._line = None
        self._color = color
        if self._sensor.valid_range is not None:
            rng = self._sensor.valid_range
            self._axes.axhspan(rng[0], rng[1], color='g', alpha=0.2)
        if not keep_old_title:
            self._axes.set_title(f'{self._sensor.name}\n')
            self._axes.set_ylabel(self._sensor.unit_str)

class TSMSensorPlot:
    def __init__(self, plot_name, axes, unit):
        self._lgr = logging.getLogger(__name__)
        self._plot_name = plot_name
        self._axes = axes
        self._unit = unit
        self._configure_plot()

    @property
    def full_name(self):
        return self._plot_name

    def plot(self, data, data_time):
        if data is None:
            return
        if data_time is None:
            return
        self._axes.plot(data_time, data, 'ko')

    def _configure_plot(self):
        self._axes.set_title(self._plot_name)
        self._axes.set_ylabel(self._unit)

class EventPlot(SensorPlot):
    def __init__(self, sensor, axes, readout=True):
        super().__init__(sensor, axes, readout)
        self._line = self._axes.vlines([], ymin=0, ymax=100, color=self._color)
        self._line.set_label(self.name)

    def plot(self, frame_ms, plot_len):
        if not self._strategy:
            return
        data_time, data = self._strategy.retrieve_buffer(frame_ms, plot_len)
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
        self._valid_range = None
        self._plot_frame_ms = 5_000

        self.fig = mpl.figure.Figure()
        self.canvas = FigureCanvasWxAgg(self, wx.ID_ANY, self.fig)
        # self._axes = self.fig.add_subplot(111)
        self._axes = self.fig.add_axes([0.05, 0.05, 0.9, 0.85])
        self._plots = []
        self._leg = []
        self.list_strategy = wx.ListBox(self, wx.ID_ANY)

        self.__do_layout()
        self.__set_bindings()

        self.timer_plot = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
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
        self.fig.tight_layout()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvas, 10, wx.ALL | wx.EXPAND, border=1)
        sizer.Add(self.list_strategy, 1, wx.ALL)
        self.list_strategy.Hide()

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()

    def __set_bindings(self):
        pass

    def plot(self):
        for plot in self._plots:
            plot.plot(self._plot_frame_ms, self.__plot_len)

        self._axes.relim()
        self._axes.autoscale_view()
        self.canvas.draw()
        self.show_legend()

    def OnTimer(self, event):
        if event.GetId() == self.timer_plot.GetId():
            self.plot()

    def show_legend(self):
        total_plots = len(self._plots)
        ncols = total_plots if total_plots % 2 == 0 else total_plots + 1
        if self._axes.lines:
            self._axes.legend(loc='lower left', bbox_to_anchor=(0.0, 1.01, 1.0, .102), ncol=ncols, mode="expand",
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

class TSMPanelPlotting(wx.Panel):
    def __init__(self, parent, with_readout=True):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.__parent = parent
        self._with_readout = with_readout

        self.__plot_len = 200
        self._valid_range = None
        self._plot_frame_ms = 5_000

        self.fig = mpl.figure.Figure()
        self.canvas = FigureCanvasWxAgg(self, wx.ID_ANY, self.fig)
        # self._axes = self.fig.add_subplot(111)
        self._axes = self.fig.add_axes([0.05, 0.05, 0.9, 0.85])
        self._plots = []
        self._leg = []
        self._x_range_minutes = None

        self.__do_layout()
        self.__set_bindings()

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
        self.fig.tight_layout()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvas, 10, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()

    def __set_bindings(self):
        pass

    def plot(self, data, data_time):
        for plot in self._plots:
            plot.plot(data, data_time)
        current_upper_x_lim = data_time
        if not self._x_range_minutes:
            self._axes.set_xlim([0, current_upper_x_lim])
        else:
            self._axes.set_xlim([current_upper_x_lim - self._x_range_minutes, current_upper_x_lim])
        self._axes.relim()
        self._axes.autoscale_view()
        self.canvas.draw()

    def add_plot(self, plot):
        self._plots.append(plot)
        self.Fit()
        self.__parent.Fit()

class TSMPanelPlotLT(TSMPanelPlotting):
    def __init__(self, parent):
        TSMPanelPlotting.__init__(self, parent, with_readout=False)

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
