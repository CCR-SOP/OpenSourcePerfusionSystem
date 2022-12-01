# -*- coding: utf-8 -*-
""" Application to display all hardware control

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.

As of 20221130 - only setup for syringe control
"""
import logging

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import pyPerfusion.pyPump11Elite as pyPump11Elite
from pyPerfusion.panel_syringe import PanelSyringeControls

drugs = ['TPN + Bile Salts', 'Insulin', 'Glucagon', 'Heparin', 'Phenylephrine', 'Epoprostenol']
comports = ['COM12', 'COM9', 'COM11', 'COM10', 'COM7', 'COM8']
sizes = ['60', '60', '10', '60', '10', '10']  # sizes in mL
rates = [83.3, 4.2, 0, 3.33, 0, 10]  # uL/min.
target_vols = [0, 0, 0, 0, 0, 0]  # uL. 0 means basal rate or off to start
# TODO: Insulin, glucagon need the target_vol updated by Dexcom

class HardwareFrame(wx.Frame):
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
            SpecificConfig = pyPump11Elite.SyringeConfig(drug=drugs[x], comport=comports[x], size=sizes[x],
                                                         init_injection_rate=rates[x],
                                                         init_target_volume=target_vols[x])
            # does the line above actually work for saving and updating the config?
            syringe = pyPump11Elite.Pump11Elite(name=drugs[x], config=SpecificConfig)
            self.syringes.append(syringe)
            self.panel[drugs[x]] = PanelSyringeControls(parent=self, syringe=syringe, start_rate=rates[x],
                                                        start_vol=target_vols[x])
            sizer.Add(self.panel[drugs[x]], 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)


    def OnClose(self, evt):  # UPDATE
        for syringe in self.syringes:
            syringe.stop()
        for panel in self.panel.keys():
            self.panel[panel].Destroy()
        self.Destroy()


class MyHardwareApp(wx.App):
    def OnInit(self):
        frame = HardwareFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    app = MyHardwareApp(0)
    app.MainLoop()