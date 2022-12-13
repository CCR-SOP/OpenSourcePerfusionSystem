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

drugs = ['TPN + Bile Salts', 'Insulin', 'Glucagon', 'Heparin', 'Phenylephrine', 'Epoprostenol']

# TODO: Insulin, glucagon need the target_vol updated by Dexcom

class SyringeFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=2)
        utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
        utils.configure_matplotlib_logging()

        # Initialize syringes with corresponding panels
        self.syringes = []
        self.panel = {}
        for x in range(6):
            SpecificConfig = pyPump11Elite.SyringeConfig(drug=drugs[x])
            syringe = pyPump11Elite.Pump11Elite(name=drugs[x], config=SpecificConfig)
            syringe.read_config()

            self.syringes.append(syringe)
            self.panel[drugs[x]] = PanelSyringeControls(parent=self, syringe=syringe)
            self.panel[drugs[x]].update_controls_from_config()
            sizer.Add(self.panel[drugs[x]], 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)


    def OnClose(self, evt):
        for syringe in self.syringes:
            syringe.stop()
        for panel in self.panel.keys():
            self.panel[panel].Destroy()  # this threw an error suddenly?
        self.Destroy()


class MySyringeApp(wx.App):
    def OnInit(self):
        frame = SyringeFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    app = MySyringeApp(0)
    app.MainLoop()
