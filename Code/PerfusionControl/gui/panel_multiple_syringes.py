# -*- coding: utf-8 -*-
""" Panel to display multiple (6) syringes together

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from gui.panel_syringe import PanelSyringeControls
from pyPerfusion.PerfusionSystem import PerfusionSystem
from gui.panel_config import AutomationConfig


class SyringePanel(wx.Panel):
    def __init__(self, parent, automations):
        super().__init__(parent)
        self._lgr = logging.getLogger(__name__)
        self.automations = automations

        font = wx.Font()
        font.SetPointSize(int(16))

        self.static_box = wx.StaticBox(self, wx.ID_ANY, label="Syringe Pumps")
        self.static_box.SetFont(font)

        self.wrapper = wx.StaticBoxSizer(self.static_box, wx.HORIZONTAL)
        flagsExpand = wx.SizerFlags(1)
        flagsExpand.Expand().Border(wx.ALL, 5)
        self.sizer = wx.FlexGridSizer(rows=3, cols=3, hgap=1, vgap=1)

        self.panels = []
        self.panels_vaso = []
        self.panels_glucose = []
        for automation in self.automations:
            panel = PanelSyringeControls(self, automation)
            self.sizer.Add(panel, proportion=1, flag=wx.ALL | wx.EXPAND, border=1)
            self.panels.append(panel)
            if automation.device.name == 'Epoprostenol' or automation.device.name == 'Phenylephrine':
                self.panels_vaso.append(panel)
            elif automation.device.name == 'Glucagon' or automation.device.name == 'Insulin':
                self.panels_glucose.append(panel)

        # Add auto start buttons
        auto_font = wx.Font()
        auto_font.SetPointSize(int(14))
        self.btn_auto_glucose = wx.Button(self, label='Start Auto Glucose Control')
        self.btn_auto_glucose.SetFont(auto_font)
        self.btn_auto_glucose.SetBackgroundColour(wx.Colour(0, 240, 0))
        self.sizer.Add(self.btn_auto_glucose, flagsExpand)

        self.btn_auto_vaso = wx.Button(self, label='Start Auto Vasoactive Control')
        self.btn_auto_vaso.SetFont(auto_font)
        self.btn_auto_vaso.SetBackgroundColour(wx.Colour(0, 240, 0))
        self.sizer.Add(self.btn_auto_vaso, flagsExpand)

        # Add log
        log_names = []
        for automation in self.automations:
            log_names.append(automation.device.name)
        log_names.append('AutoSyringe')
        self.text_log_syringes = utils.create_log_display(self, logging.INFO, log_names, use_last_name=True)
        self.sizer.Add(self.text_log_syringes, flagsExpand)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        self.sizer.AddGrowableRow(0, 1)
        self.sizer.AddGrowableRow(1, 1)
        self.sizer.AddGrowableRow(2, 2)
        self.sizer.AddGrowableCol(0, 1)
        self.sizer.AddGrowableCol(1, 1)
        self.sizer.AddGrowableCol(2, 1)

        self.sizer.SetSizeHints(self.GetParent())
        self.wrapper.Add(self.sizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=2)
        self.SetSizer(self.wrapper)
        self.Fit()
        self.Layout()

    def __set_bindings(self):
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.btn_auto_glucose.Bind(wx.EVT_BUTTON, self.on_auto_glucose)
        self.btn_auto_vaso.Bind(wx.EVT_BUTTON, self.on_auto_vaso)
        
    def on_auto_glucose(self, evt):
        if self.btn_auto_glucose.GetLabel() == "Start Auto Glucose Control":
            self.btn_auto_glucose.SetLabel("Stop Auto Glucose Control")
            self.btn_auto_glucose.SetBackgroundColour(wx.Colour(240, 0, 0))
            for panel in self.panels_glucose:
                panel.spin_rate.Enable(False)
                panel.spin_volume.Enable(False)
                panel.btn_basal.Enable(False)
                panel.btn_bolus.Enable(False)
                panel.automation.start()
        else:
            self.btn_auto_glucose.SetLabel("Start Auto Glucose Control")
            self.btn_auto_glucose.SetBackgroundColour(wx.Colour(0, 240, 0))
            for panel in self.panels_glucose:
                panel.spin_rate.Enable(True)
                panel.spin_volume.Enable(True)
                panel.btn_basal.Enable(True)
                panel.btn_bolus.Enable(True)
                panel.automation.stop()

    def on_auto_vaso(self, evt):
        if self.btn_auto_vaso.GetLabel() == "Start Auto Vasoactive Control":
            self.btn_auto_vaso.SetLabel("Stop Auto Vasoactive Control")
            self.btn_auto_vaso.SetBackgroundColour(wx.Colour(240, 0, 0))
            for panel in self.panels_vaso:
                panel.spin_rate.Enable(False)
                panel.spin_volume.Enable(False)
                panel.btn_basal.Enable(False)
                panel.btn_bolus.Enable(False)
                panel.automation.start()
        else:
            self.btn_auto_vaso.SetLabel("Start Auto Vasoactive Control")
            self.btn_auto_vaso.SetBackgroundColour(wx.Colour(0, 240, 0))
            for panel in self.panels_vaso:
                panel.spin_rate.Enable(True)
                panel.spin_volume.Enable(True)
                panel.btn_basal.Enable(True)
                panel.btn_bolus.Enable(True)
                panel.automation.stop()

    def OnClose(self, evt):
        for panel in self.panels:
            panel.Close()


class SyringeFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        automation_names = ['Insulin Automation', 'Epoprostenol Automation', 'TPN + Bile Salts Manual',
                            'Glucagon Automation', 'Phenylephrine Automation', 'Zosyn Manual']
        automations = []
        for name in automation_names:
            automations.append(SYS_PERFUSION.get_automation(name))
        self.panel = SyringePanel(self, automations)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel.Close()
        self.Destroy()


class MySyringeApp(wx.App):
    def OnInit(self):
        frame = SyringeFrame(None)
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('panel_multiple_syringes', logging.DEBUG)

    SYS_PERFUSION = PerfusionSystem()
    try:
        SYS_PERFUSION.open()
        SYS_PERFUSION.load_all()
        SYS_PERFUSION.load_automations()
    except Exception as e:
        # if anything goes wrong loading the perfusion system
        # close the hardware and exit the program
        SYS_PERFUSION.close()
        raise e

    app = MySyringeApp(0)
    app.MainLoop()
    SYS_PERFUSION.close()

