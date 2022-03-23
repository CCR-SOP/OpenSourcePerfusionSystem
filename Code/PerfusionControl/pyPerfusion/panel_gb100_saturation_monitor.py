# -*- coding: utf-8 -*-
"""
@author: Allen Luna
Test app for integrating gas mixer with saturation monitor, and for displaying monitor data
"""
from enum import Enum
import wx
import logging
import pyPerfusion.utils as utils
import os
from pathlib import Path
from pyPerfusion.plotting_TSM_GB100 import TSMPanelPlotting, TSMPanelPlotLT, TSMSensorPlot
from pyHardware.pySaturationMonitor import TSMSerial
from pyHardware.pyGB100 import GB100
import pyPerfusion.PerfusionConfig as LP_CFG

class PlotFrame(Enum):
    FROM_START = 0
    LAST_30_SECONDS = 30_000
    LAST_MINUTE = 60_000
    Last_5_MINUTES = 300_000
    LAST_15_MINUTES = 900_000
    LAST_30_MINUTES = 1_800_000
    LAST_HOUR = 3_600_000

class TSMReadout(wx.Panel):
    def __init__(self, parent, label, unit):
        self._logger = logging.getLogger(__name__)
        super().__init__(parent, -1)
        self._parent = parent
        self._label = label
        self._unit = unit

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer_value = wx.BoxSizer(wx.HORIZONTAL)
        self.label_name = wx.StaticText(self, label=label)
        self.label_value = wx.StaticText(self, label='000')
        self.label_units = wx.StaticText(self, label=unit)
        self.__do_layout()

    def __do_layout(self):
        font = self.label_name.GetFont()
        font.SetPointSize(10)
        self.label_name.SetFont(font)
        font = self.label_value.GetFont()
        font.SetPointSize(15)
        self.label_value.SetFont(font)

        self.sizer.Add(self.label_name, wx.SizerFlags().CenterHorizontal())
        self.sizer_value.Add(self.label_value, wx.SizerFlags().CenterVertical())
        self.sizer_value.AddSpacer(10)
        self.sizer_value.Add(self.label_units, wx.SizerFlags().CenterVertical())
        self.sizer.Add(self.sizer_value, wx.SizerFlags().CenterHorizontal())

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.__plot_frame = PlotFrame.LAST_MINUTE

        LP_CFG.set_base(basepath='~/Documents/LPTEST')
        LP_CFG.update_stream_folder()
        self._logger = logging.getLogger(__name__)
        utils.setup_stream_logger(self._logger, logging.DEBUG)
        utils.configure_matplotlib_logging()

        self._mixer = GB100('GB100')
        self._mixer.open()
        LP_PATH = Path(os.path.expanduser('~')) / 'Documents/LPTEST/LiverPerfusion/data/Gas Mixer Stream'
        self._mixer.open_stream(LP_PATH)
        self._monitor = TSMSerial('CDI Monitor')
        self._monitor.open('COM5', 9600, 8, 'N', 1)
        LP_PATH = Path(os.path.expanduser('~')) / 'Documents/LPTEST/LiverPerfusion/data/CDI Stream'
        self._monitor.open_stream(LP_PATH)
        self._labels = {'Time': '', 'Arterial pH': 'units', 'Arterial pCO2': 'mmHg', 'Arterial pO2': 'mmHg', 'Arterial Temperature': 'C', 'Arterial Bicarbonate': 'mmol/L', 'Arterial BE': 'mmol/L', 'K': 'mmol/L', 'O2 Saturation': '%', 'Hct': '%', 'Hb': 'g/dL'}

        self.sizer_main = wx.BoxSizer(wx.HORIZONTAL)

        self.sizer_plot_grid = wx.GridSizer(cols=2, hgap=5, vgap=5)
        self.sizer_plots = []  # List of sizers, one for each plot set (big + small)
        self._plots_main = []  # List of TSMPanelPlotting objects; each associated w/a TSMSensorPlot object
        self._plots_lt = []  # List of TSMPanelPlotLT objects; each associated w/a TSMSensorPlot object

        for plot_name in ['Arterial pH', 'O2 Saturation', 'Arterial pO2', 'Arterial pCO2']:
            self.sizer_plots.append(self._add_lt(plot_name))

        self.sizer_readout = wx.GridSizer(cols=1)
        self.sizer_config = wx.BoxSizer(wx.VERTICAL)
        self.sizer_start_streams = wx.BoxSizer(wx.VERTICAL)
        self.choice_time = self._create_choice_time()
        self.label_choice_time = wx.StaticText(self, label='Display Window')
        self.btn_stream_GB100 = wx.Button(self, label='Start Gas Mixer')
        self.btn_stream_TSM = wx.Button(self, label='Start CDI Monitor')

        self._mixer.start_stream()

        self.__do_layout()
        self.__set_bindings()

        for plot in self._plots_main:
            plot.show_legend()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def _add_lt(self, plot_name):
        sizer = wx.BoxSizer(wx.VERTICAL)

        panel = TSMPanelPlotting(self)
        self._plots_main.append(panel)
        plotraw = TSMSensorPlot(plot_name, panel.axes)
        panel.add_plot(plotraw)
        sizer.Add(panel, 10, wx.ALL | wx.EXPAND, border=0)

        panel = TSMPanelPlotLT(self)
        self._plots_lt.append(panel)
        panel.plot_frame_ms = -1
        plotraw = TSMSensorPlot(plot_name, panel.axes)
        panel.add_plot(plotraw)
        sizer.Add(panel, 2, wx.ALL | wx.EXPAND, border=0)

        return sizer

    def _create_choice_time(self):
        parameters = [item.name for item in PlotFrame]
        choice = wx.Choice(self, choices=parameters)
        choice.SetStringSelection(self.__plot_frame.name)
        font = choice.GetFont()
        font.SetPointSize(12)
        choice.SetFont(font)
        return choice

    def __do_layout(self):
        for plot in self.sizer_plots:
            self.sizer_plot_grid.Add(plot, 1, wx.ALL | wx.EXPAND)

        self.sizer_main.Add(self.sizer_plot_grid, 1, wx.ALL | wx.EXPAND)

        self.readouts = []
        for label in self._labels:
            readout = TSMReadout(self, label, self._labels[label])
            self.readouts.append(readout)
            self.sizer_readout.Add(readout, 1, wx.ALL | wx.EXPAND, border=1)

        self.sizer_config.Add(self.label_choice_time, 1, wx.ALL | wx.ALIGN_CENTER)
        self.sizer_config.Add(self.choice_time, 1, wx.ALL)
        self.sizer_start_streams.Add(self.btn_stream_GB100, 1, wx.ALL)
        self.sizer_start_streams.AddSpacer(5)
        self.sizer_start_streams.Add(self.btn_stream_TSM, 1, wx.ALL)
        self.sizer_readout.AddSpacer(5)
        self.sizer_readout.Add(self.sizer_config, 1, wx.ALL)
        self.sizer_readout.AddSpacer(5)
        self.sizer_readout.Add(self.sizer_start_streams, 1, wx.ALL)
        self.sizer_main.Add(self.sizer_readout)
        self.SetSizer(self.sizer_main)

        self.Fit()
        self.Layout()
        self.Maximize(True)

        self.timer_update = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

    def __set_bindings(self):
        self.choice_time.Bind(wx.EVT_CHOICE, self._onchange_plotchoice)
        self.btn_stream_GB100.Bind(wx.EVT_TOGGLEBUTTON, self.OnGB100)
        self.btn_stream_TSM.Bind(wx.EVT_TOGGLEBUTTON, self.OnTSM)

    def _onchange_plotchoice(self, event):
        self.__plot_frame = PlotFrame[self.choice_time.GetStringSelection()]
        for plot in self._plots_main:
            plot.plot_frame_ms = self.__plot_frame.value

    def OnTimer(self, event):
        if event.GetId() == self.timer_update.GetId():
            self.update_plots()

    def OnGB100(self, event):
        label = self.btn_stream_GB100.GetLabel()
        if label == 'Start Gas Mixer':
            self.btn_stream_GB100.SetLabel('Stop Gas Mixer')
        elif label == 'Stop Gas Mixer':
            self.btn_stream_GB100.SetLabel('Start Gas Mixer')

    def OnTSM(self, event):
        label = self.btn_stream_TSM.GetLabel()
        if label == 'Start CDI Monitor':
            self.btn_stream_TSM.SetLabel('Stop CDI Monitor')
            self._monitor.start_stream()
        elif label == 'Stop CDI Monitor':
            self.btn_stream_TSM.SetLabel('Start CDI Monitor')
        self.timer_update.Start(6000, wx.TIMER_CONTINUOUS)

    def update_plots(self):
        data = self._monitor.get_parsed_data()
        data_list = list(data)
        time = data_list[0]
        for num in range(1, 11):
            self.readouts[num].label_value.SetLabel(data_list[num])
        self._plots_main[0].plot(data_list[1], time)
        self._plots_main[1].plot(data_list[8], time)
        self._plots_main[2].plot(data_list[3], time)
        self._plots_main[3].plot(data_list[2], time)
        self._plots_lt[0].plot(data_list[1], time)
        self._plots_lt[1].plot(data_list[8], time)
        self._plots_lt[2].plot(data_list[3], time)
        self._plots_lt[3].plot(data_list[2], time)

    def OnClose(self, evt):
        self._monitor.stop_stream()
        self._mixer.stop_stream()
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

if __name__ == "__main__":
    app = MyTestApp(0)
    app.MainLoop()
