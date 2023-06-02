# -*- coding: utf-8 -*-
""" Application to display all hardware control

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.utils as utils
from gui.panel_multiple_syringes import SyringePanel
from gui.panel_syringes_all import PanelAllSyringes
from gui.panel_DialysisPumps import DialysisPumpPanel
from gui.panel_gas_mixers import GasMixerPanel
from gui.panel_levitronix_pumps import LeviPumpPanel
from pyPerfusion.PerfusionSystem import PerfusionSystem
import pyPerfusion.PerfusionConfig as PerfusionConfig


class HardwarePanel(wx.Panel):
    def __init__(self, parent, perfusion_system):
        self.parent = parent
        wx.Panel.__init__(self, parent)
        self._lgr = logging.getLogger('HardwarePanel')

        pump_names = ['Dialysate Inflow Pump', 'Dialysate Outflow Pump', 'Dialysis Blood Pump']
        pumps = []
        for pump_name in pump_names:
            pumps.append(perfusion_system.get_sensor(pump_name))

        vaso = perfusion_system.get_automation('Vasoactive Automation')
        glucose = perfusion_system.get_automation('Glucose Automation')
        manual = [perfusion_system.get_automation('TPN + Bile Salts Manual'),
                  perfusion_system.get_automation('Zosyn Manual')]

        self.panel_syringes = PanelAllSyringes(self, vaso, glucose, manual)

        automation_names = ['Dialysate Inflow Automation',
                            'Dialysate Outflow Automation',
                            'Dialysis Blood Automation']
        automations = []
        for name in automation_names:
            automations.append(perfusion_system.get_automation(name))
        self.panel_dialysate_pumps = DialysisPumpPanel(self, automations)

        automation_names = ['Arterial Gas Mixer Automation', 'Venous Gas Mixer Automation']
        automations = []
        for name in automation_names:
            automations.append(perfusion_system.get_automation(name))
        self.panel_gas_mixers = GasMixerPanel(self, automations)

        sensor_names = ['Arterial PuraLev', 'Venous PuraLev']
        sensors = []
        for name in sensor_names:
            sensors.append(perfusion_system.get_sensor(name))
        self.panel_levitronix_pumps = LeviPumpPanel(self, sensors)

        static_box = wx.StaticBox(self, wx.ID_ANY, label="Hardware Control App")
        self.wrapper = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer_leftside = wx.BoxSizer(wx.VERTICAL)
        sizer_leftside.Add(self.panel_syringes, wx.SizerFlags().Proportion(1).Expand())
        sizer_leftside.Add(self.panel_gas_mixers, wx.SizerFlags().Proportion(1).Expand())

        sizer_rightside = wx.BoxSizer(wx.VERTICAL)
        sizer_rightside.Add(self.panel_dialysate_pumps, wx.SizerFlags().Proportion(1).Expand())
        sizer_rightside.Add(self.panel_levitronix_pumps, wx.SizerFlags().Proportion(1).Expand())

        self.sizer.Add(sizer_leftside, wx.SizerFlags().Proportion(2).Expand())
        self.sizer.Add(sizer_rightside, wx.SizerFlags().Proportion(1).Expand())

        self.wrapper.Add(self.sizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=2)
        self.sizer.SetSizeHints(self.parent)  # this makes it expand to its proportional size at the start
        self.SetSizer(self.wrapper)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel_syringes.Close()
        self.panel_gas_mixers.Close()
        self.panel_dialysate_pumps.Close()
        self.Destroy()


class HardwareFrame(wx.Frame):
    def __init__(self, perfusion_system, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)

        self.sys = perfusion_system
        self.panel = HardwarePanel(self, self.sys)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        if self.panel:
            self.panel.Close()
        for child in self.GetChildren():
            child.Close()
        self.Destroy()


class MyHardwareApp(wx.App):
    def OnInit(self):
        frame = HardwareFrame(sys, None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        # match approx size of window on Perfusion Laptop
        frame.SetSize((1666, 917))
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('app_hardware_control', logging.DEBUG)

    sys = PerfusionSystem()
    sys.open()
    sys.load_all()
    sys.load_automations()

    app = MyHardwareApp(0)
    app.MainLoop()
    sys.close()
