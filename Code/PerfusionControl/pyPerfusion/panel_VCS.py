# -*- coding: utf-8 -*-
"""
@author: Allen Luna
Panel class for testing and configuring Valve Control System
"""
import wx
import logging

from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyHardware.pyDIO_NIDAQ import NIDAQ_DIO
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.panel_DIO import PanelDIOIndicator
from pyHardware.pyDIO import DIODeviceException
import pyPerfusion.utils as utils
from pyHardware.pyVCS import VCS, VCSPump

DEV_LIST = ['Dev1', 'Dev2', 'Dev3', 'Dev4', 'Dev5']
LINE_LIST = [f'{line}' for line in range(0, 9)]

DEFAULT_CLEARANCE_TIME_MS = 10_000
DEFAULT_ACQ_TIME_MS = 10_000

class PanelCoordination(wx.Panel):
    def __init__(self, parent, vcs, name):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self._vcs = vcs
        self._name = name

        static_box = wx.StaticBox(self, wx.ID_ANY, label=self._name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.btn_start_stop = wx.ToggleButton(self, label='Start')

        self.btn_glucose_start_stop = wx.ToggleButton(self, label='Open Glucose Valves')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Left().Proportion(0)

        self.sizer.Add(self.btn_start_stop)
        self.sizer.Add(self.btn_glucose_start_stop)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_start_stop.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartStop)
        self.btn_glucose_start_stop.Bind(wx.EVT_TOGGLEBUTTON, self.OnGlucoseStartStop)

    def OnStartStop(self, evt):
        state = self.btn_start_stop.GetLabel()
        if state == 'Start':
            self._vcs.start_cycle('CDI')
            self.btn_start_stop.SetLabel('Stop')
        elif state == 'Stop':
            self._vcs.stop_cycle('CDI')
            self.btn_start_stop.SetLabel('Start')

    def OnGlucoseStartStop(self, evt):
        state = self.btn_glucose_start_stop.GetLabel()
        if state == 'Open Glucose Valves':
            self._vcs.open_independent_valve('Portal Vein (Glucose)')
            self._vcs.open_independent_valve('Inferior Vena Cava (Glucose)')
            self.btn_glucose_start_stop.SetLabel('Close Glucose Valves')
        else:
            self._vcs.close_independent_valve('Portal Vein (Glucose)')
            self._vcs.close_independent_valve('Inferior Vena Cava (Glucose)')
            self.btn_glucose_start_stop.SetLabel('Open Glucose Valves')

class PanelPump(wx.Panel):
    def __init__(self, parent, pump):
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._parent = parent
        self._pump = pump

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.slider_speed = wx.Slider(self, value=100, minValue=0, maxValue=100,
                                      style=wx.SL_HORIZONTAL | wx.SL_LABELS)
        self._default_label = 'VCS Pump Speed (%)'
        self.label_speed = wx.StaticText(self, label=self._default_label)

        self.timer_update = wx.Timer(self)
        self.__do_layout()
        self.__set_bindings()
        self.timer_update.Start(200, wx.TIMER_CONTINUOUS)

    def __set_bindings(self):
        self.slider_speed.Bind(wx.EVT_SLIDER, self.OnSpeedChange)
        self.Bind(wx.EVT_TIMER, self.OnUpdate)

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()
        self.sizer.Add(self.label_speed, flags)
        self.sizer.Add(self.slider_speed, flags)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def OnSpeedChange(self, evt):
        val = self.slider_speed.GetValue()
        self._pump.set_speed(val)

    def OnUpdate(self, evt):
        color = wx.GREEN if self._pump.active else wx.RED
        lbl = 'Active' if self._pump.active else 'Inactive'
        self.label_speed.SetLabel(f'{self._default_label}: {lbl}')
        self.label_speed.SetBackgroundColour(color)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self._lgr = logging.getLogger(__name__)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self._vcs = VCS(clearance_time_ms=DEFAULT_CLEARANCE_TIME_MS, acq_time_ms=DEFAULT_ACQ_TIME_MS)
        self._panel_coord = PanelCoordination(self, self._vcs, name='Valve Coordination')

        self.ao = NIDAQ_AO('VCS Pump')
        section = LP_CFG.get_hwcfg_section(self.ao.name)
        self._lgr.debug(f'Reading config for {self.ao.name}')
        dev = section['DevName']
        line = section['LineName']
        self.ao.open(period_ms=1000, dev=dev, line=line)
        self.pump = VCSPump(self.ao)
        self.pump.set_speed(100)
        self.panel_pump = PanelPump(self, self.pump)
        self._vcs.set_pump(self.pump)

        valves = [NIDAQ_DIO('Hepatic Artery (CDI Shunt Sensor)'),
                  NIDAQ_DIO('Portal Vein (CDI Shunt Sensor)'),
                  NIDAQ_DIO('Portal Vein (Glucose)'),
                  NIDAQ_DIO('Inferior Vena Cava (Glucose)')
                  ]
        flags = wx.SizerFlags().Expand().Border()

        self.sizer_dio = wx.GridSizer(cols=2)
        for valve in valves:
            key = valve.name
            try:
                panel = PanelDIOIndicator(self, valve, valve.name)
                self.sizer_dio.Add(panel, flags)
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
                if 'CDI' in key:
                    self._lgr.debug(f'Adding cycled input {key} to CDI')
                    self._vcs.add_cycled_input('CDI', valve)
                elif 'Glucose' in key:
                    self._vcs.add_independent_input(valve)
                panel.update_label()
            except DIODeviceException as e:
                dlg = wx.MessageDialog(parent=self, message=str(e), caption='Digital Output Device Error', style=wx.OK)
                dlg.ShowModal()
                continue

        sizerv = wx.BoxSizer(wx.VERTICAL)
        sizerv.Add(self._panel_coord, flags)
        sizerv.Add(self.panel_pump, flags)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_indicators = wx.BoxSizer(wx.VERTICAL)
        sizer_indicators.Add(self.sizer_dio)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(sizer_indicators, flags)
        sizer.Add(sizerv, flags)
        self.sizer.Add(sizer, flags)

        self.SetSizer(self.sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
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
    app = MyTestApp(0)
    app.MainLoop()
