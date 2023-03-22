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
from pyHardware.SystemHardware import SYS_HW

class HardwarePanel(wx.Panel):
    def __init__(self, parent, gas_control, roller_pumps, syringes, cdi_object):
        self.parent = parent
        wx.Panel.__init__(self, parent)

        self.gas_control = gas_control
        self.roller_pumps = roller_pumps
        self.syringes = syringes
        self.cdi = cdi_object

        drugs = ['TPN + Bile Salts', 'Insulin', 'Zosyn', 'Methylprednisone', 'Phenylephrine', 'Epoprostenol']

        self._panel_syringes = SyringePanel(self, drugs)
        self._panel_centrifugal_pumps = CentrifugalPumpPanel(self)
        self._panel_dialysate_pumps = DialysisPumpPanel(self, self.roller_pumps, self.cdi)
        self._panel_gas_mixers = GasMixerPanel(self, self.gas_control, self.cdi)

        static_box = wx.StaticBox(self, wx.ID_ANY, label="Hardware Control App")
        self.wrapper = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()

        self.sizer = wx.GridSizer(cols=2)

        self.sizer.Add(self._panel_syringes, flags.Proportion(2))
        self.sizer.Add(self._panel_centrifugal_pumps, flags.Proportion(2))
        self.sizer.Add(self._panel_dialysate_pumps, flags.Proportion(2))
        self.sizer.Add(self._panel_gas_mixers, flags.Proportion(2))

        self.wrapper.Add(self.sizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=2)
        self.sizer.SetSizeHints(self.parent)  # this makes it expand to its proportional size at the start
        self.SetSizer(self.wrapper)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass


class HardwareFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = HardwarePanel(self, gas_control=gas_controller, roller_pumps=r_pumps, syringes=syringe_array, cdi_object=cdi_obj)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.Destroy()

        self.panel._panel_syringes.OnClose(self)

        self.panel._panel_dialysate_pumps.close()
        self.panel._panel_dialysate_pumps.cdi_timer.Stop()

        self.panel._panel_gas_mixers._panel_HA.sync_with_hw_timer.Stop()
        self.panel._panel_gas_mixers._panel_PV.sync_with_hw_timer.Stop()
        self.panel._panel_gas_mixers._panel_HA.cdi_timer.Stop()
        self.panel._panel_gas_mixers._panel_PV.cdi_timer.Stop()
        self.panel._panel_gas_mixers._panel_HA.gas_device.set_working_status(turn_on=False)
        self.panel._panel_gas_mixers._panel_PV.gas_device.set_working_status(turn_on=False)

        cdi_obj.stop()


class MyHardwareApp(wx.App):
    def OnInit(self):
        frame = HardwareFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
    utils.configure_matplotlib_logging()

    SYS_HW.load_hardware_from_config()
    gas_controller = SYS_HW.get_hw('GasControl')
    cdi_obj = SYS_HW.get_hw('CDI')

    # look at ex_CDI_sensor

    app = MyHardwareApp(0)
    app.MainLoop()
