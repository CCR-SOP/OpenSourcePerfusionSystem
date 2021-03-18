# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for plotting data
"""
from enum import Enum
import numpy as np

import wx
import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
import matplotlib.transforms as mtransforms
# from matplotlib.backends.backend_wx import NavigationToolbar2Wx

from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.DexcomStream import DexcomStream
from pyPerfusion.SensorPoint import SensorPoint


class PanelPlotting(wx.Panel):
    def __init__(self, parent, with_readout=True):
        self.__parent = parent
        self.__sensors = []
        self._with_readout = with_readout
        wx.Panel.__init__(self, parent, -1)
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

    @plot_frame_ms.setter  # Can I use this?
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
            if type(sensor) is SensorStream:
                if sensor.valid_range is not None:
                    self.__line_invalid[sensor.name] = self.axes.fill_between(data_time, data, sensor.valid_range[0],
                                                                              where=data < sensor.valid_range[0],
                                                                              color='r')
                    self.__line_invalid[sensor.name] = self.axes.fill_between(data_time, data, sensor.valid_range[1],
                                                                              where=data > sensor.valid_range[1],
                                                                              color='r')
                    if self._with_readout:
                        if readout < sensor.valid_range[0]:
                            color = 'orange'
                        elif readout > sensor.valid_range[1]:
                            color = 'red'
                        else:
                            color = 'black'

                line.set_data(data_time, data)
                if self._with_readout:
                    self.__val_display[sensor.name].set_text(f'{readout:.0f}')
                    self.__val_display[sensor.name].set_color(color)
                try:
                    self.axes.collections.remove(self.__line_invalid[sensor.name])
                except ValueError:
                    pass

            elif type(sensor) is DexcomStream and data_time is not None:  # DexcomStream.get_data returns 'None' for data_time if DexcomStream thread is not running
                if readout == 5000:  # Signifies end of run
                    self.timer_plot.Stop()
                    print('stopped plotting')
                    self.axes.set_xlabel('End of Sensor Run: Replace Sensor Now!')
                    text = 'End'
                    color = 'red'
                elif readout == 0:
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

            elif type(sensor) is SensorPoint:
                    color = self.__colors[sensor.name]
                    del self.__line[sensor.name]
                    self.__line[sensor.name] = self.axes.vlines(data_time, ymin=0, ymax=100, color=color)


    def OnTimer(self, event):
        if event.GetId() == self.timer_plot.GetId():
            self.plot()

    def add_sensor(self, sensor, color='r'):
        assert isinstance(sensor, SensorStream)
        self.__sensors.append(sensor)
        if type(sensor) is SensorStream or DexcomStream:
            if type(sensor) is SensorStream:
                self.__line[sensor.name] = self.axes.plot([0] * self.__plot_len)
            elif type(sensor) is DexcomStream:
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
        elif type(sensor) is SensorPoint:
            self.__line[sensor.name] = self.axes.vlines(0, ymin=0, ymax=100, color=color, label=sensor.name)
            self.__colors[sensor.name] = color

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
    app = MyTestApp(0)
    app.MainLoop()
