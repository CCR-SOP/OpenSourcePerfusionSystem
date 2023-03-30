# -*- coding: utf-8 -*-
""" Application to display dual gas mixer controls

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import time

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyHardware.SystemHardware import SYS_HW
from pyPerfusion.Sensor import Sensor
from pyPerfusion.panel_GB100 import BaseGasMixerPanel


class GasMixerPanel(wx.Panel):
    def __init__(self, parent, HA_mixer, PV_mixer, cdi):
        self.parent = parent
        wx.Panel.__init__(self, parent)

        self.cdi_sensor = cdi

        self._panel_HA = BaseGasMixerPanel(self, name='Arterial Gas Mixer', gas_device=HA_mixer, cdi=self.cdi_sensor)
        self._panel_PV = BaseGasMixerPanel(self, name='Venous Gas Mixer', gas_device=PV_mixer, cdi=self.cdi_sensor)
        static_box = wx.StaticBox(self, wx.ID_ANY, label="Gas Mixers")
        self.wrapper = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()
        self.sizer = wx.FlexGridSizer(rows=1, cols=2, vgap=1, hgap=1)

        self.sizer.Add(self._panel_HA, flags)
        self.sizer.Add(self._panel_PV, flags)

        self.sizer.AddGrowableCol(0, 1)
        self.sizer.AddGrowableCol(1, 1)

        self.sizer.SetSizeHints(self.parent)
        self.wrapper.Add(self.sizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=2)
        self.SetSizer(self.wrapper)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = GasMixerPanel(self, ha_mixer, pv_mixer, cdi=cdi_sensor)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel.cdi_sensor.stop()
        self.Destroy()

        self.panel._panel_HA.sync_with_hw_timer.Stop()
        self.panel._panel_PV.sync_with_hw_timer.Stop()
        self.panel._panel_HA.cdi_timer.Stop()
        self.panel._panel_PV.cdi_timer.Stop()
        self.panel._panel_HA.gas_device.set_working_status(turn_on=False)
        self.panel._panel_PV.gas_device.set_working_status(turn_on=False)

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)

    SYS_HW.load_hardware_from_config()
    ha_mixer = SYS_HW.get_hw('Arterial Gas Mixer')
    pv_mixer = SYS_HW.get_hw('Venous Gas Mixer')

    # Load CDI sensor
    cdi_sensor = Sensor(name='CDI')
    cdi_sensor.read_config()

    app = MyTestApp(0)
    app.MainLoop()
