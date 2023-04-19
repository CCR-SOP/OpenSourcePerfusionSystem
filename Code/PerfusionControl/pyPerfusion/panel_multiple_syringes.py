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
from pyPerfusion.panel_syringe import PanelSyringeControls
from pyPerfusion.PerfusionSystem import PerfusionSystem


class SyringePanel(wx.Panel):
    def __init__(self, parent, automations):
        wx.Panel.__init__(self, parent)
        self._lgr = logging.getLogger(__name__)

        self.panels = []

        for automation in automations:
            self._lgr.debug(automation)
            panel = PanelSyringeControls(self, automation)
            panel.update_controls_from_config()
            self.panels.append(panel)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()
        self.sizer = wx.GridSizer(cols=2)

        for panel in self.panels:
            self.sizer.Add(panel, flags)

        self.sizer.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.Layout()

    def __set_bindings(self):
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for panel in self.panels:
            panel.Close()


class SyringeFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)

        automation_names = ['Insulin Automation', 'Glucagon Automation',
                            'Phenylephrine Automation', 'Epoprostenol Automation']
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
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()

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

