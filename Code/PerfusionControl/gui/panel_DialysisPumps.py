# -*- coding: utf-8 -*-
""" Application to display dialysis pump controls

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from gui.panel_DC import PanelDC
from pyPerfusion.PerfusionSystem import PerfusionSystem
from gui.panel_config import AutomationConfig


class DialysisPumpPanel(wx.Panel):
    def __init__(self, parent, automations):
        super().__init__(parent)
        self._lgr = logging.getLogger(__name__)
        self.automations = automations

        self.panels = []
        self.configs = []
        for automation in automations:
            panel = PanelDC(self, automation.pump)
            self.panels.append(panel)
            if automation.name == 'Dialysate Inflow Automation':
                config = AutomationConfig(self, automation)
                config.add_var('adjust_rate_ms', 'Adjust Rate (ms)', (0, 60 * 1_000, 60 * 60 * 1_000))  # TODO: make this minutes
                config.add_var('adjust_rate', 'Flow (ml/min)', (0, 0.1, 100), decimal_places=1)
                config.add_var('K_min', 'K (min)', limits=(0, 1, 10))
                config.add_var('K_max', 'K (max)', limits=(0, 1, 10))
                config.do_layout()
                config.set_bindings()
                self.configs.append(config)
            elif automation.name == 'Dialysate Outflow Automation':
                config = AutomationConfig(self, automation)
                config.add_var('adjust_rate_ms', 'Adjust Rate (ms)', (0, 60 * 1_000, 60 * 60 * 1_000))
                config.add_var('adjust_rate', 'Flow (ml/min)', (0, 0.1, 100), decimal_places=1)
                config.add_var('K_min', 'K (min)', limits=(0, 1, 10))
                config.add_var('K_max', 'K (max)', limits=(0, 1, 10))
                config.add_var('hct_min', 'hct (min)', limits=(0, 1, 100))
                config.add_var('hct_max', 'hct (max)', limits=(0, 1, 100))
                config.do_layout()
                config.set_bindings()
                self.configs.append(config)


        # Add log
        log_names = []
        for automation in self.automations:
            log_names.append(automation.pump.name)
        log_names.append('AutoDialysis')
        self.text_log_roller_pumps = utils.create_log_display(self, logging.INFO, log_names, use_last_name=True)

        # Add auto start button
        self.btn_auto_dialysis = wx.Button(self, label='Start Auto Dialysis', size=(100, 20))
        font =wx.Font()
        font.SetPointSize(8)
        self.btn_auto_dialysis.SetFont(font)
        # self.btn_auto_dialysis.SetBackgroundColour(wx.Colour(0, 240, 0))

        self.__do_layout()
        self.__set_bindings()

    def close(self):
        for panel in self.panels:
            panel.close()
        super().Close()

    def __do_layout(self):
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        pumpsizer = wx.GridSizer(3)
        for idx, panel in enumerate(self.panels):
            pumpsizer.Add(panel, flags=wx.SizerFlags().Expand())

        pumpsizer.Add(self.btn_auto_dialysis, wx.SizerFlags())

        configsizer = wx.BoxSizer(wx.VERTICAL)
        for config in self.configs:
            configsizer.Add(config, wx.SizerFlags().Proportion(0).Border(wx.RIGHT, 5))

        self.sizer.Add(pumpsizer, wx.SizerFlags().Proportion(2))
        self.sizer.Add(configsizer, wx.SizerFlags().Proportion(0))
        self.sizer.Add(self.text_log_roller_pumps, flags=wx.SizerFlags().Expand())

        self.sizer.SetSizeHints(self.GetParent())
        self.SetSizer(self.sizer)
        self.Fit()
        self.Layout()

    def __set_bindings(self):
        self.btn_auto_dialysis.Bind(wx.EVT_BUTTON, self.on_auto)
        for pane in self.configs:
            for pane in self.configs:
                pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_pane_changed)

    def on_auto(self, evt):
        if self.btn_auto_dialysis.GetLabel() == "Start Auto Dialysis":
            self.btn_auto_dialysis.SetLabel("Stop Auto Dialysis")
            self.btn_auto_dialysis.SetBackgroundColour(wx.Colour(240, 0, 0))
            for automation in self.automations:
                automation.start()
            for panel in self.panels:
                panel.panel_dc.spin_offset.Enable(False)
        else:
            self.btn_auto_dialysis.SetLabel("Start Auto Dialysis")
            self.btn_auto_dialysis.SetBackgroundColour(wx.Colour(0, 240, 0))
            for automation in self.automations:
                automation.stop()
            for panel in self.panels:
                panel.panel_dc.spin_offset.Enable(True)

    def on_pane_changed(self, evt):
        self.sizer.Layout()
        self.Layout()


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        automation_names = ['Dialysate Inflow Automation',
                            'Dialysate Outflow Automation',
                            'Dialysis Blood Automation']
        automations = []
        for name in automation_names:
            automations.append(SYS_PERFUSION.get_automation(name))
        self.panel = DialysisPumpPanel(self, automations)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel.close()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None)
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('panel_DialysisPumps', logging.DEBUG)

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

    app = MyTestApp(0)
    app.MainLoop()
    SYS_PERFUSION.close()
