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
        wx.Panel.__init__(self, parent)
        self._lgr = logging.getLogger(__name__)
        self.automations = automations

        font = wx.Font()
        font.SetPointSize(int(16))
        static_box = wx.StaticBox(self, wx.ID_ANY, label="Syringe Pumps")
        static_box.SetFont(font)
        self.wrapper = wx.StaticBoxSizer(static_box, wx.VERTICAL)
        self.sizer = wx.GridSizer(cols=2)
        self.sizer2 = wx.FlexGridSizer(rows=1, cols=3, hgap=1, vgap=1)

        self.panels = []
        for automation in self.automations:
            self._lgr.debug(automation)
            panel = PanelSyringeControls(self, automation)
            self.panels.append(panel)

        # Add auto start buttons and log
        auto_font = wx.Font()
        auto_font.SetPointSize(int(14))
        self.btn_auto_glucose = wx.Button(self, label='Start Auto Glucose Control')
        self.btn_auto_glucose.SetFont(auto_font)
        self.btn_auto_glucose.SetBackgroundColour(wx.Colour(0, 240, 0))
        self.btn_auto_vaso = wx.Button(self, label='Start Auto Vasoactive Control')
        self.btn_auto_vaso.SetFont(auto_font)
        self.btn_auto_vaso.SetBackgroundColour(wx.Colour(0, 240, 0))
        self.text_log_syringes = utils.create_log_display(self, logging.INFO, ['Insulin'])  # have this do all syringes... currently outputting nothing

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
        counter = 0
        if self.btn_auto_glucose.GetLabel() == "Start Auto Glucose Control":
            self.btn_auto_glucose.SetLabel("Stop Auto Glucose Control")
            self.btn_auto_glucose.SetBackgroundColour(wx.Colour(240, 0, 0))
            for panel in self.panels:
                if counter < 2:
                    panel.spin_rate.Enable(False)
                    panel.spin_volume.Enable(False)
                    panel.btn_basal.Enable(False)
                    panel.automation.start()
                counter += 1
        else:
            self.btn_auto_glucose.SetLabel("Start Auto Glucose Control")
            self.btn_auto_glucose.SetBackgroundColour(wx.Colour(0, 240, 0))
            for panel in self.panels:
                if counter < 2:
                    panel.spin_rate.Enable(True)
                    panel.spin_volume.Enable(True)
                    panel.btn_basal.Enable(True)
                    panel.automation.stop()
                counter += 1

    def on_auto_vaso(self, evt):
        counter = 0
        if self.btn_auto_vaso.GetLabel() == "Start Auto Vasoactive Control":
            self.btn_auto_vaso.SetLabel("Stop Auto Vasoactive Control")
            self.btn_auto_vaso.SetBackgroundColour(wx.Colour(240, 0, 0))
            for panel in self.panels:
                if 1 < counter < 4:
                    panel.spin_rate.Enable(False)
                    panel.spin_volume.Enable(False)
                    panel.btn_basal.Enable(False)
                    panel.automation.start()
                counter += 1
        else:
            self.btn_auto_vaso.SetLabel("Start Auto Vasoactive Control")
            self.btn_auto_vaso.SetBackgroundColour(wx.Colour(0, 240, 0))
            for panel in self.panels:
                if 1 < counter < 4:
                    panel.spin_rate.Enable(True)
                    panel.spin_volume.Enable(True)
                    panel.btn_basal.Enable(True)  # cannot do this w basal button since it's not a toggle
                    panel.automation.stop()
                counter += 1

    def OnClose(self, evt):  # not working --> double check
        for panel in self.panels:
            panel.Close()


class SyringeFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)

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
    lgr = logging.getLogger()
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(lgr, logging.DEBUG)
    utils.setup_file_logger(lgr, logging.DEBUG, 'panel_multiple_syringes_debug')

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

