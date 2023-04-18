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
    def __init__(self, parent, syringe_sensors):
        self.parent = parent
        wx.Panel.__init__(self, parent)
        self.syringes = []

        font_panel_label = wx.Font()
        font_panel_label.SetPointSize(int(12))
        static_box = wx.StaticBox(self, wx.ID_ANY, label="Syringe Infusions")
        static_box.SetFont(font_panel_label)
        self.wrapper = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)
        sizer = wx.GridSizer(cols=2)

        self.panel = {}

        for syringe in syringe_sensors:
            # Initialize panel
            self.panel[syringe.name] = PanelSyringeControls(parent=self, sensor=syringe)
            self.panel[syringe.name].update_controls_from_config()
            sizer.Add(self.panel[syringe.name], 1, wx.ALL | wx.EXPAND, border=1)

        sizer.SetSizeHints(self.parent)
        self.wrapper.Add(sizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=2)
        self.SetSizer(self.wrapper)
        self.Fit()
        self.Layout()

    def OnClose(self, evt):
        for panel in self.panel.keys():
            self.panel[panel].Close()


class SyringeFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = SyringePanel(self, syringes)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel.OnClose(self)
        sys.close()
        self.Destroy()


class MySyringeApp(wx.App):
    def OnInit(self):
        frame = SyringeFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()

    sys = PerfusionSystem()
    sys.load_all()
    sys.open()

    drugs = ['TPN + Bile Salts', 'Insulin', 'Zosyn', 'Methylprednisone', 'Phenylephrine', 'Epoprostenol']
    syringes = []
    for drug in drugs:
        syringes.append(sys.get_sensor(drug))

    app = MySyringeApp(0)
    app.MainLoop()
