# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Demonstration of plots screen with full array of different sensors
"""
from enum import Enum
import time

import wx

from pyPerfusion.panel_plotting import PanelPlotting, PanelPlotLT
from pyPerfusion.panel_readout import PanelReadout
from pyHardware.pyAI import AI
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.SensorPoint import SensorPoint
import pyPerfusion.PerfusionConfig as LP_CFG





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

        self.hw_stream = AI(period_sample_ms=100)
        self.hw_events = AI(period_sample_ms=1000)
        self.sensors = [
            SensorStream('HA Flow', 'ml/min', self.hw_stream, valid_range=[20, 60]),
            SensorStream('PV Flow', 'ml/min', self.hw_stream, valid_range=[25, 35]),
            SensorStream('HA Pressure', 'mmHg', self.hw_stream, valid_range=[40, 60]),
            SensorStream('PV Pressure', 'mmHg', self.hw_stream, valid_range=[3, 7]),
            SensorStream('IVC Pressure', 'mmHg', self.hw_stream, valid_range=[0, 2])
            ]
        self.sensors[0].hw.set_demo_properties(0, demo_amp=80, demo_offset=0)
        self.sensors[1].hw.set_demo_properties(1, demo_amp=40, demo_offset=20)
        self.sensors[2].hw.set_demo_properties(2, demo_amp=100, demo_offset=0)
        self.sensors[3].hw.set_demo_properties(3, demo_amp=10, demo_offset=0)
        self.sensors[4].hw.set_demo_properties(4, demo_amp=3, demo_offset=0)
        for ch, sensor in enumerate(self.sensors):
            sensor.hw.add_channel(ch)
            sensor.set_ch_id(ch)
        self.hw_events.open()
        self.hw_stream.open()

        self.events = [SensorPoint('Vasodilator', '2 ml', self.hw_events),
                       SensorPoint('Vasoconstrictor', '2 ml', self.hw_events)
                       ]
        self.events[0].hw.set_read_period_ms(2250)
        self.events[1].hw.set_read_period_ms(3725)

        self.sizer_main = wx.BoxSizer(wx.HORIZONTAL)

        self.sizer_plot_grid = wx.GridSizer(cols=2, hgap=5, vgap=5)
        self.sizer_plots = []
        self._plots_main = []
        self._plots_lt = []

        for sensor_name in ['HA Flow', 'PV Flow', 'HA Pressure', 'PV Pressure']:
            self.sizer_plots.append(self._add_lt(self.get_sensor(sensor_name)))

        for plot in self._plots_main:
            plot.add_sensor(self.get_event('Vasoconstrictor'), color='orange')
            plot.add_sensor(self.get_event('Vasodilator'), color='blue')

        for plot in self._plots_lt:
            plot.add_sensor(self.get_event('Vasoconstrictor'), color='orange')
            plot.add_sensor(self.get_event('Vasodilator'), color='blue')

        for plot in self._plots_main:
            plot.show_legend()

        self.sizer_readout = wx.GridSizer(cols=1)
        self.sizer_config = wx.BoxSizer(wx.VERTICAL)
        self.choice_time = self._create_choice_time()
        self.label_choice_time = wx.StaticText(self, label='Display Window')

        self.__do_layout()
        self.__set_bindings()

        LP_CFG.set_base(basepath='~/Documents/LPTEST')
        LP_CFG.update_stream_folder()
        [sensor.open(LP_CFG.LP_PATH['stream']) for sensor in self.sensors]
        [sensor.start() for sensor in self.sensors]
        [evt.open(LP_CFG.LP_PATH['stream']) for evt in self.events]
        [evt.start() for evt in self.events]

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def get_sensor(self, sensor_name):
        sensor = next((sensor for sensor in self.sensors if sensor.name == sensor_name), None)
        print(f'{sensor.name}')
        return sensor

    def get_event(self, sensor_name):
        sensor = next((sensor for sensor in self.events if sensor.name == sensor_name), None)
        return sensor

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

        for sensor in self.sensors:
            self.sizer_readout.Add(PanelReadout(self, sensor), 1, wx.ALL | wx.EXPAND, border=1)

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
        self._plots_main.append(panel)
        panel = PanelPlotLT(self)
        panel.plot_frame_ms = 0
        panel.add_sensor(sensor)
        sizer.Add(panel, 1, wx.ALL | wx.EXPAND, border=0)
        self._plots_lt.append(panel)
        return sizer

    def _add_plot(self, sensor):
        panel = PanelPlotting(self)
        panel.add_sensor(sensor)
        return panel

    def OnClose(self, evt):
        for sensor in self.sensors:
            sensor.stop()
        for sensor in self.events:
            sensor.stop()
        self.hw_stream.close()
        self.hw_events.close()
        for plot in self._plots_main:
            plot.Destroy()
        for plot in self._plots_lt:
            plot.Destroy()
        self.Destroy()

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()

        return True

app = MyTestApp(0)
app.MainLoop()



