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
from pyHardware.pyDIO_NIDAQ import NIDAQ_DIO
from pyPerfusion.panel_AI import PanelAI, PanelAICalibration
from pyPerfusion.SensorPoint import SensorPoint
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.panel_readout import PanelReadout
from pyPerfusion.panel_DIO import PanelDIO, PanelDIOControls, PanelDIOIndicator
from pyHardware.pyDIO import DIODeviceException
import pyPerfusion.utils as utils
from pyHardware.pyAI_Finite_NIDAQ import AI_Finite_NIDAQ
from pyHardware.pyVCS import VCS, VCSPump


DEV_LIST = ['Dev1', 'Dev2', 'Dev3', 'Dev4', 'Dev5']
LINE_LIST = [f'{line}' for line in range(0, 9)]

DEFAULT_CLEARANCE_TIME_MS = 20_000  # 150_000
DEFAULT_SAMPLES_PER_READ = 3


class PanelAIVCS(wx.Panel):
    def __init__(self, parent, sensor, name):
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)

        dev = sensor.hw.devname.split('/')
        hw_details = f'{dev[0]}/ai{sensor.ch_id}'

        self._panel_cfg = PanelAICalibration(self, sensor, name)
        self._label = wx.StaticText(self, label=name)
        self._label.SetToolTip(wx.ToolTip(hw_details))
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.__do_layout()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()

        self.sizer.Add(self._label)
        self.sizer.Add(self._panel_cfg, flags)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()


class PanelReadoutGroup(wx.Panel):
    def __init__(self, parent, group_name, o2, co2, ph):
        super().__init__(parent)
        self.name = group_name
        self.static_box = wx.StaticBox(self, wx.ID_ANY, label=self.name)
        self.sizer = wx.StaticBoxSizer(self.static_box, wx.HORIZONTAL)
        self.readout_o2 = PanelReadoutVCS(self, o2, f'Oxygen')
        self.readout_co2 = PanelReadoutVCS(self, co2, f'Carbon Dioxide')
        self.readout_ph = PanelReadoutVCS(self, ph, f'pH')

        self.__do_layout()
        self.__set_bindings()

    def __set_bindings(self):
        pass

    def __do_layout(self):
        flags = wx.SizerFlags().Proportion(1).Expand().Border()

        self.sizer.Add(self.readout_o2, flags)
        self.sizer.Add(self.readout_co2, flags)
        self.sizer.Add(self.readout_ph, flags)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def update_label(self, ct):
        time_str = "{0:0=2d}".format(ct.hour) + ':' + "{0:0=2d}".format(ct.minute) + ':' + "{0:0=2d}".format(ct.second)
        self.static_box.SetLabel(f'{self.name} as of {time_str}')

    def update_value(self):
        ct = datetime.datetime.now()
        self.update_label(ct)
        self.readout_co2.update_value()
        self.readout_o2.update_value()
        self.readout_ph.update_value()


