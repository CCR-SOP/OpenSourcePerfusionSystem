# -*- coding: utf-8 -*-
"""

@author: Allen Luna

Panel class for testing and configuring Dexcom G6 Receiver/Sensor pair, plotting glucose sensor data, and for initiating glucose controlled insulin/glucagon infusions
"""
from enum import Enum
import wx
import logging
import pyPerfusion.utils as utils

from dexcom_G6_reader.readdata import Dexcom
from pyHardware.pyDexcom import DexcomSensor
from pyPerfusion.plotting import TSMDexPanelPlotting, TSMDexPanelPlotLT, TSMDexSensorPlot
from pyHardware.PHDserial import PHDserial
from pyPerfusion.panel_Syringe import PanelSyringe
from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyHardware.pyDIO_NIDAQ import NIDAQ_DIO
from pyHardware.pyDIO import DIODeviceException
from pyHardware.pyVCS import VCS, VCSPump
import pyPerfusion.PerfusionConfig as LP_CFG

engaged_COM_list = []
sensors = []

class PlotFrame(Enum):
    FROM_START = 0
    LAST_30_SECONDS = 0.5
    LAST_MINUTE = 1
    Last_5_MINUTES = 5
    LAST_15_MINUTES = 15
    LAST_30_MINUTES = 30
    LAST_HOUR = 60

class DexcomReadout(wx.Panel):
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

