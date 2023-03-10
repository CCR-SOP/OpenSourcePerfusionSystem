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

drugs = ['TPN + Bile Salts', 'Insulin', 'Zosyn', 'Methylprednisone', 'Phenylephrine', 'Epoprostenol']

# TODO: Insulin, glucagon need the target_vol updated by Dexcom
utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
utils.configure_matplotlib_logging()


class SyringePanel(wx.Panel):  # does not expand to correct size by itself now
    def __init__(self, parent, syringes):
        self.parent = parent
        wx.Panel.__init__(self, parent)
        self.syringes = syringes
        sizer = wx.GridSizer(cols=2)

        self.panel = {}
        i = 0
        for syringe in self.syringes:
            self.panel[drugs[i]] = PanelSyringeControls(parent=self, syringe=syringe)
            self.panel[drugs[i]].update_controls_from_config()
            sizer.Add(self.panel[drugs[i]], 1, wx.ALL | wx.EXPAND, border=1)
            i += 1

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

        self.panel = SyringePanel(self, syringes=syringe_array)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel.OnClose(self)
        self.Destroy()


class MySyringeApp(wx.App):
    def OnInit(self):
        frame = SyringeFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()

    syringe_array = []
    for x in range(6):
        SpecificConfig = pyPump11Elite.SyringeConfig(drug=drugs[x])
        new_syringe = pyPump11Elite.Pump11Elite(name=drugs[x], config=SpecificConfig)
        new_syringe.read_config()
        syringe_array.append(new_syringe)

    app = MySyringeApp(0)
    app.MainLoop()