class PanelReadoutVCS(PanelReadout):
    def __init__(self, parent, sensor, name):
        super().__init__(parent, sensor)
        self._logger = logging.getLogger(__name__)
        self.name = name
        self._parent = parent

        # panel will be manually updated
        self.timer_update.Stop()

    def update_value(self):
        ts, data = self._sensor.get_last_acq()
        # data = self._sensor.get_current()
        if data is not None:
            avg = np.mean(data)
            val = float(avg)
            self.label_value.SetLabel(f'{round(val, 1):3}')


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
    def __init__(self, parent, vcs, name):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self._vcs = vcs
        self._name = name
        self._readout_list = None

        self._readings = None  # Readings taken before switching to next valve
        self._sampling_period_ms = 3000  # New readings (O2/CO2/pH) are collected every 3 seconds and are coordinated (occur @ the same time)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=self._name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.spin_readings_chemical = wx.SpinCtrlDouble(self, min=0, max=20,
                                                        initial=DEFAULT_SAMPLES_PER_READ,
                                                        inc=1)
        self.lbl_readings_chemical = wx.StaticText(self, label='Sensor Readings per Switch')

        self.btn_start_stop = wx.ToggleButton(self, label='Start')

        self.btn_glucose_start_stop = wx.ToggleButton(self, label='Open Glucose Valves')

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

    def OnGlucoseStartStop(self, evt):  # For the moment, we are not using the Hepatic Artery Glucose Valve
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
        self.slider_speed = wx.Slider(self, value=25, minValue=0, maxValue=100,
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
        # color = wx.GREEN if self._pump.active else wx.RED
        lbl = 'Active' if self._pump.active else 'Inactive'
        self.label_speed.SetLabel(f'{self._default_label}: {lbl}')
        # self.label_speed.SetBackgroundColour(color)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self._lgr = logging.getLogger(__name__)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self._vcs = VCS(clearance_time_ms=DEFAULT_CLEARANCE_TIME_MS)

        self.ao = NIDAQ_AO('VCS Pump')
        section = LP_CFG.get_hwcfg_section(self.ao.name)
        self._lgr.debug(f'Reading config for {self.ao.name}')
        dev = section['DevName']
        line = section['LineName']
        self.ao.open(period_ms=1000, dev=dev, line=line)
        self.pump = VCSPump(self.ao)
        self.pump.set_speed(3)
        self.panel_pump = PanelPump(self, self.pump)
        self._vcs.set_pump(self.pump)

        valves = [NIDAQ_DIO('Hepatic Artery (Chemical)'),
                  NIDAQ_DIO('Portal Vein (Chemical)'),
                  NIDAQ_DIO('Inferior Vena Cava (Chemical)'),
                  NIDAQ_DIO('Hepatic Artery (Glucose)'),
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
                valve.open(port=port, line=line, active_high=active_high_state, read_only=read_only_state, dev=dev)
                if 'Chemical' in key:
                    self._lgr.debug(f'Adding cycled input {key} to Chemical')
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
        readouts = [PanelReadoutGroup(self, 'HA',
                                      self._chemical_sensors[0],
                                      self._chemical_sensors[1],
                                      self._chemical_sensors[2]),
                    PanelReadoutGroup(self, 'PV',
                                      self._chemical_sensors[0],
                                      self._chemical_sensors[1],
                                      self._chemical_sensors[2]),
                    PanelReadoutGroup(self, 'IVC',
                                      self._chemical_sensors[0],
                                      self._chemical_sensors[1],
                                      self._chemical_sensors[2])]
        self.sizer_readout = wx.BoxSizer(wx.VERTICAL)
        for panel in readouts:
            self.sizer_readout.Add(panel, flags.Border())

        self.sizer_sensors = wx.GridSizer(cols=2)
        for sensor in self._chemical_sensors:
            section = LP_CFG.get_hwcfg_section(sensor.name)
            self._lgr.debug(f'Reading config for {sensor.name}')
            dev = section['Device']
            line = section['LineName']
            self.acq.open(dev)
            self.acq.add_channel(line)
            sensor.set_ch_id(line)
            self.sizer_sensors.Add(PanelAIVCS(self, sensor, name=sensor.name), flags.Border())
            sensor.open(LP_CFG.LP_PATH['stream'])
            sensor.start()

        self._vcs.add_sensor_to_cycled_valves('Chemical', self._chemical_sensors[0])
        self._vcs.add_sensor_to_cycled_valves('Chemical', self._chemical_sensors[1])
        self._vcs.add_sensor_to_cycled_valves('Chemical', self._chemical_sensors[2])

        self._lgr.debug(f'oxy readout is {readouts[0].readout_o2.update_value}')
        self._vcs.add_notify('Chemical', valves[0].name, readouts[0].update_value)
        self._vcs.add_notify('Chemical', valves[1].name, readouts[1].update_value)
        self._vcs.add_notify('Chemical', valves[2].name, readouts[2].update_value)

        panel_O2_util = PanelReadoutOxygenUtilization(self, [self._chemical_sensors[0], self._chemical_sensors[0]], 'Oxygen Utilization')
        self.sizer_readout.Add(panel_O2_util, flags)

        sizerv = wx.BoxSizer(wx.VERTICAL)
        sizerv.Add(PanelCoordination(self, self._vcs, name='Valve Coordination'), flags)
        sizerv.Add(self.panel_pump, flags)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_indicators = wx.BoxSizer(wx.VERTICAL)
        sizer_indicators.Add(self.sizer_dio)
        sizer_indicators.Add(self.sizer_readout, flags)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(sizer_indicators, flags)
        sizer.Add(sizerv, flags)
        self.sizer.Add(sizer, flags)

        self.sizer.Add(self.sizer_sensors, flags)

        self.SetSizer(self.sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for sensor in self._chemical_sensors:
            sensor.stop()
        self._vcs.stop()
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
