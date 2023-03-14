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
import pyPerfusion.pyPump11Elite as pyPump11Elite
from pyPerfusion.panel_syringe import PanelSyringeControls
from pyHardware.SystemHardware import SYS_HW

drugs = ['TPN + Bile Salts', 'Insulin', 'Zosyn', 'Methylprednisone', 'Phenylephrine', 'Epoprostenol']


class SyringePanel(wx.Panel):  # does not expand to correct size by itself now
    def __init__(self, parent):
        self.parent = parent
        wx.Panel.__init__(self, parent)

        sizer = wx.GridSizer(cols=2)

        # Initialize syringes with corresponding panels
        self.syringes = []
        self.panel = {}
        for drug in drugs:
            syringe = SYS_HW.get_hw(drug)
            self.syringes.append(syringe)
            self.panel[drug] = PanelSyringeControls(parent=self, syringe=syringe)
            self.panel[drug].update_controls_from_config()
            sizer.Add(self.panel[drug], 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()

    def OnClose(self, evt):
        for syringe in self.syringes:
            syringe.stop()
        for panel in self.panel.keys():
            self.panel[panel].Destroy()


class SyringeFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = SyringePanel(self)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel.OnClose(self)
        SYS_HW.stop()
        self.Destroy()


class MySyringeApp(wx.App):
    def OnInit(self):
        frame = SyringeFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
    utils.configure_matplotlib_logging()

    SYS_HW.load_hardware_from_config()

    app = MySyringeApp(0)
    app.MainLoop()