class PanelDexcom(wx.Panel):
    def __init__(self, parent, receiver_class, valve, vcs, name, unit, valid_range, lgr):
        self._logger = lgr
        self.parent = parent
        self._receiver_class = receiver_class
        self._valve = valve
        self._vcs = vcs
        self._name = name
        self._unit = unit
        self._valid_range = valid_range
        self._connected_receiver = None

        wx.Panel.__init__(self, parent, -1)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer_main = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_circuit_SN_pair = wx.StaticText(self, label='Dexcom Receiver')
        self.choice_circuit_SN_pair = wx.StaticText(self, label='')

        self.label_connect = wx.StaticText(self, label='')

        self.btn_start = wx.Button(self, label='Start Acquisition')
        self.btn_start.Enable(False)

        self.set_receiver()

        self.sensor = DexcomSensor(self._name[14:] + ' Glucose', self._unit, self._connected_receiver)
        sensors.append(self.sensor)

        self.graph_sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel_main = TSMDexPanelPlotting(self)
        self.panel_main_plotraw = TSMDexSensorPlot(self._name, self.panel_main.axes, self._unit, self._valid_range)
        self.panel_main.add_plot(self.panel_main_plotraw)
        self.graph_sizer.Add(self.panel_main, 9, wx.ALL | wx.EXPAND, border=0)
        self.panel_sub = TSMDexPanelPlotLT(self)
        self.panel_sub_plotraw = TSMDexSensorPlot('', self.panel_sub.axes, '', self._valid_range)
        self.panel_sub.add_plot(self.panel_sub_plotraw)
        self.graph_sizer.Add(self.panel_sub, 2, wx.ALL | wx.EXPAND, border=0)

        self.__plot_frame = PlotFrame.LAST_MINUTE
        self.choice_time = self._create_choice_time()

        self.readout = DexcomReadout(self, self._name[14:] + ' Glucose', self._unit)

        self.__do_layout()
        self.__set_bindings()

        self.sensor.open()
        self.sensor.open_stream(LP_CFG.LP_PATH['stream'])

    def set_receiver(self):
        receiver_info = LP_CFG.open_receiver_info()
        for key, val in receiver_info.items():
            if key in self._name.lower():
                self.choice_circuit_SN_pair.SetLabel('%s (SN = %s)' % (key, val))
        receiver_choice = self.choice_circuit_SN_pair.GetLabel()
        SN_choice = receiver_choice[-11:-1]
        COM_ports = self._receiver_class.FindDevices()
        for COM in COM_ports:
            if not (COM in engaged_COM_list):
                potential_receiver = self._receiver_class(COM)
                potential_SN = potential_receiver.ReadManufacturingData().get('SerialNumber')
                if potential_SN == SN_choice:
                    potential_receiver.Disconnect()
                    self._connected_receiver = self._receiver_class(COM)
                    engaged_COM_list.append(COM)
                    self.label_connect.SetLabel('Connected to %s' % COM)
                    self.btn_start.Enable(True)
                    return
                else:
                    potential_receiver.Disconnect()

    def _create_choice_time(self):
        parameters = [item.name for item in PlotFrame]
        choice = wx.Choice(self, choices=parameters)
        choice.SetStringSelection(self.__plot_frame.name)
        self.panel_main._x_range_minutes = PlotFrame.LAST_MINUTE.value
        font = choice.GetFont()
        font.SetPointSize(12)
        choice.SetFont(font)
        return choice

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 2).Center().Proportion(1)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_circuit_SN_pair, flags)
        sizer.AddSpacer(2)
        sizer.Add(self.choice_circuit_SN_pair, flags)
        sizer.AddSpacer(2)
        sizer.Add(self.label_connect, flags)
        sizer.AddSpacer(2)
        sizer.Add(self.btn_start, flags)
        sizer.AddSpacer(2)
        sizer.Add(self.choice_time, 1, wx.ALL | wx.ALIGN_CENTER)
        sizer.AddSpacer(2)
        sizer.Add(self.readout, 1, wx.ALL | wx.ALIGN_CENTER)
        self.sizer_main.Add(sizer)

        self.sizer_plot_grid = wx.GridSizer(cols=1, hgap=5, vgap=5)
        self.sizer_plot_grid.Add(self.graph_sizer, 1, wx.ALL | wx.EXPAND)
        self.sizer_main.Add(self.sizer_plot_grid, 1, wx.ALL | wx.EXPAND)

        self.SetSizer(self.sizer_main)
        self.Layout()
        self.Fit()

        self.timer_update_plot = wx.Timer(self, id=1)
        self.Bind(wx.EVT_TIMER, self.OnUpdatePlot, id=1)

    def __set_bindings(self):
        self.btn_start.Bind(wx.EVT_BUTTON, self.OnStart)
        self.choice_time.Bind(wx.EVT_CHOICE, self._onchange_plotchoice)

    def _onchange_plotchoice(self, event):
        choice_time = PlotFrame[self.choice_time.GetStringSelection()]
        self.panel_main._x_range_minutes = choice_time.value

    def OnStart(self, evt):
        state = self.btn_start.GetLabel()
        if state == 'Start Acquisition':
            self.sensor.start_stream()
            self.timer_update_plot.Start(60000, wx.TIMER_CONTINUOUS)  # Want to try to update plots every 60 seconds
            self.btn_start.SetLabel('Stop Acquisition')
            self._vcs.open_independent_valve(self._valve.name)
            self._vcs._pump.start()
        elif state == 'Stop Acquisition':
            self.sensor.stop_stream()
            self.timer_update_plot.Stop()
            self.btn_start.SetLabel('Start Acquisition')
            self._vcs.close_independent_valve(self._valve.name)
            for valve in self._vcs._independent.keys():
                if valve != self._valve.name and not self._vcs._independent[valve].is_active:
                    self._vcs._pump.stop()

    def OnUpdatePlot(self, event):
        if event.GetId() == self.timer_update_plot.GetId():
            self.update_plot()

    def update_plot(self):
        time_seconds, data = self.sensor.get_latest()
        error = self.sensor.error
        if data:
            time_minutes = time_seconds / 60
            self.panel_main.plot(data, time_minutes)
            self.panel_sub.plot(data, time_minutes)
            if not error:
                self.readout.label_value.SetLabel(str(float(data)))
            else:
                self.readout.label_value.SetLabel('E')
        if error:
            self.readout.label_value.SetLabel('E')

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self._lgr = logging.getLogger(__name__)

        self._vcs = VCS(clearance_time_ms=None, acq_time_ms=None)

        self.ao = NIDAQ_AO('VCS Pump')
        section = LP_CFG.get_hwcfg_section(self.ao.name)
        self._lgr.debug(f'Reading config for {self.ao.name}')
        dev = section['DevName']
        line = section['LineName']
        self.ao.open(period_ms=1000, dev=dev, line=line)
        self.pump = VCSPump(self.ao)
        self.pump.set_speed(100)
        self._vcs.set_pump(self.pump)

        valves = [NIDAQ_DIO('Portal Vein (Glucose)'), NIDAQ_DIO('Inferior Vena Cava (Glucose)')]

        for valve in valves:
            key = valve.name
            try:
                self._lgr.debug(f'opening config section {key}')
                section = LP_CFG.get_hwcfg_section(key)
                dev = section['Device']
                port = section['Port']
                line = section['Line']
                active_high_state = (section['Active High'] == 'True')
                self._lgr.debug(f'active high is {active_high_state}, {section["Active High"]}')
                read_only_state = (section['Read Only'] == 'True')
            except KeyError as e:
                self._lgr.error(f'Could not find configuration info for {key}')
                self._lgr.error(f'Looking in {LP_CFG.LP_PATH["config"]}')
                continue
            try:
                valve.open(port=port, line=line, active_high=active_high_state, read_only=read_only_state, dev=dev)  # Setting dev/port/line values for DIO
                self._vcs.add_independent_input(valve)
            except DIODeviceException as e:
                dlg = wx.MessageDialog(parent=self, message=str(e), caption='Digital Output Device Error', style=wx.OK)
                dlg.ShowModal()
                continue

        panel_PV = PanelDexcom(self, Dexcom, valves[0], self._vcs, 'Receiver #1 - Portal Vein', 'mg/dL', [80, 120], self._lgr)
        panel_IVC = PanelDexcom(self, Dexcom, valves[1], self._vcs, 'Receiver #2 - Inferior Vena Cava', 'mg/dL', [80, 120], self._lgr)

        dexcom_sizer = wx.GridSizer(cols=1)
        dexcom_sizer.Add(panel_PV, 1, wx.EXPAND, border=2)
        dexcom_sizer.Add(panel_IVC, 1, wx.EXPAND, border=2)

        insulin_injection = PHDserial('Insulin')
        insulin_injection.open('COM12', 9600)
        insulin_injection.ResetSyringe()
        insulin_injection.open_stream(LP_CFG.LP_PATH['stream'])
        insulin_injection.start_stream()

        glucagon_unasyn_injection = PHDserial('Glucagon (Unasyn)')
        glucagon_unasyn_injection.open('COM6', 9600)
        glucagon_unasyn_injection.ResetSyringe()
        glucagon_unasyn_injection.open_stream(LP_CFG.LP_PATH['stream'])
        glucagon_unasyn_injection.start_stream()

        self.sensor = panel_IVC.sensor  # Glucose measurements which inform syringe injections are from the IVC; this is the panel being referenced here
        self._syringes = [insulin_injection, glucagon_unasyn_injection]

        syringe_sizer = wx.GridSizer(cols=2)
        syringe_sizer.Add(PanelTestVasoactiveSyringe(self, self.sensor, 'Insulin Syringe', insulin_injection), 1, wx.ALL | wx.EXPAND, border=1)
        syringe_sizer.Add(PanelTestVasoactiveSyringe(self, self.sensor, 'Glucagon (Unasyn) Syringe', glucagon_unasyn_injection), 1, wx.ALL | wx.EXPAND, border=1)

        sizer = wx.GridSizer(cols=2)
        sizer.Add(dexcom_sizer, 1, wx.ALL | wx.EXPAND, border=1)
        sizer.Add(syringe_sizer, 1, wx.ALL | wx.EXPAND, border=1)
        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for syringe in self._syringes:
            infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
            syringe.stop(-1, infuse_rate, ml_volume, ml_min_rate)
            syringe.stop_stream()
        for sensor in sensors:
            sensor.stop_stream()
            sensor.close_stream()
        self.pump.stop()
        self._vcs.close()
        self.ao.close()
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
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    utils.setup_stream_logger(logger, logging.DEBUG)
    utils.configure_matplotlib_logging()
    utils.setup_default_logging(filename='panel_Dexcom')
    app = MyTestApp(0)
    app.MainLoop()
