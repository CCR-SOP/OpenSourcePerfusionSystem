# -*- coding: utf-8 -*-
"""

@author: Allen Luna

Panel class for testing and configuring Valve Control System and associated Chemical Sensors
"""
import wx
import logging
import datetime

from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyPerfusion.panel_AO import PanelAO
from pyHardware.pyDIO_NIDAQ import NIDAQ_DIO
from pyPerfusion.panel_DIO import PanelDIO
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.panel_AI import PanelAI, PanelAI_Config
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.panel_readout import PanelReadout

chemical_valves = {}
glucose_valves = {}
DEV_LIST = ['Dev1', 'Dev2', 'Dev3', 'Dev4', 'Dev5']
LINE_LIST = [f'{line}' for line in range(0, 9)]

class PanelVCS(PanelDIO):

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
        self._logger = logging.getLogger(__name__)
        wx.Panel.__init__(self, parent, -1)
        self._sensor = sensor
        self._name = name

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer_value = wx.BoxSizer(wx.HORIZONTAL)
        self.label_name = wx.StaticText(self, label=self._name)
        self.label_value = wx.StaticText(self, label='000')
        self.label_units = wx.StaticText(self, label=sensor.unit_str)

        self._PanelReadout__do_layout()

    def update_value(self):
        val = float(self._sensor.get_current())
        self.label_value.SetLabel(f'{round(val, 1):3}')
        ct = datetime.datetime.now()
        time = "{0:0=2d}".format(ct.hour) + ':' + "{0:0=2d}".format(ct.minute) + ':' + "{0:0=2d}".format(ct.second)
        self.label_name.SetLabel(self._name + ' (As of ' + time + ')')

class PanelReadoutOxygenUtilization(PanelReadout):
    def __init__(self, parent, sensors, name):
        self._logger = logging.getLogger(__name__)
        wx.Panel.__init__(self, parent, -1)
        self._sensors = sensors
        self._name = name

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer_value = wx.BoxSizer(wx.HORIZONTAL)
        self.label_name = wx.StaticText(self, label=self._name)
        self.label_value = wx.StaticText(self, label='000')
        self.label_units = wx.StaticText(self, label='%')

        self._PanelReadout__do_layout()

    def update_value(self):
        if float(self._sensors[0].label_value.GetLabel()) != 0:
            val = (float(self._sensors[0].label_value.GetLabel()) - float(self._sensors[1].label_value.GetLabel())) / float(
                self._sensors[0].label_value.GetLabel())
            val = val * 100
            self.label_value.SetLabel(f'{round(val, 3):3}')
        else:
            return

