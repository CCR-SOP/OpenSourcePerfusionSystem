# -*- coding: utf-8 -*-
"""

@author: Allen Luna

Panel class for testing and configuring Valve Control System
"""
import wx
import time
from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyHardware.pyDIO_NIDAQ import NIDAQ_DIO
from pyPerfusion.panel_AO import PanelAO
import pyPerfusion.PerfusionConfig as LP_CFG

DEV_LIST = ['Dev1', 'Dev2', 'Dev3']
PORT_LIST = [f'port{p}' for p in range(0, 5)]
LINE_LIST = [f'line{line}' for line in range(0, 9)]

chemical_valves = {}
glucose_valves = {}
open_chemical_valves = {}
open_glucose_valves = {}

class PanelVCS(wx.Panel):
    def __init__(self, parent, dio, name):
        self.parent = parent
        self._dio = dio
        self._name = name
        wx.Panel.__init__(self, parent, -1)

        self._avail_dev = DEV_LIST
        self._avail_ports = PORT_LIST
        self._avail_lines = LINE_LIST

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_dev = wx.StaticText(self, label='NI Device Name')
        self.choice_dev = wx.Choice(self, wx.ID_ANY, choices=self._avail_dev)

        self.label_port = wx.StaticText(self, label='Port Number')
        self.choice_port = wx.Choice(self, wx.ID_ANY, choices=self._avail_ports)

        self.label_line = wx.StaticText(self, label='Line Number')
        self.choice_line = wx.Choice(self, wx.ID_ANY, choices=self._avail_lines)

        self.btn_save = wx.Button(self, label='Save Config')
        self.btn_load = wx.Button(self, label='Load Config')

        self.radio_active_sel = wx.RadioBox(self, label='Active State Selection',
                                            choices=['Active High', 'Active Low'])

        self.check_read_only = wx.CheckBox(self, label='Read Only')

        self.btn_open = wx.ToggleButton(self, label='Open')

        self.btn_activate = wx.ToggleButton(self, label='Activate')
        self.btn_activate.SetBackgroundColour('gray')
        self.btn_activate.Enable(False)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center().Proportion(0)
        gridflags = wx.SizerFlags(0).Border(wx.LEFT | wx.RIGHT, 5)
        sizer_dev = wx.GridSizer(cols=3, hgap=5, vgap=2)
        sizer_dev.Add(self.label_dev, gridflags)
        sizer_dev.Add(self.label_port, gridflags)
        sizer_dev.Add(self.label_line, gridflags)
        sizer_dev.Add(self.choice_dev, gridflags)
        sizer_dev.Add(self.choice_port, gridflags)
        sizer_dev.Add(self.choice_line, gridflags)

        sizer_config = wx.BoxSizer(wx.HORIZONTAL)
        sizer_config.Add(self.btn_save, flags)
        sizer_config.Add(self.btn_load, flags)

        sizer_params = wx.BoxSizer(wx.HORIZONTAL)
        sizer_params.Add(self.radio_active_sel, flags)
        sizer_params.Add(self.check_read_only, flags)

        sizer_test = wx.GridSizer(cols=2, hgap=5, vgap=5)
        sizer_test.Add(self.btn_open, gridflags)
        sizer_test.Add(self.btn_activate, gridflags)

        self.sizer.Add(sizer_dev)
        self.sizer.AddSpacer(5)
        self.sizer.Add(sizer_config)
        self.sizer.AddSpacer(5)
        self.sizer.Add(sizer_params)
        self.sizer.AddSpacer(5)
        self.sizer.Add(sizer_test)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_open.Bind(wx.EVT_TOGGLEBUTTON, self.OnOpen)
        self.btn_activate.Bind(wx.EVT_TOGGLEBUTTON, self.OnActivate)
        self.btn_save.Bind(wx.EVT_BUTTON, self.OnSaveConfig)
        self.btn_load.Bind(wx.EVT_BUTTON, self.OnLoadConfig)

    def OnOpen(self, evt):
        state = self.btn_open.GetLabel()
        if state == 'Open':
            dev = self.choice_dev.GetStringSelection()
            port = self.choice_port.GetStringSelection()
            line = self.choice_line.GetStringSelection()
            active_high = self.radio_active_sel.GetSelection() == 0
            read_only = self.check_read_only.GetValue()
            try:
                self._dio.open(port, line, active_high, read_only, dev)
                self._dio.deactivate()  # Takes care of case where lines are active when the DAQ is connected to laptop
                self.btn_open.SetLabel('Close')
                self.btn_activate.Enable(True)
                self.btn_activate.SetBackgroundColour('red')
                if 'pH/CO2/O2' in self._name:
                    chemical_valves.update({self._name: self})
                else:
                    glucose_valves.update({self._name: self})
            except AttributeError:
                wx.MessageBox('Line Could Not be Opened; it is Already in Use', 'Error',
                              wx.OK | wx.ICON_ERROR)
                return
        else:
            self._dio.deactivate()
            self._dio.close()
            if self._name in open_chemical_valves.keys():
                del open_chemical_valves[self._name]
            elif self._name in open_glucose_valves.keys():
                del open_glucose_valves[self._name]
            self.btn_open.SetLabel('Open')
            self.btn_activate.SetLabel('Activate')
            self.btn_activate.SetBackgroundColour('gray')
            self.btn_activate.Enable(False)

    def OnActivate(self, evt):
        state = self.btn_activate.GetLabel()
        if state == 'Activate':
            if 'pH/CO2/O2' in self._name:
                if bool(open_chemical_valves):  # If one or more of the chemical valves is currently open
                    for key, chem in open_chemical_valves.items():  # Close all open chemical valves
                        chem._dio.deactivate()
                        chem.btn_activate.SetLabel('Activate')
                        chem.btn_activate.SetBackgroundColour('red')
                    open_chemical_valves.clear()
                open_chemical_valves.update({self._name: self})
            elif 'Glucose' in self._name:
                open_glucose_valves.update({self._name: self})
            self._dio.activate()
            self.btn_activate.SetLabel('Deactivate')
            self.btn_activate.SetBackgroundColour('green')
        else:
            self._dio.deactivate()
            self.btn_activate.SetLabel('Activate')
            self.btn_activate.SetBackgroundColour('red')
            if 'pH/CO2/O2' in self._name:
                del open_chemical_valves[self._name]
            elif 'Glucose' in self._name:
                del open_glucose_valves[self._name]

    def OnSaveConfig(self, evt):
         section = LP_CFG.get_hwcfg_section(self._name)
         section['Device'] = self.choice_dev.GetStringSelection()
         section['Port'] = self.choice_port.GetStringSelection()
         section['Line'] = self.choice_line.GetStringSelection()
         section['Active High'] = str(self.radio_active_sel.GetSelection() == 0)
         section['Read Only'] = str(self.check_read_only.GetValue())
         LP_CFG.update_hwcfg_section(self._name, section)

    def OnLoadConfig(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        state = self.btn_open.GetLabel()
        if state == 'Close':  # If a config is loaded in on a sub panel that already has access to one of the valves, close this particular valve
            self._dio.deactivate()
            self._dio.close()
            if self._name in open_chemical_valves.keys():
                del open_chemical_valves[self._name]
            elif self._name in open_glucose_valves.keys():
                del open_glucose_valves[self._name]
            self.btn_open.SetLabel('Open')
            self.btn_activate.SetLabel('Activate')
            self.btn_activate.SetBackgroundColour('gray')
            self.btn_activate.Enable(False)
        self.choice_dev.SetStringSelection(section['Device'])
        self.choice_port.SetStringSelection(section['Port'])
        self.choice_line.SetStringSelection(section['Line'])
        active_high_state = (section['Active High'] != 'True')
        self.radio_active_sel.SetSelection(active_high_state)
        read_only_state = (section['Read Only'] == 'True')
        self.check_read_only.SetValue(read_only_state)
        dev = self.choice_dev.GetStringSelection()
        port = self.choice_port.GetStringSelection()
        line = self.choice_line.GetStringSelection()
        active_high = self.radio_active_sel.GetSelection() == 0
        read_only = self.check_read_only.GetValue()
        try:
            self._dio.open(port, line, active_high, read_only, dev)
            self._dio.deactivate()  # Takes care of case where lines are originally active when the DAQ initially turns on
            self.btn_open.SetLabel('Close')
            self.btn_activate.Enable(True)
            self.btn_activate.SetBackgroundColour('red')
            if 'pH/CO2/O2' in self._name:
                chemical_valves.update({self._name: self})
            else:
                glucose_valves.update({self._name: self})
        except AttributeError:
            wx.MessageBox('Line Could Not be Opened; it is Already in Use', 'Error',
                          wx.OK | wx.ICON_ERROR)
            return

class PanelCoordination(wx.Panel):
    def __init__(self, parent, name):
        self.parent = parent
        self._name = name
        wx.Panel.__init__(self, parent, -1)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=self._name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.spin_time_chemical = wx.SpinCtrlDouble(self, min=0, max=300, initial=10, inc=1)
        self.lbl_time_chemical = wx.StaticText(self, label='Chemical Sensor Switching Time (sec)')  # Amount of time where one valve (corresponding to HA/PV/IVC line) will be open for reading of chemical parameters before this valve is closed an another is opened; will depend on how quickly data is collected by the chemical sensors/how many reads we want before a valve switch (TBD)

        self.btn_start_stop = wx.ToggleButton(self, label='Start')
        self.btn_save_cfg = wx.Button(self, label='Save Config')
        self.btn_load_cfg = wx.Button(self, label='Load Config')

        self.timer_chemical = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnChemicalTimer)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Left().Proportion(0)

        self.sizer_chemical = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_chemical.Add(self.lbl_time_chemical, flags)
        self.sizer_chemical.Add(self.spin_time_chemical, flags)

        self.sizer_config = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_config.Add(self.btn_start_stop, flags)
        self.sizer_config.Add(self.btn_save_cfg, flags)
        self.sizer_config.Add(self.btn_load_cfg, flags)

        self.sizer.Add(self.sizer_chemical)
        self.sizer.AddSpacer(5)
        self.sizer.Add(self.sizer_config)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_save_cfg.Bind(wx.EVT_BUTTON, self.OnSaveCfg)
        self.btn_load_cfg.Bind(wx.EVT_BUTTON, self.OnLoadCfg)
        self.btn_start_stop.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartStop)

    def OnSaveCfg(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        section['Chemical Sensor Switching Time (sec)'] = str(self.spin_time_chemical.GetValue())
        LP_CFG.update_hwcfg_section(self._name, section)

    def OnLoadCfg(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        self.spin_time_chemical.SetValue(float((section['Chemical Sensor Switching Time (sec)'])))

    def OnStartStop(self, evt):
        state = self.btn_start_stop.GetLabel()
        if state == 'Start':
            switching_time = int(self.spin_time_chemical.GetValue())
            self.timer_chemical.Start(switching_time * 1000, wx.TIMER_CONTINUOUS)
            self.btn_start_stop.SetLabel('Stop')
        else:
            self.timer_chemical.Stop()
            self.btn_start_stop.SetLabel('Start')

    def OnChemicalTimer(self, event):
        if event.GetId() == self.timer_chemical.GetId():
            self.update_chemical_valves()

    def update_chemical_valves(self):
        if bool(open_chemical_valves):  # If one of the chemical valves is already open
            for key, valve in open_chemical_valves.items():
                valve._dio.deactivate()
                valve.btn_activate.SetLabel('Activate')
                valve.btn_activate.SetBackgroundColour('red')
            open_valve_name = list(open_chemical_valves.keys())[0]
            open_chemical_valves.clear()
            valve_names = list(chemical_valves.keys())
            if 'Hepatic Artery' in open_valve_name:
                chemical_valves[valve_names[1]]._dio.activate()
                chemical_valves[valve_names[1]].btn_activate.SetLabel('Deactivate')
                chemical_valves[valve_names[1]].btn_activate.SetBackgroundColour('green')
                open_chemical_valves.update({valve_names[1]: chemical_valves[valve_names[1]]})
            elif 'Portal Vein' in open_valve_name:
                chemical_valves[valve_names[2]]._dio.activate()
                chemical_valves[valve_names[2]].btn_activate.SetLabel('Deactivate')
                chemical_valves[valve_names[2]].btn_activate.SetBackgroundColour('green')
                open_chemical_valves.update({valve_names[2]: chemical_valves[valve_names[2]]})
            else:
                chemical_valves[valve_names[0]]._dio.activate()
                chemical_valves[valve_names[0]].btn_activate.SetLabel('Deactivate')
                chemical_valves[valve_names[0]].btn_activate.SetBackgroundColour('green')
                open_chemical_valves.update({valve_names[0]: chemical_valves[valve_names[0]]})
        else:  # If no chemical valves are currently open; in this case, open HA valve
            valve_names = list(chemical_valves.keys())
            chemical_valves[valve_names[0]]._dio.activate()
            chemical_valves[valve_names[0]].btn_activate.SetLabel('Deactivate')
            chemical_valves[valve_names[0]].btn_activate.SetBackgroundColour('green')
            open_chemical_valves.update({valve_names[0]: chemical_valves[valve_names[0]]})


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        valves = {'Hepatic Artery (pH/CO2/O2)': NIDAQ_DIO(),
                  'Portal Vein (pH/CO2/O2)': NIDAQ_DIO(),
                  'Inferior Vena Cava (pH/CO2/O2)': NIDAQ_DIO(),
                  'Hepatic Artery (Glucose)': NIDAQ_DIO(),
                  'Portal Vein (Glucose)': NIDAQ_DIO(),
                  'Inferior Vena Cava (Glucose)': NIDAQ_DIO(),
                  }
        sizer = wx.GridSizer(cols=4)
        for key, valve in valves.items():
            sizer.Add(PanelVCS(self, valve, name=key), 1, wx.EXPAND, border=2)
        sizer.Add(PanelAO(self, NIDAQ_AO, name='VCS Peristaltic Pump (AO)'), 1, wx.EXPAND, border=2)
        sizer.Add(PanelCoordination(self, name='Valve Coordination'), 1, wx.EXPAND, border=2)
        self.SetSizer(sizer)
        self.Fit()
        self.Layout()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    app = MyTestApp(0)
    app.MainLoop()
