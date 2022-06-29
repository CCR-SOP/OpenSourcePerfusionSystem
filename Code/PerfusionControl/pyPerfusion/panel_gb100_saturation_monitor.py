# -*- coding: utf-8 -*-
"""
@author: Allen Luna
Panel for integrating venous gas mixer with saturation monitor, and for displaying monitor data
"""
from enum import Enum
import wx
import logging
import pyPerfusion.utils as utils
from pyPerfusion.plotting import PanelPlotting, TSMDexPanelPlotting, TSMDexPanelPlotLT, TSMDexSensorPlot, SensorPlot
from pyHardware.pySaturationMonitor import TSMSerial
from pyHardware.pyGB100 import GB100
from pyHardware.pyDialysatePumps import DialysatePumps
import pyPerfusion.PerfusionConfig as LP_CFG
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyHardware.pyAI import AIDeviceException
from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.FileStrategy import StreamToFile
from pyHardware.pyAO_NIDAQ import NIDAQ_AO

class PlotFrame(Enum):
    FROM_START = 0
    LAST_30_SECONDS = 0.5
    LAST_MINUTE = 1
    Last_5_MINUTES = 5
    LAST_15_MINUTES = 15
    LAST_30_MINUTES = 30
    LAST_HOUR = 60

class Readout(wx.Panel):
    def __init__(self, parent, label, unit):
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