class PanelCoordination(wx.Panel):
    def __init__(self, parent, sensors, readout_dict, name):
        self.parent = parent
        self._sensors = sensors
        self._name = name
        self._readout_dict = readout_dict
        self._readout_list = None

        self._valve_to_open = None
        self._last_valve = ''

        self._readings = None  # Readings taken before switching to next valve
        self._sampling_period_ms = 3000  # New readings (O2/CO2/pH) are collected every 3 seconds and are coordinated (occur @ the same time)
        self._clearance_time_ms = None

        wx.Panel.__init__(self, parent, -1)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=self._name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.spin_readings_chemical = wx.SpinCtrlDouble(self, min=0, max=20, initial=0, inc=1)
        self.lbl_readings_chemical = wx.StaticText(self, label='Sensor Readings per Switch')

        self.btn_start_stop = wx.ToggleButton(self, label='Start')

        self.__do_layout()
        self.__set_bindings()

        self.timer_clear_valve = wx.Timer(self, id=0)
        self.Bind(wx.EVT_TIMER, self.OnClearValve, id=0)

        self.timer_read_values = wx.Timer(self, id=1)
        self.Bind(wx.EVT_TIMER, self.OnReadValues, id=1)

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

    def OnStartStop(self, evt):
        for sensor in self._sensors:  # Stop all sensors, as all valves are about to be closed
            sensor.hw.remove_channel(sensor._ch_id)
        self.close_all_chemical_valves()
        self._last_valve = ''
        state = self.btn_start_stop.GetLabel()
        if state == 'Start':
            self._readings = int(self.spin_readings_chemical.GetValue())
            self.update_chemical_valves()
            self.timer_clear_valve.Start(self._clearance_time_ms, wx.TIMER_CONTINUOUS)
            self.btn_start_stop.SetLabel('Stop')
        else:
            self.timer_read_values.Stop()
            self.timer_clear_valve.Stop()
            for sensor in self._sensors:
                sensor.hw.add_channel(sensor._ch_id)
                sensor.hw.start()
            for readout in self._readout_list:
                readout.timer_update.Stop()
            self._readout_list.clear()
            self.btn_start_stop.SetLabel('Start')

    def OnReadValues(self, event):
        if event.GetId() == self.timer_read_values.GetId():
            self.timer_read_values.Stop()  # Requested number of reads have now been taken
            for sensor in self._sensors:
                sensor.hw.remove_channel(sensor._ch_id)  # Stop sensors in anticipation of a valve switch
             #   latest = sensor.get_latest(self._readings)  # Get last (# of readings) from sensor
             #   print(latest, sensor.name)
            for readout in self._readout_list:
                readout.timer_update.Stop()
            self.update_chemical_valves()  # Switch valve
            self.timer_clear_valve.Start(self._clearance_time_ms, wx.TIMER_CONTINUOUS)

    def OnClearValve(self, event):
        if event.GetId() == self.timer_clear_valve.GetId():
            self.timer_clear_valve.Stop()  # Fresh perfusate has now reached the sensors
            for sensor in self._sensors:
                sensor.hw.add_channel(sensor._ch_id)
                sensor.hw.start()
            for readout in self._readout_list:
                readout.timer_update.Start(3000, wx.TIMER_CONTINUOUS)
            self.timer_read_values.Start((self._readings + 1) * self._sampling_period_ms, wx.TIMER_CONTINUOUS)  # Have sensors read for (seconds/reading) x (# of readings), plus an extra three seconds to ensure that at least (# of readings) are recorded (as Python timers and chemical sensors aren't perfectly coordinated)

    def update_chemical_valves(self):
        valve_names = list(chemical_valves.keys())
        for key, valve in chemical_valves.items():
            if valve._dio.value:
                self._last_valve = key
                break
        if 'Hepatic Artery' in self._last_valve:
            self._valve_to_open = [valve for valve in valve_names if 'Portal Vein' in valve][0]
            self.close_chemical_valve(chemical_valves[self._last_valve])
            self._clearance_time_ms = 150000  # Time for PV perfusate to reach all sensors once PV valve is opened
            self._readout_list = [self._readout_dict['PV Oxygen'], self._readout_dict['PV CO2'], self._readout_dict['PV pH']]
        elif 'Portal Vein' in self._last_valve:
            self._valve_to_open = [valve for valve in valve_names if 'Inferior Vena Cava' in valve][0]
            self.close_chemical_valve(chemical_valves[self._last_valve])
            self._clearance_time_ms = 150000  # Time for IVC perfusate to reach all sensors once IVC valve is opened
            self._readout_list = [self._readout_dict['IVC Oxygen'], self._readout_dict['IVC CO2'], self._readout_dict['IVC pH']]
        elif 'Inferior Vena Cava' in self._last_valve:
            self._valve_to_open = [valve for valve in valve_names if 'Hepatic Artery' in valve][0]
            self.close_chemical_valve(chemical_valves[self._last_valve])
            self._clearance_time_ms = 150000  # Time for HA perfusate to reach all sensors once HA valve is opened
            self._readout_list = [self._readout_dict['HA Oxygen'], self._readout_dict['HA CO2'], self._readout_dict['HA pH']]
        else:
            self._valve_to_open = [valve for valve in valve_names if 'Hepatic Artery' in valve][0]
            self._clearance_time_ms = 150000  # Time for HA perfusate to reach all sensors once HA valve is opened
            self._readout_list = [self._readout_dict['HA Oxygen'], self._readout_dict['HA CO2'], self._readout_dict['HA pH']]
        chemical_valves[self._valve_to_open]._dio.activate()
        chemical_valves[self._valve_to_open].btn_activate.SetLabel('Deactivate')
        chemical_valves[self._valve_to_open].btn_activate.SetBackgroundColour('Green')

    def close_all_chemical_valves(self):
        for valve in chemical_valves.values():
            self.close_chemical_valve(valve)

    def close_chemical_valve(self, valve):
        valve._dio.deactivate()
        valve.btn_activate.SetLabel('Activate')
        valve.btn_activate.SetBackgroundColour('red')

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=3)

        valves = {'Hepatic Artery (Chemical)': NIDAQ_DIO(),
                  'Portal Vein (Chemical)': NIDAQ_DIO(),
                  'Inferior Vena Cava (Chemical)': NIDAQ_DIO(),
                  'Hepatic Artery (Glucose)': NIDAQ_DIO(),
                  'Portal Vein (Glucose)': NIDAQ_DIO(),
                  'Inferior Vena Cava (Glucose)': NIDAQ_DIO()
                  }
        for key, valve in valves.items():
            sizer.Add(PanelVCS(self, valve, name=key), 1, wx.EXPAND, border=2)

        self.acq = NIDAQ_AI(period_ms=1, volts_p2p=5, volts_offset=2.5)
        self._chemical_sensors = [SensorStream('Oxygen', 'mmHg', self.acq), SensorStream('Carbon Dioxide', 'mmHg', self.acq), SensorStream('pH', '', self.acq)]
        for sensor in self._chemical_sensors:
            sizer.Add(PanelAIVCS(self, sensor, name=sensor.name), 1, wx.EXPAND, border=2)

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
        panel_O2_util = PanelReadoutOxygenUtilization(self, [readout_dict['HA Oxygen'], readout_dict['IVC Oxygen']], 'Oxygen Utilization')
        self.sizer_readout.Add(panel_O2_util, 1, wx.ALL | wx.EXPAND, border=1)
        sizer.Add(self.sizer_readout, 1, wx.EXPAND, border=2)

        sizer.Add(PanelCoordination(self, self._chemical_sensors, readout_dict, name='Valve Coordination'), 1, wx.EXPAND, border=2)

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
    app = MyTestApp(0)
    app.MainLoop()
