# -*- coding: utf-8 -*-
""" Application to display all hardware control

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.panel_multiple_syringes import SyringePanel
from pyPerfusion.panel_DialysisPumps import DialysisPumpPanel
from pyPerfusion.panel_SPCStockertPumps import CentrifugalPumpPanel
from pyPerfusion.panel_gas_mixers import GasMixerPanel

from pyPerfusion.pyGB100_SL import GasControl
import pyPerfusion.pyCDI as pyCDI
from pyPerfusion.SensorPoint import SensorPoint, ReadOnlySensorPoint
from pyPerfusion.FileStrategy import MultiVarToFile, MultiVarFromFile

utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
utils.configure_matplotlib_logging()

class HardwarePanel(wx.Panel):
    def __init__(self, parent, gas_control, cdi_object):
        self.parent = parent
        wx.Panel.__init__(self, parent)

        self.gas_control = gas_control
        self.cdi = cdi_object  # should everything be initialized like this?

        self._panel_syringes = SyringePanel(self)
        self._panel_centrifugal_pumps = CentrifugalPumpPanel(self)
        self._panel_dialysate_pumps = DialysisPumpPanel(self)
        self._panel_gas_mixers = GasMixerPanel(self, self.gas_control, self.cdi)
        self.sizer = wx.GridSizer(cols=2)  # label="Hardware Control App" - how can we put this in?

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()

        self.sizer.Add(self._panel_syringes, flags.Proportion(2))
        self.sizer.Add(self._panel_centrifugal_pumps, flags.Proportion(2))
        self.sizer.Add(self._panel_dialysate_pumps, flags.Proportion(2))
        self.sizer.Add(self._panel_gas_mixers, flags.Proportion(2))

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass

class HardwareFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = HardwarePanel(self, gas_control=gas_controller, cdi_object=cdi_obj)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.Destroy()


class MyHardwareApp(wx.App):
    def OnInit(self):
        frame = HardwareFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()

    gas_controller = GasControl()
    cdi_obj = pyCDI.CDIStreaming('CDI')
    cdi_obj.read_config()
    stream_cdi_to_file = SensorPoint(cdi_obj, 'NA')
    stream_cdi_to_file.add_strategy(strategy=MultiVarToFile('write', 1, 17))
    ro_sensor = ReadOnlySensorPoint(cdi_obj, 'na')
    read_from_cdi = MultiVarFromFile('multi_var', 1, 17, 1)
    ro_sensor.add_strategy(strategy=read_from_cdi)
    stream_cdi_to_file.start()
    cdi_obj.start()

    app = MyHardwareApp(0)
    app.MainLoop()