class PanelGB100CDIPresens(wx.Panel):
    def __init__(self, parent, arterial_mixer, venous_mixer, monitor, sensor, inflow_pump, outflow_pump, pump_streaming, cdi_labels, cdi_graphs_ranges, gas_parameters, name):
        self._logger = logging.getLogger(__name__)
        utils.setup_stream_logger(self._logger, logging.DEBUG)
        utils.configure_matplotlib_logging()
        self.parent = parent
        self._arterial_mixer = arterial_mixer
        self._venous_mixer = venous_mixer
        self._monitor = monitor
        self._sensor = sensor
        self._inflow_pump = inflow_pump
        self._outflow_pump = outflow_pump
        self._pump_streaming = pump_streaming
        self._cdi_labels = cdi_labels
        self._cdi_graphs_ranges = cdi_graphs_ranges
        self._gas_parameters = gas_parameters
        self._name = name
        self.__plot_frame = PlotFrame.LAST_MINUTE

        section = LP_CFG.get_hwcfg_section(self._sensor.name)
        self.pO2lowerrange = float(section['lowerrange'])
        self.pO2upperrange = float(section['upperrange'])

        section = LP_CFG.get_hwcfg_section(self._monitor.name)
        self.phlower = float(section['phlower'])
        self.phupper = float(section['phupper'])
        self.saturationlower = float(section['saturationlower'])
        self.saturationupper = float(section['saturationupper'])
        self.co2lower = float(section['co2lower'])
        self.co2upper = float(section['co2upper'])

        section = LP_CFG.get_hwcfg_section(self._inflow_pump.name)
        dev = section['Device']
        line = section['LineName']
        self._inflow_pump.open(period_ms=1000, dev=dev, line=line)
        self._inflow_pump.set_dc(0)

        section = LP_CFG.get_hwcfg_section(self._outflow_pump.name)
        dev = section['Device']
        line = section['LineName']
        self._outflow_pump.open(period_ms=1000, dev=dev, line=line)
        self._outflow_pump.set_dc(0)

        self.cdi_graphs_values = {}
        for key in self._cdi_graphs_ranges.keys():
            self.cdi_graphs_values[key] = []

        wx.Panel.__init__(self, parent, -1)

        self.sizer_main = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_plot_grid = wx.GridSizer(cols=2, hgap=5, vgap=5)
        self.sizer_plots = []
        self._plots_main = []
        self._plots_lt = []

        for key, value in self._cdi_graphs_ranges.items():
            self.sizer_plots.append(self._add_lt_cdi(key, value))
        self.sizer_plots.append(self._add_lt_presens())

        self.sizer_readout = wx.GridSizer(cols=1)
        self.sizer_config = wx.BoxSizer(wx.VERTICAL)
        self.sizer_start_gas_mixers = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_start_cdi_presens_sensors = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_start_automated_dialysis = wx.BoxSizer(wx.HORIZONTAL)
        self.choice_time = self._create_choice_time()
        self.label_choice_time = wx.StaticText(self, label='Display Window')

        section = LP_CFG.get_hwcfg_section('Arterial Gas Mixer')
        channel1perc = section['channel1perc']
        channel2perc = section['channel2perc']
        totalflow = section['totalflow']

        self.sizer_arterial_gas_config = wx.BoxSizer(wx.VERTICAL)
        self.sizer_arterial_gas1_percentage = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_arterial_gas2_percentage = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_arterial_flow = wx.BoxSizer(wx.HORIZONTAL)

        self.arterial_label_gas1_percentage = wx.StaticText(self, label='Channel 1 Percentage (A):')
        self.arterial_spin_gas1_percentage = wx.SpinCtrlDouble(self, min=0, max=100, initial=int(channel1perc), inc=1)
        self.arterial_label_gas2_percentage = wx.StaticText(self, label='Channel 2 Percentage (A):')
        self.arterial_spin_gas2_percentage = wx.SpinCtrlDouble(self, min=0, max=100, initial=int(channel2perc), inc=1)
        self.arterial_label_total_flow = wx.StaticText(self, label='Total Flow (A):')
        self.arterial_spin_total_flow = wx.SpinCtrlDouble(self, min=0, max=400, initial=int(totalflow), inc=1)

        self.arterial_btn_stream_GB100 = wx.ToggleButton(self, label='Start Arterial Gas Mixer')

        section = LP_CFG.get_hwcfg_section('Venous Gas Mixer')
        channel1perc = section['channel1perc']
        channel2perc = section['channel2perc']
        totalflow = section['totalflow']

        self.sizer_venous_gas_config = wx.BoxSizer(wx.VERTICAL)
        self.sizer_venous_gas1_percentage = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_venous_gas2_percentage = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_venous_flow = wx.BoxSizer(wx.HORIZONTAL)

        self.venous_label_gas1_percentage = wx.StaticText(self, label='Channel 1 Percentage (V):')
        self.venous_spin_gas1_percentage = wx.SpinCtrlDouble(self, min=0, max=100, initial=int(channel1perc), inc=1)
        self.venous_label_gas2_percentage = wx.StaticText(self, label='Channel 2 Percentage (V):')
        self.venous_spin_gas2_percentage = wx.SpinCtrlDouble(self, min=0, max=100, initial=int(channel2perc), inc=1)
        self.venous_label_total_flow = wx.StaticText(self, label='Total Flow (V):')
        self.venous_spin_total_flow = wx.SpinCtrlDouble(self, min=0, max=400, initial=int(totalflow), inc=1)

        self.venous_btn_stream_GB100 = wx.ToggleButton(self, label='Start Venous Gas Mixer')

        self.btn_stream_TSM = wx.ToggleButton(self, label='Start CDI Monitor')
        self.btn_stream_presens = wx.ToggleButton(self, label='Start Arterial pO2 Sensor')

        section = LP_CFG.get_hwcfg_section(self._inflow_pump.name)
        initial_rate_inflow = float(section['initialrate'])
        self.upper_hct_limit = float(section['hctlimit'])
        self.upper_k_limit = float(section['kupperlimit'])
        self.lower_k_limit = float(section['klowerlimit'])
        self.upper_dialysis_limit = float(section['upperdialysislimit'])
        self.lower_dialysis_limit = float(section['lowerdialysislimit'])
        section = LP_CFG.get_hwcfg_section(self._outflow_pump.name)
        initial_rate_outflow = float(section['initialrate'])
        self.lower_hct_limit = float(section['hctlimit'])

        self.label_inflow_pump_rate = wx.StaticText(self, label='Inflow (ml/min):')
        self.spin_inflow_pump_rate = wx.SpinCtrlDouble(self, min=0, max=100, initial=initial_rate_inflow, inc=0.1)
        self.label_outflow_pump_rate = wx.StaticText(self, label='Outflow (ml/min):')
        self.spin_outflow_pump_rate = wx.SpinCtrlDouble(self, min=0, max=100, initial=initial_rate_outflow, inc=0.1)
        self.btn_automated_dialysis = wx.ToggleButton(self, label='Start Automated Dialysis')

        self.__do_layout()
        self.__set_bindings()

    def _add_lt_cdi(self, plot_name, valid_range):
        sizer = wx.BoxSizer(wx.VERTICAL)

        panel = TSMDexPanelPlotting(self)
        self._plots_main.append(panel)
        plotraw = TSMDexSensorPlot(plot_name, panel.axes, self._cdi_labels[plot_name], valid_range)
        panel.add_plot(plotraw)
        sizer.Add(panel, 9, wx.ALL | wx.EXPAND, border=0)

        panel = TSMDexPanelPlotLT(self)
        self._plots_lt.append(panel)
        plotraw = TSMDexSensorPlot('', panel.axes, '', valid_range)
        panel.add_plot(plotraw)
        sizer.Add(panel, 2, wx.ALL | wx.EXPAND, border=0)

        return sizer

    def _add_lt_presens(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        panel = PanelPlotting(self)
        self._plots_main.append(panel)
        plotraw = SensorPlot(self._sensor, panel.axes)
        plotraw.set_strategy(self._sensor.get_file_strategy('StreamRaw'))
        panel.add_plot(plotraw)
        sizer.Add(panel, 9, wx.ALL | wx.EXPAND, border=0)

        return sizer

    def _create_choice_time(self):
        parameters = [item.name for item in PlotFrame]
        choice = wx.Choice(self, choices=parameters)
        choice.SetStringSelection(self.__plot_frame.name)
        for panel in self._plots_main:
            if type(panel) == TSMDexPanelPlotting:
                panel._x_range_minutes = PlotFrame.LAST_MINUTE.value
            else:
                pass
        font = choice.GetFont()
        font.SetPointSize(12)
        choice.SetFont(font)
        return choice

    def __do_layout(self):
        for plot in self.sizer_plots:
            self.sizer_plot_grid.Add(plot, 1, wx.ALL | wx.EXPAND)

        self.sizer_main.Add(self.sizer_plot_grid, 1, wx.ALL | wx.EXPAND)

        self.readouts = {}
        for key, value in self._cdi_labels.items():
            if key != 'Time':
                readout = Readout(self, key, value)
                self.readouts[key] = readout
                self.sizer_readout.Add(readout, 1, wx.ALL | wx.EXPAND, border=1)

        self.sizer_config.Add(self.label_choice_time, 1, wx.ALL | wx.ALIGN_CENTER)
        self.sizer_config.Add(self.choice_time, 1, wx.ALL | wx.ALIGN_CENTER)

        self.sizer_arterial_gas1_percentage.Add(self.arterial_label_gas1_percentage)
        self.sizer_arterial_gas1_percentage.AddSpacer(10)
        self.sizer_arterial_gas1_percentage.Add(self.arterial_spin_gas1_percentage)
        self.sizer_arterial_gas2_percentage.Add(self.arterial_label_gas2_percentage)
        self.sizer_arterial_gas2_percentage.AddSpacer(10)
        self.sizer_arterial_gas2_percentage.Add(self.arterial_spin_gas2_percentage)
        self.sizer_arterial_flow.Add(self.arterial_label_total_flow)
        self.sizer_arterial_flow.AddSpacer(10)
        self.sizer_arterial_flow.Add(self.arterial_spin_total_flow)
        self.sizer_arterial_gas_config.Add(self.sizer_arterial_gas1_percentage)
        self.sizer_arterial_gas_config.Add(self.sizer_arterial_gas2_percentage)
        self.sizer_arterial_gas_config.Add(self.sizer_arterial_flow)

        self.sizer_venous_gas1_percentage.Add(self.venous_label_gas1_percentage)
        self.sizer_venous_gas1_percentage.AddSpacer(10)
        self.sizer_venous_gas1_percentage.Add(self.venous_spin_gas1_percentage)
        self.sizer_venous_gas2_percentage.Add(self.venous_label_gas2_percentage)
        self.sizer_venous_gas2_percentage.AddSpacer(10)
        self.sizer_venous_gas2_percentage.Add(self.venous_spin_gas2_percentage)
        self.sizer_venous_flow.Add(self.venous_label_total_flow)
        self.sizer_venous_flow.AddSpacer(10)
        self.sizer_venous_flow.Add(self.venous_spin_total_flow)
        self.sizer_venous_gas_config.Add(self.sizer_venous_gas1_percentage)
        self.sizer_venous_gas_config.Add(self.sizer_venous_gas2_percentage)
        self.sizer_venous_gas_config.Add(self.sizer_venous_flow)

        self.sizer_start_gas_mixers.Add(self.arterial_btn_stream_GB100, 1, wx.ALL | wx.EXPAND, border=1)
        self.sizer_start_gas_mixers.AddSpacer(1)
        self.sizer_start_gas_mixers.Add(self.venous_btn_stream_GB100, 1, wx.ALL | wx.EXPAND, border=1)
        self.sizer_start_cdi_presens_sensors.Add(self.btn_stream_TSM, 1, wx.ALL | wx.EXPAND, border=1)
        self.sizer_start_cdi_presens_sensors.AddSpacer(1)
        self.sizer_start_cdi_presens_sensors.Add(self.btn_stream_presens, 1, wx.ALL | wx.EXPAND, border=1)
        self.sizer_start_automated_dialysis.Add(self.label_inflow_pump_rate)
        self.sizer_start_automated_dialysis.Add(self.spin_inflow_pump_rate)
        self.sizer_start_automated_dialysis.Add(self.label_outflow_pump_rate)
        self.sizer_start_automated_dialysis.Add(self.spin_outflow_pump_rate)
        self.sizer_start_automated_dialysis.Add(self.btn_automated_dialysis)

        self.sizer_readout.Add(self.sizer_config, 1, wx.ALL | wx.ALIGN_CENTER)
        self.sizer_readout.AddSpacer(10)
        self.sizer_readout.Add(self.sizer_arterial_gas_config, 1, wx.ALL)
        self.sizer_readout.AddSpacer(10)
        self.sizer_readout.Add(self.sizer_venous_gas_config, 1, wx.ALL)
        self.sizer_readout.AddSpacer(10)
        self.sizer_readout.Add(self.sizer_start_gas_mixers, 1, wx.ALL | wx.EXPAND, border=1)
        self.sizer_readout.Add(self.sizer_start_cdi_presens_sensors, 1, wx.ALL | wx.EXPAND, border=1)
        self.sizer_readout.AddSpacer(10)
        self.sizer_readout.Add(self.sizer_start_automated_dialysis, 1, wx.ALL | wx.EXPAND, border=1)
        self.sizer_main.Add(self.sizer_readout)
        self.SetSizer(self.sizer_main)

        self.Fit()
        self.Layout()

        self.timer_update_CDI = wx.Timer(self, id=1)
        self.Bind(wx.EVT_TIMER, self.OnCDITimer, id=1)

        self.timer_update_arterial_GB100 = wx.Timer(self, id=2)
        self.Bind(wx.EVT_TIMER, self.OnArterialGB100Timer, id=2)

        self.timer_update_venous_GB100 = wx.Timer(self, id=3)
        self.Bind(wx.EVT_TIMER, self.OnVenousGB100Timer, id=3)

        self.timer_update_dialysis = wx.Timer(self, id=4)
        self.Bind(wx.EVT_TIMER, self.OnDialysisTimer, id=4)

    def __set_bindings(self):
        self.choice_time.Bind(wx.EVT_CHOICE, self._onchange_plotchoice)
        self.arterial_btn_stream_GB100.Bind(wx.EVT_TOGGLEBUTTON, self.OnArterialGB100)
        self.venous_btn_stream_GB100.Bind(wx.EVT_TOGGLEBUTTON, self.OnVenousGB100)
        self.btn_stream_TSM.Bind(wx.EVT_TOGGLEBUTTON, self.OnTSM)
        self.btn_stream_presens.Bind(wx.EVT_TOGGLEBUTTON, self.OnPresens)
        self.btn_automated_dialysis.Bind(wx.EVT_TOGGLEBUTTON, self.OnDialysis)

    def _onchange_plotchoice(self, event):
        choice_time = PlotFrame[self.choice_time.GetStringSelection()]
        for plot in self._plots_main:
            if type(plot) == TSMDexPanelPlotting:
                plot._x_range_minutes = choice_time.value
            else:
                pass

    def OnArterialGB100(self, event):
        label = self.arterial_btn_stream_GB100.GetLabel()
        if label == 'Start Arterial Gas Mixer':
            self.arterial_btn_stream_GB100.SetLabel('Stop Arterial Gas Mixer')
            dlg = wx.SingleChoiceDialog(self, 'Choose Arterial Mixer Balance Channel', 'Balance Channel', ['1', '2'])
            if dlg.ShowModal() == wx.ID_OK:
                arterialchoicebalance = dlg.GetStringSelection()
            dlg.Destroy()
            dlg = wx.SingleChoiceDialog(self, 'Choose Arterial Mixer Channel 1 Gas', 'Channel 1 Gas', self._gas_parameters)
            if dlg.ShowModal() == wx.ID_OK:
                arterialchoicegas1 = dlg.GetStringSelection()
            dlg.Destroy()
            dlg = wx.SingleChoiceDialog(self, 'Choose Arterial Mixer Channel 2 Gas', 'Channel 2 Gas', self._gas_parameters)
            if dlg.ShowModal() == wx.ID_OK:
                arterialchoicegas2 = dlg.GetStringSelection()
            dlg.Destroy()
            self._arterial_mixer.start_stream()
            self.arterial_spin_gas1_percentage.Enable(False)
            self.arterial_spin_gas2_percentage.Enable(False)
            self.arterial_spin_total_flow.Enable(False)
            gas1 = self._arterial_mixer.get_gas_ID(arterialchoicegas1)
            gas2 = self._arterial_mixer.get_gas_ID(arterialchoicegas2)
            gas1_percentage = self.arterial_spin_gas1_percentage.GetValue()
            gas2_percentage = self.arterial_spin_gas2_percentage.GetValue()
            flow = int(self.arterial_spin_total_flow.GetValue())
            balance = float(arterialchoicebalance)
            self._arterial_mixer.change_gas_mix(gas1_percentage, gas2_percentage, flow, 1, gas1=gas1, gas2=gas2, balance_channel=balance)
            self.timer_update_arterial_GB100.Start(60000, wx.TIMER_CONTINUOUS)
        elif label == 'Stop Arterial Gas Mixer':
            self.timer_update_arterial_GB100.Stop()
            self.arterial_btn_stream_GB100.SetLabel('Start Arterial Gas Mixer')
            gas1_percentage = self._arterial_mixer.get_channel_percent_value(1)
            gas2_percentage = self._arterial_mixer.get_channel_percent_value(2)
            flow = self._arterial_mixer.get_mainboard_total_flow()
            self._arterial_mixer.change_gas_mix(gas1_percentage, gas2_percentage, flow, 0)
            self._arterial_mixer.stop_stream()
            self.arterial_spin_gas1_percentage.Enable(True)
            self.arterial_spin_gas2_percentage.Enable(True)
            self.arterial_spin_total_flow.Enable(True)
            self.arterial_spin_gas1_percentage.SetValue(gas1_percentage)
            self.arterial_spin_gas2_percentage.SetValue(gas2_percentage)
            self.arterial_spin_total_flow.SetValue(flow)

    def OnVenousGB100(self, event):
        label = self.venous_btn_stream_GB100.GetLabel()
        if label == 'Start Venous Gas Mixer':
            self.venous_btn_stream_GB100.SetLabel('Stop Venous Gas Mixer')
            dlg = wx.SingleChoiceDialog(self, 'Choose Venous Mixer Balance Channel', 'Balance Channel', ['1', '2'])
            if dlg.ShowModal() == wx.ID_OK:
                venouschoicebalance = dlg.GetStringSelection()
            dlg.Destroy()
            dlg = wx.SingleChoiceDialog(self, 'Choose Venous Mixer Channel 1 Gas', 'Channel 1 Gas', self._gas_parameters)
            if dlg.ShowModal() == wx.ID_OK:
                venouschoicegas1 = dlg.GetStringSelection()
            dlg.Destroy()
            dlg = wx.SingleChoiceDialog(self, 'Choose Venous Mixer Channel 2 Gas', 'Channel 2 Gas', self._gas_parameters)
            if dlg.ShowModal() == wx.ID_OK:
                venouschoicegas2 = dlg.GetStringSelection()
            dlg.Destroy()
            self._venous_mixer.start_stream()
            self.venous_spin_gas1_percentage.Enable(False)
            self.venous_spin_gas2_percentage.Enable(False)
            self.venous_spin_total_flow.Enable(False)
            gas1 = self._venous_mixer.get_gas_ID(venouschoicegas1)
            gas2 = self._venous_mixer.get_gas_ID(venouschoicegas2)
            gas1_percentage = self.venous_spin_gas1_percentage.GetValue()
            gas2_percentage = self.venous_spin_gas2_percentage.GetValue()
            flow = int(self.venous_spin_total_flow.GetValue())
            balance = float(venouschoicebalance)
            self._venous_mixer.change_gas_mix(gas1_percentage, gas2_percentage, flow, 1, gas1=gas1, gas2=gas2, balance_channel=balance)
            self.timer_update_venous_GB100.Start(60000, wx.TIMER_CONTINUOUS)
        elif label == 'Stop Venous Gas Mixer':
            self.timer_update_venous_GB100.Stop()
            self.venous_btn_stream_GB100.SetLabel('Start Venous Gas Mixer')
            gas1_percentage = self._venous_mixer.get_channel_percent_value(1)
            gas2_percentage = self._venous_mixer.get_channel_percent_value(2)
            flow = self._venous_mixer.get_mainboard_total_flow()
            self._venous_mixer.change_gas_mix(gas1_percentage, gas2_percentage, flow, 0)
            self._venous_mixer.stop_stream()
            self.venous_spin_gas1_percentage.Enable(True)
            self.venous_spin_gas2_percentage.Enable(True)
            self.venous_spin_total_flow.Enable(True)
            self.venous_spin_gas1_percentage.SetValue(gas1_percentage)
            self.venous_spin_gas2_percentage.SetValue(gas2_percentage)
            self.venous_spin_total_flow.SetValue(flow)

    def OnTSM(self, event):
        label = self.btn_stream_TSM.GetLabel()
        if label == 'Start CDI Monitor':
            self.btn_stream_TSM.SetLabel('Stop CDI Monitor')
            self._monitor.start_stream()
            self.timer_update_CDI.Start(5000, wx.TIMER_CONTINUOUS)
        elif label == 'Stop CDI Monitor':
            self.timer_update_CDI.Stop()
            self._monitor.stop_stream()
            self.btn_stream_TSM.SetLabel('Start CDI Monitor')

    def OnPresens(self, event):
        label = self.btn_stream_presens.GetLabel()
        section = LP_CFG.get_hwcfg_section(self._sensor.name)
        dev = section['Device']
        line = section['LineName']
        low_pt = section['CalPt1_Target']
        low_read = section['CalPt1_Reading']
        high_pt = section['CalPt2_Target']
        high_read = section['CalPt2_Reading']
        if label == 'Start Arterial pO2 Sensor':
            self.btn_stream_presens.SetLabel('Stop Arterial pO2 Sensor')
            try:
                self._sensor.hw.open(dev=dev)
                self._sensor.hw.add_channel(line)
                self._sensor.set_ch_id(line)
                channel = self._sensor.ch_id
                self._sensor.hw.set_calibration(channel, float(low_pt), float(low_read), float(high_pt), float(high_read))
            except AIDeviceException as e:
                dlg = wx.MessageDialog(parent=self, message=str(e), caption='AI Device Error', style=wx.OK)
                dlg.ShowModal()
            if self._sensor.hw.is_open():
                self._sensor.hw.start()
            else:
                self._sensor.hw.remove_channel(line)
        elif label == 'Stop Arterial pO2 Sensor':
            self.btn_stream_presens.SetLabel('Start Arterial pO2 Sensor')
            self._sensor.hw.remove_channel(line)

    def OnDialysis(self, event):  # Logging dialysis rates? New file?
        label = self.btn_automated_dialysis.GetLabel()
        if label == 'Start Automated Dialysis':
            inflow = self.spin_inflow_pump_rate.GetValue()
            outflow = self.spin_outflow_pump_rate.GetValue()
            self._pump_streaming.start_stream()
            self._pump_streaming.record(inflow, outflow, 1)
            self._inflow_pump.start()
            self._inflow_pump.set_dc(inflow/10.9)  # With the 3.17mm BWB peristaltic pump tubing that we use, 1 V = 10.9 ml/min of flow
            self._inflow_pump.set_dc(inflow/10.9)
            self._outflow_pump.start()
            self._outflow_pump.set_dc(outflow/10.9)
            self._outflow_pump.set_dc(outflow/10.9)  # For some reason this only works if I give two commands...
            self.spin_inflow_pump_rate.Enable(False)
            self.spin_outflow_pump_rate.Enable(False)
            self.timer_update_dialysis.Start(300000, wx.TIMER_CONTINUOUS)
            self.btn_automated_dialysis.SetLabel('Stop Automated Dialysis')
        elif label == 'Stop Automated Dialysis':
            self.timer_update_dialysis.Stop()
            self._inflow_pump.set_dc(0)
            self._inflow_pump.close()
            self._outflow_pump.set_dc(0)
            self._outflow_pump.close()
            self._pump_streaming.record(self.spin_inflow_pump_rate.GetValue(), self.spin_outflow_pump_rate.GetValue(), 0)
            self._pump_streaming.stop_stream()
            self.spin_inflow_pump_rate.Enable(True)
            self.spin_outflow_pump_rate.Enable(True)
            self.btn_automated_dialysis.SetLabel('Start Automated Dialysis')

    def OnArterialGB100Timer(self, event):
        if event.GetId() == self.timer_update_arterial_GB100.GetId():
            self.update_arterial_gas_mix()

    def OnVenousGB100Timer(self, event):
        if event.GetId() == self.timer_update_venous_GB100.GetId():
            self.update_venous_gas_mix()

    def OnCDITimer(self, event):
        if event.GetId() == self.timer_update_CDI.GetId():
            self.update_cdi_plots()

    def OnDialysisTimer(self, event):
        if event.GetId() == self.timer_update_dialysis.GetId():
            self.update_dialysis()

    def update_arterial_gas_mix(self):
        channel1_gas_ID = self._arterial_mixer.get_channel_id_gas(1)
        channel2_gas_ID = self._arterial_mixer.get_channel_id_gas(2)
        new_channel_1_percentage = self._arterial_mixer.get_channel_percent_value(1)
        new_channel_2_percentage = self._arterial_mixer.get_channel_percent_value(2)
        current_flow = self._arterial_mixer.get_mainboard_total_flow()
        if self._sensor.hw._AI__thread and self._sensor.hw._AI__thread.is_alive() and self._sensor.hw.active_channels():
            t, pO2 = self._sensor.get_file_strategy('StreamRaw').retrieve_buffer(0, 1)
            if pO2 > self.pO2upperrange:
                if channel1_gas_ID == 2 and channel2_gas_ID == 3:
                    new_channel_1_percentage = new_channel_1_percentage + 1
                    new_channel_2_percentage = new_channel_2_percentage - 1
                elif channel1_gas_ID == 3 and channel2_gas_ID == 2:
                    new_channel_1_percentage = new_channel_1_percentage - 1
                    new_channel_2_percentage = new_channel_2_percentage + 1
                else:
                    pass
            elif pO2 < self.pO2lowerrange:
                if channel1_gas_ID == 2 and channel2_gas_ID == 3:
                    new_channel_1_percentage = new_channel_1_percentage - 1
                    new_channel_2_percentage = new_channel_2_percentage + 1
                elif channel1_gas_ID == 3 and channel2_gas_ID == 2:
                    new_channel_1_percentage = new_channel_1_percentage + 1
                    new_channel_2_percentage = new_channel_2_percentage - 1
                else:
                    pass
        if new_channel_1_percentage < 0:
            new_channel_1_percentage = 0
        if new_channel_1_percentage > 100:
            new_channel_1_percentage = 100
        if new_channel_2_percentage < 0:
            new_channel_2_percentage = 0
        if new_channel_2_percentage > 100:
            new_channel_2_percentage = 100
        if new_channel_1_percentage == self._arterial_mixer.get_channel_percent_value(1) and new_channel_2_percentage == self._arterial_mixer.get_channel_percent_value(2):
            print('no change in arterial gas mix required')
            return
        else:
            print('changing arterial gas mix due to Arterial pO2')
            self._arterial_mixer.change_gas_mix(new_channel_1_percentage, new_channel_2_percentage, current_flow, 1)

    def update_venous_gas_mix(self):
        self.get_cdi_label_values()
        channel1_gas_ID = self._venous_mixer.get_channel_id_gas(1)
        channel2_gas_ID = self._venous_mixer.get_channel_id_gas(2)
        current_flow = self._venous_mixer.get_mainboard_total_flow()
        new_gas_flow = current_flow
        new_channel_1_percentage = self._venous_mixer.get_channel_percent_value(1)
        new_channel_2_percentage = self._venous_mixer.get_channel_percent_value(2)
        if self.cdi_graphs_values['Venous pCO2'] and self._monitor._TSMSerial__thread_streaming:  # Don't update gas mix if no data is being streamed by CDI
            pCO2 = self.cdi_graphs_values['Venous pCO2']
            if pCO2 > self.co2upper:
                new_gas_flow = new_gas_flow + 2
            elif pCO2 < self.co2lower:
                new_gas_flow = new_gas_flow - 2
        if self.cdi_graphs_values['Venous pH'] and self._monitor._TSMSerial__thread_streaming:
            pH = self.cdi_graphs_values['Venous pH']
            if pH < self.phlower:
                new_gas_flow = new_gas_flow + 4
            elif pH > self.phupper:
                new_gas_flow = new_gas_flow - 4
        if self.cdi_graphs_values['O2 Saturation'] and self._monitor._TSMSerial__thread_streaming:
            sO2 = self.cdi_graphs_values['O2 Saturation']
            if sO2 > self.saturationupper:
                if channel1_gas_ID == 2 and channel2_gas_ID == 3:
                    new_channel_1_percentage = new_channel_1_percentage + 1
                    new_channel_2_percentage = new_channel_2_percentage - 1
                elif channel1_gas_ID == 3 and channel2_gas_ID == 2:
                    new_channel_1_percentage = new_channel_1_percentage - 1
                    new_channel_2_percentage = new_channel_2_percentage + 1
                else:
                    pass
            elif sO2 < self.saturationlower:
                if channel1_gas_ID == 2 and channel2_gas_ID == 3:
                    new_channel_1_percentage = new_channel_1_percentage - 1
                    new_channel_2_percentage = new_channel_2_percentage + 1
                elif channel1_gas_ID == 3 and channel2_gas_ID == 2:
                    new_channel_1_percentage = new_channel_1_percentage + 1
                    new_channel_2_percentage = new_channel_2_percentage - 1
                else:
                    pass
        if new_gas_flow < 0:
            new_gas_flow = 0
        if new_gas_flow > 200:  # Gas flow cannot exceed blood flow through the PV oxygenator
            new_gas_flow = 200
        if new_channel_1_percentage < 0:
            new_channel_1_percentage = 0
        if new_channel_1_percentage > 100:
            new_channel_1_percentage = 100
        if new_channel_2_percentage < 0:
            new_channel_2_percentage = 0
        if new_channel_2_percentage > 100:
            new_channel_2_percentage = 100
        if new_gas_flow == current_flow and new_channel_1_percentage == self._venous_mixer.get_channel_percent_value(1) and new_channel_2_percentage == self._venous_mixer.get_channel_percent_value(2):
            print('no change in venous gas mix required')
            return
        else:
            print('changing venous gas mix')
            self._venous_mixer.change_gas_mix(new_channel_1_percentage, new_channel_2_percentage, new_gas_flow, 1)

    def get_cdi_label_values(self):
        for key in self.cdi_graphs_values.keys():
            label = self.readouts[key].label_value.GetLabel()
            self.cdi_graphs_values[key] = label
        for key, value in self.cdi_graphs_values.items():
            if value == '000':
                self.cdi_graphs_values[key] = []
            else:
                try:
                    self.cdi_graphs_values[key] = float(value)
                except ValueError:
                    self.cdi_graphs_values[key] = []

    def update_cdi_plots(self):
        data = self._monitor.get_parsed_data()
        if not data:
            return
        data_list = list(data)
        time_min = data_list[0] / 60000  # Gives time in minutes
        for key in self.readouts.keys():
            self.readouts[key].label_value.SetLabel(data_list[list(self._cdi_labels).index(key)])
        self.get_cdi_label_values()
        for key, value in self.cdi_graphs_values.items():
            if value:
                self._plots_main[list(self._cdi_graphs_ranges).index(key)].plot(value, time_min)
                self._plots_lt[list(self._cdi_graphs_ranges).index(key)].plot(value, time_min)

    def update_dialysis(self):
        change_inflow = False
        change_outflow = False
        current_inflow = self.spin_inflow_pump_rate.GetValue()
        new_inflow = current_inflow
        if self._monitor._TSMSerial__thread_streaming:
            K = self.readouts['K'].label_value.GetLabel()
            try:
                k_value = float(K)
            except ValueError:
                k_value = []
            if k_value and k_value >= self.upper_k_limit:  # Want to run harder dialysis
                new_inflow = current_inflow + 0.5
            elif k_value and k_value <= self.lower_k_limit:  # Back off on dialysis
                new_inflow = current_inflow - 0.5
            else:
                pass
        if new_inflow > self.upper_dialysis_limit:
            new_inflow = self.upper_dialysis_limit
        elif new_inflow < self.lower_dialysis_limit:
            new_inflow = self.lower_dialysis_limit
        if new_inflow == current_inflow:
            print('no change in dialysate inflow rate required')
            adjusted_outflow = self.spin_outflow_pump_rate.GetValue()
        else:
            print('changing dialysate inflow rate')
            self._inflow_pump.set_dc(new_inflow/10.9)
            self.spin_inflow_pump_rate.SetValue(new_inflow)
            adjusted_outflow = self.spin_outflow_pump_rate.GetValue() + (new_inflow - current_inflow)
            change_inflow = True
        current_inflow = self.spin_inflow_pump_rate.GetValue()
        current_outflow = self.spin_outflow_pump_rate.GetValue()
        new_outflow = adjusted_outflow
        if self._monitor._TSMSerial__thread_streaming:
            Hct = self.readouts['Hct'].label_value.GetLabel()
            try:
                hct_value = float(Hct)
            except ValueError:
                hct_value = []
            if hct_value and hct_value >= self.upper_hct_limit:  # Want to dilute
                new_outflow -= 0.5
            elif hct_value and hct_value <= self.lower_hct_limit:  # Want to concentrate
                new_outflow += 0.5
            else:
                pass
        if new_outflow > (current_inflow + 1.5):  # Don't want flow rates to be massively divergent or else we will get significant concentration/dilution in a short period
            new_outflow = current_inflow + 1.5
        elif new_outflow < (current_inflow - 1.5):
            new_outflow = current_inflow - 1.5
        if new_outflow == current_outflow:
            print('no change in dialysate outflow rate required')
        else:
            print('changing dialysate outflow rate')
            self._outflow_pump.set_dc(new_outflow/10.9)
            self.spin_outflow_pump_rate.SetValue(new_outflow)
            change_outflow = True
        if change_inflow or change_outflow:
            self._pump_streaming.record(self.spin_inflow_pump_rate.GetValue(), self.spin_outflow_pump_rate.GetValue(), 1)

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        sensorname = 'Arterial pO2'
        section = LP_CFG.get_hwcfg_section(sensorname)
        pO2lowerrange = section['lowerrange']
        pO2upperrange = section['upperrange']
        self.acq = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
        self.sensor = SensorStream(sensorname, 'mmHg', self.acq, valid_range=[float(pO2lowerrange), float(pO2upperrange)])
        raw = StreamToFile('StreamRaw', None, self.acq.buf_len)
        raw.open(LP_CFG.LP_PATH['stream'], f'{self.sensor.name}_raw', self.sensor.params)
        self.sensor.add_strategy(raw)
        self.sensor.open()
        self.sensor.start()

        self.ao_inflow = NIDAQ_AO('Dialysate Inflow Pump')
        self.ao_outflow = NIDAQ_AO('Dialysate Outflow Pump')
        self.ao_streaming = DialysatePumps('Automated Dialysate Pumps')
        self.ao_streaming.open()
        self.ao_streaming.open_stream(LP_CFG.LP_PATH['stream'])

        self.arterial_mixer = GB100('Arterial Gas Mixer')
        self.arterial_mixer.open()
        self.arterial_mixer.open_stream(LP_CFG.LP_PATH['stream'])

        self.venous_mixer = GB100('Venous Gas Mixer')
        self.venous_mixer.open()
        self.venous_mixer.open_stream(LP_CFG.LP_PATH['stream'])

        section = LP_CFG.get_hwcfg_section('CDI Monitor')
        com = section['commport']
        baud = section['baudrate']
        bytesize = section['bytesize']
        parity = section['parity']
        stopbits = section['stopbits']
        phlower = section['phlower']
        phupper = section['phupper']
        saturationlower = section['saturationlower']
        saturationupper = section['saturationupper']
        co2lower = section['co2lower']
        co2upper = section['co2upper']
        self.monitor = TSMSerial('CDI Monitor')
        self.monitor.open(com, int(baud), int(bytesize), parity, int(stopbits))
        self.monitor.open_stream(LP_CFG.LP_PATH['stream'])
        self.cdi_labels = {'Time': '', 'Venous pH': 'units', 'Venous pCO2': 'mmHg', 'Venous pO2': 'mmHg', 'Venous Temperature': 'C', 'Venous Bicarbonate': 'mmol/L', 'Venous BE': 'mmol/L', 'K': 'mmol/L', 'O2 Saturation': '%', 'Hct': '%', 'Hb': 'g/dL'}
        self.cdi_graphs_ranges = {'Venous pH': [float(phlower), float(phupper)], 'O2 Saturation': [float(saturationlower), float(saturationupper)], 'Venous pCO2': [float(co2lower), float(co2upper)]}
        self.gas_parameters = ['Air', 'Nitrogen', 'Oxygen', 'Carbon Dioxide']
        self.name = 'GB100 CDI Presens Panel'

        self.panel_GB100_CDI_Presens = PanelGB100CDIPresens(self, self.arterial_mixer, self.venous_mixer, self.monitor, self.sensor, self.ao_inflow, self.ao_outflow, self.ao_streaming, self.cdi_labels, self.cdi_graphs_ranges, self.gas_parameters, self.name)
        sizer = wx.GridSizer(cols=1)
        sizer.Add(self.panel_GB100_CDI_Presens, 1, wx.EXPAND, border=2)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Maximize(True)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel_GB100_CDI_Presens.timer_update_arterial_GB100.Stop()
        self.panel_GB100_CDI_Presens.timer_update_venous_GB100.Stop()
        self.panel_GB100_CDI_Presens.timer_update_CDI.Stop()
        self.panel_GB100_CDI_Presens.timer_update_dialysis.Stop()
        if self.arterial_mixer.get_working_status():
            gas1_percentage = self.arterial_mixer.get_channel_percent_value(1)
            gas2_percentage = self.arterial_mixer.get_channel_percent_value(2)
            flow = self.arterial_mixer.get_mainboard_total_flow()
            self.arterial_mixer.change_gas_mix(gas1_percentage,  gas2_percentage, flow, 0)
        if self.venous_mixer.get_working_status():
            gas1_percentage = self.venous_mixer.get_channel_percent_value(1)
            gas2_percentage = self.venous_mixer.get_channel_percent_value(2)
            flow = self.venous_mixer.get_mainboard_total_flow()
            self.venous_mixer.change_gas_mix(gas1_percentage,  gas2_percentage, flow, 0)
        self.arterial_mixer.stop_stream()
        self.arterial_mixer.close_stream()
        self.venous_mixer.stop_stream()
        self.venous_mixer.close_stream()
        self.sensor.stop()
        self.sensor.close()
        if self.sensor.hw._task:
            self.sensor.hw.stop()
            self.sensor.hw.close()
        self.ao_inflow.set_dc(0)
        self.ao_inflow.close()
        self.ao_inflow.halt()
        self.ao_outflow.set_dc(0)
        self.ao_outflow.close()
        self.ao_outflow.halt()
        self.ao_streaming.record(self.panel_GB100_CDI_Presens.spin_inflow_pump_rate.GetValue(), self.panel_GB100_CDI_Presens.spin_outflow_pump_rate.GetValue(), 0)
        self.ao_streaming.stop_stream()
        self.ao_streaming.close_stream()
        self.monitor.stop_stream()
        self.monitor.close_stream()
        self.Destroy()
        self.Destroy()

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True

if __name__ == "__main__":
    LP_CFG.set_base(basepath='~/Documents/LPTEST')
    LP_CFG.update_stream_folder()
    utils.setup_default_logging(filename='panel_gb100_saturation_monitor')
    app = MyTestApp(0)
    app.MainLoop()
