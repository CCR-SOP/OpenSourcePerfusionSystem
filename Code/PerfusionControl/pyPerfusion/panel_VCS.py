# -*- coding: utf-8 -*-
"""

@author: Allen Luna

Panel class for testing and configuring Valve Control System
"""
import wx

from pyHardware.pyDIO_NIDAQ import NIDAQ_DIO
from pyPerfusion.panel_DIO import PanelDIO
from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyPerfusion.panel_AO import PanelAO

chemical_valves = {}
glucose_valves = {}
open_chemical_valves = {}
open_glucose_valves = {}

class PanelVCS(PanelDIO):

    def OnOpen(self, evt):
        super().OnOpen(evt)
        state = self.btn_open.GetLabel()
        if state == 'Close':  # If channel was just opened
            self.btn_activate.SetBackgroundColour('red')
            if 'pH/CO2/O2' in self._name:
               chemical_valves.update({self._name: self})
            else:
               glucose_valves.update({self._name: self})
        else:  # If channel was just closed
            self.btn_activate.SetBackgroundColour('gray')
            if self._name in open_chemical_valves.keys():
                del open_chemical_valves[self._name]
            elif self._name in open_glucose_valves.keys():
                del open_glucose_valves[self._name]

    def OnActivate(self, evt):
        super().OnActivate(evt)
        state = self.btn_activate.GetLabel()
        if state == 'Activate':  # If valve was just deactivated
            self.btn_activate.SetBackgroundColour('red')
            if 'pH/CO2/O2' in self._name:
                del open_chemical_valves[self._name]
            elif 'Glucose' in self._name:
                del open_glucose_valves[self._name]
        else:  # If valve was just activated
             self.btn_activate.SetBackgroundColour('green')
             if 'pH/CO2/O2' in self._name:
                if len(open_chemical_valves) > 1:  # If the activation of the valve caused two chemical valves to be open simultaneously
                    for key, chem in open_chemical_valves.items():  # Close the other open chemical valves
                        if key != self._name:
                            chem._dio.deactivate()
                            chem.btn_activate.SetLabel('Activate')
                            chem.btn_activate.SetBackgroundColour('red')
                    open_chemical_valves.clear()
                open_chemical_valves.update({self._name: self})
             elif 'Glucose' in self._name:
                open_glucose_valves.update({self._name: self})

   # def OnPulse(self, evt):
   #     pass

    def OnLoadConfig(self, evt):
        super().OnLoadConfig(evt)
        self.btn_activate.SetBackgroundColour('gray')

class PanelCoordination(wx.Panel):
    def __init__(self, parent, name):
        self.parent = parent
        self._name = name
        self._valve_to_open = None
        self._last_valve = ''
        wx.Panel.__init__(self, parent, -1)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=self._name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.spin_time_chemical = wx.SpinCtrlDouble(self, min=0, max=300, initial=10, inc=1)
        self.lbl_time_chemical = wx.StaticText(self, label='Chemical Sensor Switching Time (sec)')  # Amount of time where one valve (corresponding to HA/PV/IVC line) will be open for reading of chemical parameters before this valve is closed an another is opened; will depend on how quickly data is collected by the chemical sensors/how many reads we want before a valve switch (TBD)

        self.btn_start_stop = wx.ToggleButton(self, label='Start')

        self.timer_chemical = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnChemicalTimer)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Left().Proportion(0)

        self.sizer_chemical = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_chemical.Add(self.lbl_time_chemical, flags)
        self.sizer_chemical.Add(self.spin_time_chemical, flags)

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
        self.close_all_chemical_valves()
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
        valve_names = list(chemical_valves.keys())
        try:
            self._last_valve = list(open_chemical_valves.keys())[0]
        except IndexError:
            self._last_valve = ''
        if 'Hepatic Artery' in self._last_valve:
            self._valve_to_open = valve_names[1]
        elif 'Portal Vein' in self._last_valve:
            self._valve_to_open = valve_names[2]
        elif 'Inferior Vena Cava' in self._last_valve:
            self._valve_to_open = valve_names[0]
        else:
            self._valve_to_open = valve_names[0]
        chemical_valves[self._valve_to_open]._dio.activate()
        chemical_valves[self._valve_to_open].btn_activate.SetLabel('Deactivate')
        chemical_valves[self._valve_to_open].btn_activate.SetBackgroundColor('Green')
        open_chemical_valves.update({self._valve_to_open: chemical_valves[self._valve_to_open]})

    def close_all_chemical_valves(self):
        for key, valve in open_chemical_valves.items():
            valve._dio.deactivate()
            valve.btn_activate.SetLabel('Activate')
            valve.btn_activate.SetBackgroundColour('red')
        open_chemical_valves.clear()

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
