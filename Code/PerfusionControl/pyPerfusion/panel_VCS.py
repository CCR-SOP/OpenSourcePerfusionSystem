# -*- coding: utf-8 -*-
"""

@author: Allen Luna

Panel class for testing and configuring Valve Control System and associated Chemical Sensors
"""
import wx
import logging
import datetime

import numpy as np

from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyPerfusion.panel_AO import PanelAO
from pyHardware.pyDIO_NIDAQ import NIDAQ_DIO
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.panel_AI import PanelAI, PanelAI_Config
from pyPerfusion.SensorPoint import SensorPoint
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.panel_readout import PanelReadout
from pyPerfusion.panel_DIO import PanelDIO, PanelDIOControls
from pyHardware.pyDIO import DIODeviceException
import pyPerfusion.utils as utils
from pyHardware.pyAI import AIDeviceException
from pyHardware.pyAI_Finite_NIDAQ import AI_Finite_NIDAQ
from pyHardware.pyVCS import VCS


chemical_valves = {}
glucose_valves = {}
DEV_LIST = ['Dev1', 'Dev2', 'Dev3', 'Dev4', 'Dev5']
LINE_LIST = [f'{line}' for line in range(0, 9)]

DEFAULT_CLEARANCE_TIME_MS = 2_000 #150_000
DEFAULT_SAMPLES_PER_READ = 3


class PanelVCS(PanelDIOControls):
    def __init__(self, parent, dio, name):
        super().__init__(parent, dio, name, display_config=True)

    def OnOpen(self, evt):
        super().OnOpen(evt)
        state = self.btn_open.GetLabel()
        if state == 'Close':  # If channel was just opened
            self.btn_activate.SetBackgroundColour('red')
            if 'Chemical' in self._name:
               chemical_valves.update({self._name: self})
            elif 'Glucose' in self._name:
               glucose_valves.update({self._name: self})
        else:  # If channel was just closed
            self.btn_activate.SetBackgroundColour('gray')

    def OnActivate(self, evt):
        super().OnActivate(evt)
        state = self.btn_activate.GetLabel()
        if state == 'Activate':  # If valve was just deactivated
            self.btn_activate.SetBackgroundColour('red')
        else:  # If valve was just activated
             self.btn_activate.SetBackgroundColour('green')
             if 'Chemical' in self._name:
                 for key, chem in chemical_valves.items():  # For all chemical valves
                     if chem._dio.value and (key != self._name):  # If the valve is open AND the valve is not the one just opened;
                         chem._dio.deactivate()
                         chem.btn_activate.SetLabel('Activate')
                         chem.btn_activate.SetBackgroundColour('red')

    def OnLoadConfig(self, evt):
        super().OnLoadConfig(evt)
        self.btn_activate.SetBackgroundColour('gray')

class PanelAIVCS(PanelAI):
    def __init__(self, parent, sensor, name):
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self._sensor = sensor
        self._name = name
        self._dev = None
        wx.Panel.__init__(self, parent, -1)

        self._avail_dev = DEV_LIST
        self._avail_lines = LINE_LIST

        self._panel_cfg = PanelAI_Config(self, self._sensor, name, 'Configuration', plot=self)
        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.__do_layout()

        self._sensor.start()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand()

        self.sizer.Add(self._panel_cfg, flags)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

class PanelReadoutVCS(PanelReadout):
    def __init__(self, parent, sensor, name):
        super().__init__(parent, sensor)
        self._logger = logging.getLogger(__name__)
        self.name = name

    def update_value(self):
        data = self._sensor.get_current()
        if data is not None:
            avg = np.mean(data)
            val = float(avg)
            self.label_value.SetLabel(f'{round(val, 1):3}')
            ct = datetime.datetime.now()
            time = "{0:0=2d}".format(ct.hour) + ':' + "{0:0=2d}".format(ct.minute) + ':' + "{0:0=2d}".format(ct.second)
            self.label_name.SetLabel(self.name + ' (As of ' + time + ')')

