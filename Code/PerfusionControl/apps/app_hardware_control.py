# -*- coding: utf-8 -*-
""" Application to display all hardware control

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from gui.panel_multiple_syringes import SyringePanel
from gui.panel_DialysisPumps import DialysisPumpPanel
from gui.panel_gas_mixers import GasMixerPanel
from pyPerfusion.PerfusionSystem import PerfusionSystem
from pyPerfusion.pyAutoGasMixer import AutoGasMixerVenous, AutoGasMixerArterial
from pyPerfusion.pyAutoDialysis import AutoDialysisInflow, AutoDialysisOutflow


class HardwarePanel(wx.Panel):
    def __init__(self, parent, perfusion_system):
        self.parent = parent
        wx.Panel.__init__(self, parent)
        self._lgr = logging.getLogger('HardwareControl')

        pump_names = ['Dialysate Inflow Pump', 'Dialysate Outflow Pump', 'Dialysis Blood Pump', 'Glucose Circuit Pump']
        pumps = []
        for pump_name in pump_names:
            pumps.append(perfusion_system.get_sensor(pump_name))

        automation_names = ['Insulin Automation', 'Glucagon Automation',
                            'Phenylephrine Automation', 'Epoprostenol Automation',
                            'TPN + Bile Salts Manual', 'Zosyn Manual']
        automations = []
        for name in automation_names:
            automations.append(perfusion_system.get_automation(name))
        self.panel_syringes = SyringePanel(self, automations)

        automation_names = ['Dialysate Inflow Automation',
                            'Dialysate Outflow Automation',
                            'Dialysis Blood Automation',
                            'Glucose Circuit Automation']
        automations = []
        for name in automation_names:
            automations.append(perfusion_system.get_automation(name))
        self.panel_dialysate_pumps = DialysisPumpPanel(self, automations)

        automation_names = ['Arterial Gas Mixer Automation', 'Venous Gas Mixer Automation']
        automations = []
        for name in automation_names:
            automations.append(perfusion_system.get_automation(name))
        self.panel_gas_mixers = GasMixerPanel(self, automations)

        static_box = wx.StaticBox(self, wx.ID_ANY, label="Hardware Control App")
        self.wrapper = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()

        self.sizer = wx.GridSizer(cols=2)

        self.sizer.Add(self.panel_syringes, flags.Proportion(2))
        self.sizer.Add(self.panel_dialysate_pumps, flags.Proportion(2))
        self.sizer.Add(self.panel_gas_mixers, flags.Proportion(2))

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
        self.panel.Close()
        self.Destroy()


class MyHardwareApp(wx.App):
    def OnInit(self):
        frame = HardwareFrame(sys, None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()

    sys = PerfusionSystem()
    sys.open()
    sys.load_all()

    app = MyHardwareApp(0)
    app.MainLoop()
    sys.close()
