# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Demonstration of screen with chemical substances
"""
from enum import Enum
import time
from pathlib import Path

import wx

from pyPerfusion.panel_plotting import PanelPlotting, PanelPlotLT
from pyPerfusion.panel_readout import PanelReadout
from pyHardware.pyAI import AI
from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.SensorPoint import SensorPoint

sensors = {'PV Oxygen': SensorStream('PV Oxygen', '%', AI(10, demo_amp=80, demo_offset=0), valid_range=[20, 60]),
           'HA Oxygen': SensorStream('HA Oxygen', '%', AI(10, demo_amp=40, demo_offset=20), valid_range=[25, 35]),
           'Temperature': SensorStream('Temperature', 'F', AI(10, demo_amp=100, demo_offset=0), valid_range=[40, 60]),
           'pH': SensorStream('pH', '', AI(10, demo_amp=10, demo_offset=0), valid_range=[3, 7]),
           'CO2': SensorStream('CO2', '%', AI(10, demo_amp=3, demo_offset=0), valid_range=[0, 2]),
           'Glucose': SensorStream('Glucose', 'ml', AI(10, demo_amp=100, demo_offset=0), valid_range=[10, 90]),
           }

events = {'Insulin': SensorPoint('Insulin', '2 ml', AI(1000, read_period_ms=2250)),
          'Glucagen': SensorPoint('Glucagen', '2 ml', AI(1000, read_period_ms=3725))
          }


class PlotFrame(Enum):
    FROM_START = 0
    LAST_SECOND = 1_000
    LAST_5_SECONDS = 5_000
    LAST_MINUTE = 60_000


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.__plot_frame = PlotFrame.LAST_5_SECONDS

        self.sizer_main = wx.BoxSizer(wx.HORIZONTAL)

        self.sizer_plot_grid = wx.GridSizer(cols=2, hgap=5, vgap=5)
        self.sizer_plots = []
        self._plots_main = {}
        self._plots_lt = {}
        self._readouts = {}
        self.sizer_plots.append(self._add_lt(sensors['PV Oxygen']))
        self.sizer_plots.append(self._add_lt(sensors['pH']))
        self.sizer_plots.append(self._add_lt(sensors['CO2']))
        self.sizer_plots.append(self._add_lt(sensors['Glucose']))

        self._plots_main['Glucose'].add_sensor(events['Glucagen'], color='orange')
        self._plots_main['Glucose'].add_sensor(events['Insulin'], color='blue')
        self._plots_lt['Glucose'].add_sensor(events['Glucagen'], color='orange')
        self._plots_lt['Glucose'].add_sensor(events['Insulin'], color='blue')
        self._plots_main['Glucose'].show_legend()

        self._readouts['HA Oxygen'] = PanelReadout(self, sensors['HA Oxygen'])
        self._readouts['Temperature'] = PanelReadout(self, sensors['Temperature'])

        self.sizer_readout = wx.GridSizer(cols=1)
        self.sizer_config = wx.BoxSizer(wx.VERTICAL)
        self.choice_time = self._create_choice_time()
        self.label_choice_time = wx.StaticText(self, label='Display Window')

        self.__do_layout()
        self.__set_bindings()

        [sensor.open(Path('./__data__'), Path('yyyy-mm-dd')) for sensor in sensors.values()]
        [sensor.start() for sensor in sensors.values()]
        [evt.open(Path('./__data__'), Path('yyyy-mm-dd')) for evt in events.values()]
        [evt.start() for evt in events.values()]

    def _create_choice_time(self):
        parameters = [item.name for item in PlotFrame]
        choice = wx.Choice(self, choices=parameters)
        choice.SetStringSelection(self.__plot_frame.name)
        font = choice.GetFont()
        font.SetPointSize(12)
        choice.SetFont(font)
        return choice

    def __do_layout(self):
        # self.sizer_main.Add(self.choice_plot_parameter, 1, wx.ALIGN_CENTER_HORIZONTAL)
        for plot in self.sizer_plots:
            self.sizer_plot_grid.Add(plot, 1, wx.ALL | wx.EXPAND)

        self.sizer_main.Add(self.sizer_plot_grid, 1, wx.ALL | wx.EXPAND)

        for sensor in self._readouts.values():
            self.sizer_readout.Add(sensor, 1, wx.ALL | wx.EXPAND, border=1)

        self.sizer_config.Add(self.label_choice_time, 1, wx.ALL | wx.ALIGN_CENTER)
        self.sizer_config.Add(self.choice_time, 1, wx.ALL)
        self.sizer_readout.AddSpacer(5)
        self.sizer_readout.Add(self.sizer_config, 1, wx.ALL)
        self.sizer_main.Add(self.sizer_readout)
        self.SetSizer(self.sizer_main)
        self.Fit()
        self.Layout()
        self.Maximize(True)

    def __set_bindings(self):
        self.choice_time.Bind(wx.EVT_CHOICE, self._onchange_plotchoice)

    def _onchange_plotchoice(self, event):
        self.__plot_frame = PlotFrame[self.choice_time.GetStringSelection()]
        for plot in self._plots_main:
            plot.plot_frame_ms = self.__plot_frame.value

    def _add_lt(self, sensor):
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel = PanelPlotting(self)
        panel.add_sensor(sensor)
        sizer.Add(panel, 6, wx.ALL | wx.EXPAND, border=0)
        self._plots_main[sensor.name] = panel
        panel = PanelPlotLT(self)
        panel.plot_frame_ms = 0
        panel.add_sensor(sensor)
        sizer.Add(panel, 1, wx.ALL | wx.EXPAND, border=0)
        self._plots_lt[sensor.name] = panel
        return sizer

    def _add_plot(self, sensor):
        panel = PanelPlotting(self)
        panel.add_sensor(sensor)
        return panel


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


app = MyTestApp(0)
app.MainLoop()
time.sleep(10)
[sensor.stop() for sensor in sensors.values()]

