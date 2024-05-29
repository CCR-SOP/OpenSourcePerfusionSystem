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
from typing import Protocol
import time

import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
import matplotlib.figure
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig


class DeviceInterface(Protocol):
    @property
    def sampling_freq(self) -> int:
        """ Returns the sampling frequency in Hz"""
        pass

    @property
    def filename(self) -> str:
        """ Returns filename of saved data file"""
        pass


class PanelPlotting(wx.Panel):
    def __init__(self, parent, with_readout=True):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self._with_readout = with_readout
        self._readers = []

        self.secs2display = 5
        self.plot_len = 200

        self.fig = matplotlib.figure.Figure()
        self._axes = self.fig.add_subplot(111)
        self.canvas = FigureCanvasWxAgg(self, wx.ID_ANY, self.fig)
        self.legend = None

        self.canvas.mpl_connect('pick_event', self.on_pick)
        self.map_legend_to_axis = {}

        self.colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        self.lines = None
        self.anim = None

        self.__do_layout()
        self.__set_bindings()

        self.init_plot()
        self.anim = animation.FuncAnimation(self.fig, self.animate,
                                            interval=100, blit=True,
                                            cache_frame_data=False)

    @property
    def axes(self):
        return self._axes

    def __do_layout(self):
        self.canvas.SetMinSize(wx.Size(1, 1))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.TOP | wx.LEFT | wx.GROW, border=1)

        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def init_plot(self):
        self.time_vector = np.linspace(-self.secs2display, 0, num=self.plot_len)
        self._axes.clear()
        self.lines = self._axes.plot(self.time_vector,
                                     np.zeros([self.plot_len, len(self._readers)], dtype=np.float64))
        for idx, reader in enumerate(self._readers):
            self.lines[idx].set_label(f'{reader.name}')

        total_plots = len(self._readers)
        ncols = total_plots if total_plots % 2 == 0 else total_plots + 1
        if self._axes.lines:
            leg = self._axes.legend(loc='lower right', bbox_to_anchor=(0.0, 1.01, 1.0, .102),
                                    ncol=ncols, mode="expand",
                                    borderaxespad=0, framealpha=0.0, fontsize='medium')
            leg.set_picker(5)
            self.legend = leg

        return self.lines

    def animate(self, i):
        readout_color = 'black'

        for idx, line in enumerate(self.lines):
            reader = self._readers[idx]
            t, data = reader.retrieve_buffer(self.secs2display * 1000, self.plot_len)
            line.set_data(t, data)
            line.set_color(self.colors[idx])
            if self._with_readout:
                try:
                    unit_str = f'{reader.cfg.units}'
                except AttributeError:
                    # if sensor doesn't have units, ignore
                    unit_str = ''
                try:
                    line.set_label(f'{reader.name}: {data[-1]:.2f} {unit_str}')
                except IndexError:
                    # no data yet
                    pass

        self._axes.relim()
        self._axes.autoscale_view()
        self.canvas.draw()
        return self.lines

    def on_pick(self, event):
        reader_names = [reader.name for reader in self._readers]
        selections = [idx for idx, line in enumerate(self.lines) if line.get_visible()]
        dlg = wx.MultiChoiceDialog(None, "Choose output", "", reader_names, wx.CHOICEDLG_STYLE)
        dlg.SetSelections(selections)
        if dlg.ShowModal() == wx.ID_OK:
            selections = dlg.GetSelections()
            for idx in range(len(self._readers)):
                if idx in selections:
                    self.lines[idx].set_visible(True)
                    self.legend.get_lines()[idx].set_visible(True)
                else:
                    self.lines[idx].set_visible(False)
                    self.legend.get_lines()[idx].set_visible(False)
            self.canvas.draw()

    def add_sensor(self, sensor, reader):
        self._readers.append(reader)
        self.init_plot()

    def OnClose(self, evt):
        self.Destroy()


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
    utils.setup_default_logging('plotting', logging.DEBUG)
    app = MyTestApp(0)
    app.MainLoop()