class PanelReadoutOxygenUtilization(PanelReadout):
    def __init__(self, parent, sensors, name):
        self._logger = logging.getLogger(__name__)
        self.sensors = sensors
        old_name = sensors[0].name
        sensors[0].name = name
        super().__init__(parent, sensors[0])
        sensors[0].name = old_name

    def update_value(self):
        val0 = self.sensors[0].get_current()
        val1 = self.sensors[1].get_current()
        # val1 can be 0, but val0 must be non-zero
        if val0 is not None and val0 != 0 and val1 is not None:
            val = (float(val0) - float(val1)) / float(val0)
            val = val * 100
            self.label_value.SetLabel(f'{round(val, 3):3}')
        else:
            self.label_value.SetLabel('NA')


class PanelCoordination(wx.Panel):
    def __init__(self, parent, vcs, readout_dict, name):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self._vcs = vcs
        self._name = name
        self._readout_dict = readout_dict
        self._readout_list = None

        self._readings = None  # Readings taken before switching to next valve
        self._sampling_period_ms = 3000  # New readings (O2/CO2/pH) are collected every 3 seconds and are coordinated (occur @ the same time)
        self._clearance_time_ms = None

        static_box = wx.StaticBox(self, wx.ID_ANY, label=self._name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.spin_readings_chemical = wx.SpinCtrlDouble(self, min=0, max=20,
                                                        initial=DEFAULT_SAMPLES_PER_READ,
                                                        inc=1)
        self.lbl_readings_chemical = wx.StaticText(self, label='Sensor Readings per Switch')

        self.btn_start_stop = wx.ToggleButton(self, label='Start')
        self.timer_update = wx.Timer(self)
        self.timer_update.Start(milliseconds=1000, oneShot=wx.TIMER_CONTINUOUS)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Left().Proportion(0)

        self.sizer_chemical = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_chemical.Add(self.lbl_readings_chemical, flags)
        self.sizer_chemical.Add(self.spin_readings_chemical, flags)

        self.sizer.Add(self.sizer_chemical)
        self.sizer.AddSpacer(5)
        self.sizer.Add(self.btn_start_stop)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_start_stop.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartStop)

    def OnTimer(self, evt):
        if self._readout_dict:
            for readout in self._readout_dict.values():
                readout.update_value()

    def OnStartStop(self, evt):
        state = self.btn_start_stop.GetLabel()
        if state == 'Start':
            self._readings = int(self.spin_readings_chemical.GetValue())
            # TODO update samples_per_read for each sensor
            self._vcs.start_cycle('Chemical')
            self.btn_start_stop.SetLabel('Stop')
        else:
            self._vcs.stop_cycle('Chemical')
            if self._readout_list:
                for readout in self._readout_list:
                    readout.timer_update.Stop()
                self._readout_list.clear()
            self.btn_start_stop.SetLabel('Start')
            self.timer_update.Stop()

    def OnReadValues(self, event):
        if event.GetId() == self.timer_read_values.GetId():
            self.timer_read_values.Stop()  # Requested number of reads have now been taken
            for sensor in self._sensors:
                # Stop sensors in anticipation of a valve switch
                sensor.hw.remove_channel(sensor._ch_id)
                sensor.hw.start()
             #   latest = sensor.get_latest(self._readings)  # Get last (# of readings) from sensor
             #   print(latest, sensor.name)
            for readout in self._readout_list:
                readout.timer_update.Stop()
            self.update_chemical_valves()  # Switch valve
            self._lgr.debug('starting clear valve timer')
            self.timer_clear_valve.Start(self._clearance_time_ms, wx.TIMER_CONTINUOUS)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self._lgr = logging.getLogger(__name__)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.FlexGridSizer(cols=2)

        valves = [NIDAQ_DIO('Hepatic Artery (Chemical)'),
                  NIDAQ_DIO('Portal Vein (Chemical)'),
                  NIDAQ_DIO('Inferior Vena Cava (Chemical)'),
                  NIDAQ_DIO('Hepatic Artery (Glucose)'),
                  NIDAQ_DIO('Portal Vein (Glucose)'),
                  NIDAQ_DIO('Inferior Vena Cava (Glucose)')
                  ]
        self._vcs = VCS(clearance_time_ms=DEFAULT_CLEARANCE_TIME_MS)
        for valve in valves:
            key = valve.name
            try:
                panel = PanelDIOControls(self, valve, valve.name, display_config=True)
                sizer.Add(panel, 1, wx.EXPAND, border=2)
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
                valve.open(port=port, line=line, active_high=active_high_state, read_only=read_only_state, dev=dev)
                if 'Chemical' in key:
                    self._vcs.add_cycled_input('Chemical', valve)
                else:
                    self._vcs.add_independent_input(valve)
                panel.update_label()
            except DIODeviceException as e:
                dlg = wx.MessageDialog(parent=self, message=str(e), caption='Digital Output Device Error', style=wx.OK)
                dlg.ShowModal()
                continue

        self.acq = AI_Finite_NIDAQ(period_ms=100, volts_p2p=5, volts_offset=2.5,
                                   samples_per_read=DEFAULT_SAMPLES_PER_READ)
        self._chemical_sensors = [SensorPoint('Oxygen', 'mmHg', self.acq),
                                  SensorPoint('Carbon Dioxide', 'mmHg', self.acq),
                                  SensorPoint('pH', '', self.acq)]
        for sensor in self._chemical_sensors:
            sizer.Add(PanelAIVCS(self, sensor, name=sensor.name), 1, wx.EXPAND, border=2)
            self._vcs.add_sensor_to_cycled_valves('Chemical', sensor)



        self.sizer_readout = wx.GridSizer(cols=2)
        readout_dict = {'HA Oxygen': PanelReadoutVCS(self, self._chemical_sensors[0], 'HA Oxygen'),
                        'PV Oxygen': PanelReadoutVCS(self, self._chemical_sensors[0], 'PV Oxygen'),
                        'IVC Oxygen': PanelReadoutVCS(self, self._chemical_sensors[0], 'IVC Oxygen'),
                        'HA CO2': PanelReadoutVCS(self, self._chemical_sensors[1], 'HA CO2'),
                        'PV CO2': PanelReadoutVCS(self, self._chemical_sensors[1], 'PV CO2'),
                        'IVC CO2': PanelReadoutVCS(self, self._chemical_sensors[1], 'IVC CO2'),
                        'HA pH': PanelReadoutVCS(self, self._chemical_sensors[2], 'HA pH'),
                        'PV pH': PanelReadoutVCS(self, self._chemical_sensors[2], 'PV pH'),
                        'IVC pH': PanelReadoutVCS(self, self._chemical_sensors[2], 'IVC pH')
                        }
        for key, readout in readout_dict.items():
            readout.timer_update.Stop()
            self.sizer_readout.Add(readout, 1, wx.ALL | wx.EXPAND, border=1)
        panel_O2_util = PanelReadoutOxygenUtilization(self, [self._chemical_sensors[0], self._chemical_sensors[0]], 'Oxygen Utilization')
        self.sizer_readout.Add(panel_O2_util, 1, wx.ALL | wx.EXPAND, border=1)
        sizer.Add(self.sizer_readout, 1, wx.EXPAND, border=2)

        sizer.Add(PanelCoordination(self, self._vcs, readout_dict, name='Valve Coordination'), 1, wx.EXPAND, border=2)

        self.ao = NIDAQ_AO()
        sizer.Add(PanelAO(self, self.ao, name='VCS Peristaltic Pump (AO)'), 1, wx.EXPAND, border=2)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for sensor in self._chemical_sensors:
            sensor.stop()
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
