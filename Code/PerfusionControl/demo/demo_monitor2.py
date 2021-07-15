# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Demonstration of screen with chemical substances
"""
from enum import Enum
import time
import logging

import wx

from pyPerfusion.plotting import PanelPlotting, PanelPlotLT, SensorPlot, EventPlot
from pyPerfusion.panel_readout import PanelReadout
from pyHardware.pyAI import AI
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.SensorPoint import SensorPoint
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.FileStrategy import StreamToFile, PointsToFile
import pyPerfusion.utils as utils


class PlotFrame(Enum):
    FROM_START = 0
    LAST_SECOND = 1_000
    LAST_5_SECONDS = 5_000
    LAST_MINUTE = 60_000

demo_properties = [(80, 0), (40, 20), (100, 0), (10, 0), (3, 0), (5, 2)]


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.__plot_frame = PlotFrame.LAST_5_SECONDS

        LP_CFG.set_base(basepath='~/Documents/LPTEST')
        LP_CFG.update_stream_folder()
        self._lgr = logging.getLogger(__name__)
        utils.setup_stream_logger(self._lgr, logging.DEBUG)
        utils.configure_matplotlib_logging()

        self.hw_stream = AI(period_sample_ms=100)
        self.hw_events = [AI(period_sample_ms=1000, read_period_ms=3000),
                          AI(period_sample_ms=1000, read_period_ms=1500)]
        self.sensors = [
            SensorStream('PV Oxygen', '%', self.hw_stream, valid_range=[20, 60]),
            SensorStream('HA Oxygen', '%', self.hw_stream, valid_range=[25, 35]),
            SensorStream('Temperature', 'F', self.hw_stream, valid_range=[40, 60]),
            SensorStream('pH', '', self.hw_stream, valid_range=[3, 7]),
            SensorStream('CO2', '%', self.hw_stream, valid_range=[0, 2]),
            SensorStream('Glucose', 'ml', self.hw_stream, valid_range=[10, 90]),
            ]
        self.hw_stream.open()

        for ch, sensor in enumerate(self.sensors):
            sensor.hw.add_channel(ch)
            sensor.set_ch_id(ch)
            prop = demo_properties[ch]
            sensor.hw.set_demo_properties(ch=ch, demo_amp=prop[0], demo_offset=prop[1])

        for sensor in self.sensors:
            raw = StreamToFile('Raw', None, self.hw_stream.buf_len)
            raw.open(LP_CFG.LP_PATH['stream'], f'{sensor.name}_raw', sensor.params)
            sensor.add_strategy(raw)


        self.events = [SensorPoint('Insulin', '2 ml', self.hw_events[0]),
                       SensorPoint('Glucagen', '2 ml', self.hw_events[1])
                       ]

        for evt in self.hw_events:
            evt.open()

        for ch, sensor in enumerate(self.events):
            sensor.hw.add_channel(ch)
            sensor.set_ch_id(ch)
            prop = demo_properties[ch]
            sensor.hw.set_demo_properties(ch=ch, demo_amp=prop[0], demo_offset=prop[1])

        self.events[0].hw.set_read_period_ms(2250)
        self.events[1].hw.set_read_period_ms(3725)
        for evt in self.events:
            raw = PointsToFile('Raw', None, evt.hw.buf_len)
            raw.open(LP_CFG.LP_PATH['stream'], f'{evt.name}_raw', evt.params)
            evt.add_strategy(raw)
        self.sizer_main = wx.BoxSizer(wx.HORIZONTAL)

        self.sizer_plot_grid = wx.GridSizer(cols=2, hgap=5, vgap=5)
        self.sizer_plots = []
        self._plots_main = []
        self._plots_lt = []
        self._readouts = {}

        for sensor_name in ['PV Oxygen', 'pH', 'CO2', 'Glucose']:
            self.sizer_plots.append(self._add_lt(self.get_sensor(sensor_name)))

        for plot in self._plots_main:
            evt = self.events[0]
            plotevt = EventPlot(evt, plot.axes)
            plotevt.set_strategy(evt.get_file_strategy('Raw'), color='orange',
                                 keep_old_title=True)
            plot.add_plot(plotevt)

            evt = self.events[1]
            plotevt = EventPlot(evt, plot.axes)
            plotevt.set_strategy(evt.get_file_strategy('Raw'), color='blue',
                                 keep_old_title=True)
            plot.add_plot(plotevt)

        for plot in self._plots_lt:
            evt = self.events[0]
            plotevt = EventPlot(evt, plot.axes)
            plotevt.set_strategy(evt.get_file_strategy('Raw'), color='orange',
                                 keep_old_title=True)
            plot.add_plot(plotevt)

            evt = self.events[1]
            plotevt = EventPlot(evt, plot.axes)
            plotevt.set_strategy(evt.get_file_strategy('Raw'), color='blue',
                                 keep_old_title=True)
            plot.add_plot(plotevt)

        for plot in self._plots_main:
            plot.show_legend()

        self._readouts['HA Oxygen'] = PanelReadout(self, self.get_sensor('HA Oxygen'))
        self._readouts['Temperature'] = PanelReadout(self, self.get_sensor('Temperature'))

        self.sizer_readout = wx.GridSizer(cols=1)
        self.sizer_config = wx.BoxSizer(wx.VERTICAL)
        self.choice_time = self._create_choice_time()
        self.label_choice_time = wx.StaticText(self, label='Display Window')

        self.__do_layout()
        self.__set_bindings()

        [sensor.open() for sensor in self.sensors]
        [sensor.start() for sensor in self.sensors]
        [evt.open() for evt in self.events]
        [evt.start() for evt in self.events]
        [evt.start() for evt in self.hw_events]
        self.hw_stream.start()

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
        self._plots_main.append(panel)
        plotraw = SensorPlot(sensor, panel.axes)
        plotraw.set_strategy(sensor.get_file_strategy('Raw'))
        panel.add_plot(plotraw)
        sizer.Add(panel, 10, wx.ALL | wx.EXPAND, border=0)

        panel = PanelPlotLT(self)
        self._plots_lt.append(panel)
        panel.plot_frame_ms = -1

        plotraw = SensorPlot(sensor, panel.axes)
        plotraw.set_strategy(sensor.get_file_strategy('Raw'))
        panel.add_plot(plotraw)
        sizer.Add(panel, 2, wx.ALL | wx.EXPAND, border=0)

        return sizer

    def _add_plot(self, sensor):
        panel = PanelPlotting(self)
        plotraw = SensorPlot(sensor, panel.axes)
        plotraw.set_strategy(sensor.get_file_strategy('Raw'))
        panel.add_plot(plotraw)
        return panel

    def OnClose(self, evt):
        for sensor in self.sensors:
            sensor.stop()
        for sensor in self.events:
            sensor.stop()
        self.hw_stream.close()
        for evt in self.hw_events:
            evt.close()
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


if __name__ == '__main__':
    app = MyTestApp(0)
    app.MainLoop()