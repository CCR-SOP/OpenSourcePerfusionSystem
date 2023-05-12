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


class SyringePanel(wx.Panel):
    def __init__(self, parent, automations):
        super().__init__(parent)
        self._lgr = logging.getLogger(__name__)
        self.automations = automations

        font = wx.Font()
        font.SetPointSize(int(16))
        self.static_box = wx.StaticBox(self, wx.ID_ANY, label="Syringe Pumps")
        self.static_box.SetFont(font)
        self.wrapper = wx.StaticBoxSizer(self.static_box, wx.VERTICAL)
        self.sizer = wx.GridSizer(cols=2)
        self.sizer2 = wx.FlexGridSizer(rows=1, cols=3, hgap=1, vgap=1)

        self.panels = []
        self.panels_vaso = []
        self.panels_glucose = []
        for automation in self.automations:
            self._lgr.warning(automation.device.name)
            panel = PanelSyringeControls(self, automation)
            self.panels.append(panel)
            if automation.device.name == 'Epoprostenol' or automation.device.name == 'Phenylephrine':
                self.panels_vaso.append(panel)
                self._lgr.warning(f' Added {automation.device.name} to panels_vaso')
            elif automation.device.name == 'Glucagon' or automation.device.name == 'Insulin':
                self.panels_glucose.append(panel)
                self._lgr.warning(f' Added {automation.device.name} to panels_glucose')

        # Add auto start buttons and log
        auto_font = wx.Font()
        auto_font.SetPointSize(int(14))
        self.btn_auto_glucose = wx.Button(self, label='Start Auto Glucose Control')
        self.btn_auto_glucose.SetFont(auto_font)
        self.btn_auto_glucose.SetBackgroundColour(wx.Colour(0, 240, 0))
        self.btn_auto_vaso = wx.Button(self, label='Start Auto Vasoactive Control')
        self.btn_auto_vaso.SetFont(auto_font)
        self.btn_auto_vaso.SetBackgroundColour(wx.Colour(0, 240, 0))
        log_names = []
        for automation in self.automations:
            log_names.append(automation.device.name)
        log_names.append('AutoSyringe')
        self.text_log_syringes = utils.create_log_display(self, logging.INFO, log_names, use_last_name=True)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags(1)
        flags.Expand().Border(wx.ALL, 10)

        for panel in self.panels:
            self.sizer.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)
        self.sizer2.Add(self.btn_auto_glucose, flags)
        self.sizer2.Add(self.btn_auto_vaso, flags)
        self.sizer2.Add(self.text_log_syringes, flags)

        self.sizer2.AddGrowableCol(0, 1)
        self.sizer2.AddGrowableCol(1, 1)
        self.sizer2.AddGrowableCol(2, 3)

        self.sizer.SetSizeHints(self.GetParent())
        self.wrapper.Add(self.sizer, flag=wx.ALL | wx.EXPAND, border=1)
        self.wrapper.Add(self.sizer2, flag=wx.ALL | wx.EXPAND, border=1)
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

        automation_names = ['Insulin Automation', 'Glucagon Automation',
                            'Phenylephrine Automation', 'Epoprostenol Automation',
                            'TPN + Bile Salts Manual', 'Zosyn Manual']
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

