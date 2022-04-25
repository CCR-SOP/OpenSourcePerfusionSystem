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
from pyPerfusion.plotting import TSMPanelPlotting, TSMPanelPlotLT, TSMSensorPlot
from pyHardware.pySaturationMonitor import TSMSerial
from pyHardware.pyGB100 import GB100
import pyPerfusion.PerfusionConfig as LP_CFG

class PlotFrame(Enum):
    FROM_START = 0
    LAST_30_SECONDS = 0.5
    LAST_MINUTE = 1
    Last_5_MINUTES = 5
    LAST_15_MINUTES = 15
    LAST_30_MINUTES = 30
    LAST_HOUR = 60

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
        self._monitor.open('COM17', 9600, 8, 'N', 1)
        LP_PATH = Path(os.path.expanduser('~')) / 'Documents/LPTEST/LiverPerfusion/data/CDI Stream'
        self._monitor.open_stream(LP_PATH)
        self._labels = {'Time': '', 'Arterial pH': 'units', 'Arterial pCO2': 'mmHg', 'Arterial pO2': 'mmHg', 'Arterial Temperature': 'C', 'Arterial Bicarbonate': 'mmol/L', 'Arterial BE': 'mmol/L', 'K': 'mmol/L', 'O2 Saturation': '%', 'Hct': '%', 'Hb': 'g/dL'}

        self.sizer_main = wx.BoxSizer(wx.HORIZONTAL)  # Main sizer
        self.sizer_plot_grid = wx.GridSizer(cols=2, hgap=5, vgap=5)  # Grid which will be added to main sizer
        self.sizer_plots = []  # List of sizers, one for each plot set (big + small)
        self._plots_main = []  # List of TSMPanelPlotting objects; each associated w/a TSMSensorPlot object (which is also associated w/a TSMPanelPlotLT object)
        self._plots_lt = []  # List of TSMPanelPlotLT objects; each associated w/a TSMSensorPlot object (which is also associated w/a TSMPanelPlotting object)

        for plot_name in ['Arterial pH', 'O2 Saturation', 'Arterial pO2', 'Arterial pCO2']:
            self.sizer_plots.append(self._add_lt(plot_name))

        self.sizer_readout = wx.GridSizer(cols=1)  # Size for all readouts, buttons, etc.
        self.sizer_config = wx.BoxSizer(wx.VERTICAL)
        self.sizer_gas_config = wx.BoxSizer(wx.VERTICAL)
        self.sizer_balance = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_gas1_choice = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_gas1_percentage = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_gas2_choice = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_gas2_percentage = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_flow = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_start_streams = wx.BoxSizer(wx.VERTICAL)
        self.choice_time = self._create_choice_time()
        self.label_choice_time = wx.StaticText(self, label='Display Window')

        parameters = ['Air', 'Nitrogen', 'Oxygen', 'Carbon Dioxide']
        self.choice_gas1 = wx.Choice(self, choices=parameters)
        self.choice_gas1.SetStringSelection(parameters[2])
        self.choice_gas2 = wx.Choice(self, choices=parameters)
        self.choice_gas2.SetStringSelection(parameters[1])

        parameters = ['1', '2']
        self.choice_balance = wx.Choice(self, choices=parameters)
        self.choice_balance.SetStringSelection(parameters[0])

        self.label_balance = wx.StaticText(self, label='Balance Channel:')
        self.label_gas1 = wx.StaticText(self, label='Channel 1 Gas:')
        self.label_gas1_percentage = wx.StaticText(self, label='Channel 1 Percentage:')
        self.spin_gas1_percentage = wx.SpinCtrlDouble(self, min=0, max=100, initial=90, inc=1)
        self.label_gas2 = wx.StaticText(self, label='Channel 2 Gas:')
        self.label_gas2_percentage = wx.StaticText(self, label='Channel 2 Percentage:')
        self.spin_gas2_percentage = wx.SpinCtrlDouble(self, min=0, max=100, initial=10, inc=1)
        self.label_total_flow = wx.StaticText(self, label='Total Flow:')
        self.spin_total_flow = wx.SpinCtrlDouble(self, min=0, max=400, initial=100, inc=1)

        self.btn_stream_GB100 = wx.ToggleButton(self, label='Start Gas Mixer')
        self.btn_stream_TSM = wx.ToggleButton(self, label='Start CDI Monitor')

        self.__do_layout()
        self.__set_bindings()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def _add_lt(self, plot_name):  # Adds a large and small plot for each sizer
        sizer = wx.BoxSizer(wx.VERTICAL)

        panel = TSMPanelPlotting(self)
        self._plots_main.append(panel)
        plotraw = TSMSensorPlot(plot_name, panel.axes, self._labels[plot_name])  # Adds sensor to plot
        panel.add_plot(plotraw)
        sizer.Add(panel, 9, wx.ALL | wx.EXPAND, border=0)

        panel = TSMPanelPlotLT(self)
        self._plots_lt.append(panel)
        plotraw = TSMSensorPlot('', panel.axes, '')
        panel.add_plot(plotraw)
        sizer.Add(panel, 2, wx.ALL | wx.EXPAND, border=0)

        return sizer

    def _create_choice_time(self):
        parameters = [item.name for item in PlotFrame]
        choice = wx.Choice(self, choices=parameters)
        choice.SetStringSelection(self.__plot_frame.name)
        for panel in self._plots_main:
            panel._x_range_minutes = PlotFrame.LAST_MINUTE.value
        font = choice.GetFont()
        font.SetPointSize(12)
        choice.SetFont(font)
        return choice

    def __do_layout(self):
        for plot in self.sizer_plots:
            self.sizer_plot_grid.Add(plot, 1, wx.ALL | wx.EXPAND)  # Adding each large/small graph panel to grid

        self.sizer_main.Add(self.sizer_plot_grid, 1, wx.ALL | wx.EXPAND)  # Adding grid to main sizer

        self.readouts = []
        for label in self._labels:
            if label != 'Time':
                readout = TSMReadout(self, label, self._labels[label])
                self.readouts.append(readout)
                self.sizer_readout.Add(readout, 1, wx.ALL | wx.EXPAND, border=1)  # Adding each readout panel to main readout panel

        self.sizer_config.Add(self.label_choice_time, 1, wx.ALL | wx.ALIGN_CENTER)
        self.sizer_config.Add(self.choice_time, 1, wx.ALL | wx.ALIGN_CENTER)

        self.sizer_balance.Add(self.label_balance)
        self.sizer_balance.AddSpacer(3)
        self.sizer_balance.Add(self.choice_balance)
        self.sizer_gas1_choice.Add(self.label_gas1)
        self.sizer_gas1_choice.AddSpacer(3)
        self.sizer_gas1_choice.Add(self.choice_gas1)
        self.sizer_gas1_percentage.Add(self.label_gas1_percentage)
        self.sizer_gas1_percentage.AddSpacer(3)
        self.sizer_gas1_percentage.Add(self.spin_gas1_percentage)
        self.sizer_gas2_choice.Add(self.label_gas2)
        self.sizer_gas2_choice.AddSpacer(3)
        self.sizer_gas2_choice.Add(self.choice_gas2)
        self.sizer_gas2_percentage.Add(self.label_gas2_percentage)
        self.sizer_gas2_percentage.AddSpacer(3)
        self.sizer_gas2_percentage.Add(self.spin_gas2_percentage)
        self.sizer_flow.Add(self.label_total_flow)
        self.sizer_flow.AddSpacer(3)
        self.sizer_flow.Add(self.spin_total_flow)
        self.sizer_gas_config.Add(self.sizer_balance)
        self.sizer_gas_config.Add(self.sizer_gas1_choice)
        self.sizer_gas_config.Add(self.sizer_gas1_percentage)
        self.sizer_gas_config.Add(self.sizer_gas2_choice)
        self.sizer_gas_config.Add(self.sizer_gas2_percentage)
        self.sizer_gas_config.Add(self.sizer_flow)

        self.sizer_start_streams.Add(self.btn_stream_GB100, 1, wx.ALL | wx.EXPAND, border=1)
        self.sizer_start_streams.AddSpacer(5)
        self.sizer_start_streams.Add(self.btn_stream_TSM, 1, wx.ALL | wx.EXPAND, border=1)

        self.sizer_readout.Add(self.sizer_config, 1, wx.ALL | wx.ALIGN_CENTER)  # Adding buttons and such to readout panel, which already has individual readout panels
        self.sizer_readout.Add(self.sizer_gas_config, 1, wx.ALL)
        self.sizer_readout.AddSpacer(2)
        self.sizer_readout.Add(self.sizer_start_streams, 1, wx.ALL | wx.EXPAND, border=1)
        self.sizer_main.Add(self.sizer_readout)  # Adding readout sizer to main sizer
        self.SetSizer(self.sizer_main)

        self.Fit()
        self.Layout()
        self.Maximize(True)

        self.timer_update_CDI = wx.Timer(self, id=1)
        self.Bind(wx.EVT_TIMER, self.OnCDITimer, id=1)

        self.timer_update_GB100 = wx.Timer(self, id=2)
        self.Bind(wx.EVT_TIMER, self.OnGB100Timer, id=2)

    def __set_bindings(self):
        self.choice_time.Bind(wx.EVT_CHOICE, self._onchange_plotchoice)
        self.btn_stream_GB100.Bind(wx.EVT_TOGGLEBUTTON, self.OnGB100)
        self.btn_stream_TSM.Bind(wx.EVT_TOGGLEBUTTON, self.OnTSM)

    def _onchange_plotchoice(self, event):
        choice_time = PlotFrame[self.choice_time.GetStringSelection()]
        for plot in self._plots_main:
            plot._x_range_minutes = choice_time.value

    def OnGB100(self, event):
        label = self.btn_stream_GB100.GetLabel()
        balance = float(self.choice_balance.GetStringSelection())
        if label == 'Start Gas Mixer':
            self.btn_stream_GB100.SetLabel('Stop Gas Mixer')
            self._mixer.start_stream()
            self.choice_balance.Enable(False)
            self.choice_gas1.Enable(False)
            self.spin_gas1_percentage.Enable(False)
            self.choice_gas2.Enable(False)
            self.spin_gas2_percentage.Enable(False)
            self.spin_total_flow.Enable(False)
            gas1 = self._mixer.get_gas_ID((self.choice_gas1.GetStringSelection()))
            gas2 = self._mixer.get_gas_ID((self.choice_gas2.GetStringSelection()))
            gas1_percentage = self.spin_gas1_percentage.GetValue()
            gas2_percentage = self.spin_gas2_percentage.GetValue()
            flow = int(self.spin_total_flow.GetValue())
            self._mixer.change_gas_mix(gas1_percentage, gas2_percentage, flow, 1, gas1=gas1, gas2=gas2, balance_channel=balance)
            self.timer_update_GB100.Start(10000, wx.TIMER_CONTINUOUS)
        elif label == 'Stop Gas Mixer':
            self.btn_stream_GB100.SetLabel('Start Gas Mixer')
            self.timer_update_GB100.Stop()
            gas1_percentage = self._mixer.get_channel_percent_value(1)
            gas2_percentage = self._mixer.get_channel_percent_value(2)
            flow = self._mixer.get_mainboard_total_flow()
            self._mixer.change_gas_mix(gas1_percentage, gas2_percentage, flow, 0)
            self._mixer.stop_stream()
            self.choice_balance.Enable(True)
            self.choice_gas1.Enable(True)
            self.spin_gas1_percentage.Enable(True)
            self.choice_gas2.Enable(True)
            self.spin_gas2_percentage.Enable(True)
            self.spin_total_flow.Enable(True)
            self.spin_gas1_percentage.SetValue(gas1_percentage)
            self.spin_gas2_percentage.SetValue(gas2_percentage)
            self.spin_total_flow.SetValue(flow)

    def OnTSM(self, event):
        label = self.btn_stream_TSM.GetLabel()
        if label == 'Start CDI Monitor':
            self.btn_stream_TSM.SetLabel('Stop CDI Monitor')
            self._monitor.start_stream()
            self.timer_update_CDI.Start(6000, wx.TIMER_CONTINUOUS)
        elif label == 'Stop CDI Monitor':
            self.btn_stream_TSM.SetLabel('Start CDI Monitor')
            self._monitor.stop_stream()
            self.timer_update_CDI.Stop()

    def OnGB100Timer(self, event):
        if event.GetId() == self.timer_update_GB100.GetId():
            self.update_gas_mix()

    def OnCDITimer(self, event):
        if event.GetId() == self.timer_update_CDI.GetId():
            self.update_plots()

    def update_gas_mix(self):
        values = self.get_label_values()
        pH = values[0]
        pCO2 = values[1]
        sO2 = values[3]
        current_flow = self._mixer.get_mainboard_total_flow()
        new_gas_flow = current_flow
        new_channel_1_percentage = self._mixer.get_channel_percent_value(1)
        new_channel_2_percentage = self._mixer.get_channel_percent_value(2)
        channel1_gas_ID = self._mixer.get_channel_id_gas(1)
        if pCO2 and self._monitor._TSMSerial__thread_streaming: # Check if new data is being streamed by the CDI; if not, don't update gas mix
            if pCO2 > 45:
                new_gas_flow = current_flow + 4
            elif pCO2 < 25:
                new_gas_flow = current_flow - 4
        if pH and self._monitor._TSMSerial__thread_streaming:
            if pH < 7.35:
                new_gas_flow = new_gas_flow + 6
            elif pH > 7.45:
                new_gas_flow = new_gas_flow - 6
        if sO2 and self._monitor._TSMSerial__thread_streaming:
            if sO2 > 87:
                if channel1_gas_ID == 2:
                    new_channel_1_percentage = self._mixer.get_channel_percent_value(1) + 1
                    new_channel_2_percentage = self._mixer.get_channel_percent_value(2) - 1
                elif channel1_gas_ID == 3:
                    new_channel_1_percentage = self._mixer.get_channel_percent_value(1) - 1
                    new_channel_2_percentage = self._mixer.get_channel_percent_value(2) + 1
            elif sO2 < 80:
                if channel1_gas_ID == 2:
                    new_channel_1_percentage = self._mixer.get_channel_percent_value(1) - 1
                    new_channel_2_percentage = self._mixer.get_channel_percent_value(2) + 1
                elif channel1_gas_ID == 3:
                    new_channel_1_percentage = self._mixer.get_channel_percent_value(1) + 1
                    new_channel_2_percentage = self._mixer.get_channel_percent_value(2) - 1
        if new_gas_flow == current_flow and new_channel_1_percentage == self._mixer.get_channel_percent_value(1) and new_channel_2_percentage == self._mixer.get_channel_percent_value(2):
            return
        else:
            self._mixer.change_gas_mix(new_channel_1_percentage, new_channel_2_percentage, new_gas_flow, 1)

    def get_label_values(self):
        str_pH = self.readouts[0].label_value.GetLabel()
        str_pCO2 = self.readouts[1].label_value.GetLabel()
        str_pO2 = self.readouts[2].label_value.GetLabel()
        str_sO2 = self.readouts[7].label_value.GetLabel()
        strings = [str_pH, str_pCO2, str_pO2, str_sO2]
        values = []
        for item in strings:
            if item == '000' or item == ' ---' or item == ' -- ' or item == ' -.-':
                values.append([])
            else:
                values.append(float(item))
        return values

    def update_plots(self):
        data = self._monitor.get_parsed_data()
        data_list = list(data)
        time = data_list[0] / 60000  # Gives time in minutes
        for num in range(1, len(data_list)):  # Updating readouts
            self.readouts[num-1].label_value.SetLabel(data_list[num])
        values = self.get_label_values()
        if values[0]:
            self._plots_main[0].plot(data_list[1], time)
            self._plots_lt[0].plot(data_list[1], time)
        if values[1]:
            self._plots_main[3].plot(data_list[2], time)
            self._plots_lt[3].plot(data_list[2], time)
        if values[2]:
            self._plots_main[2].plot(data_list[3], time)
            self._plots_lt[2].plot(data_list[3], time)
        if values[3]:
            self._plots_main[1].plot(data_list[8], time)
            self._plots_lt[1].plot(data_list[8], time)

    def OnClose(self, evt):
        self._monitor.stop_stream()
        self._monitor.close_stream()
        if self._mixer.get_working_status():
            gas1_percentage = self._mixer.get_channel_percent_value(1)
            gas2_percentage = self._mixer.get_channel_percent_value(2)
            flow = self._mixer.get_mainboard_total_flow()
            self._mixer.change_gas_mix(gas1_percentage,  gas2_percentage, flow, 0)
        self._mixer.stop_stream()
        self._mixer.close_stream()
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
