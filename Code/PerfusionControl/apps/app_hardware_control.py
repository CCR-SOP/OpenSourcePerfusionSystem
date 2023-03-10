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

from pyHardware.pyDC_NIDAQ import NIDAQDCDevice
import pyHardware.pyDC as pyDC
from pyPerfusion.FileStrategy import StreamToFile
from pyPerfusion.SensorStream import SensorStream

utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
utils.configure_matplotlib_logging()

class HardwarePanel(wx.Panel):
    def __init__(self, parent, gas_control, roller_pumps, cdi_object):
        self.parent = parent
        wx.Panel.__init__(self, parent)

        self.gas_control = gas_control
        self.roller_pumps = roller_pumps
        self.cdi = cdi_object

        self._panel_syringes = SyringePanel(self)
        self._panel_centrifugal_pumps = CentrifugalPumpPanel(self)
        self._panel_dialysate_pumps = DialysisPumpPanel(self, self.roller_pumps, self.cdi)
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

        self.panel = HardwarePanel(self, gas_control=gas_controller, roller_pumps=r_pumps, cdi_object=cdi_obj)
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
        stream_cdi_to_file.stop()


class MyHardwareApp(wx.App):
    def OnInit(self):
        frame = HardwareFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()

    # TODO: Initialize syringe pump hardware here: requires changes to multiple_panel_syringes

    # Initialize gas controllers
    gas_controller = GasControl()

    # Initialize pumps
    r_pumps = {}
    rPumpNames = ["Dialysate Outflow Pump", "Dialysate Inflow Pump",
                  "Dialysis Blood Pump", "Glucose Circuit Pump"]
    for pumpName in rPumpNames:
        hw = NIDAQDCDevice()
        hw.cfg = pyDC.DCChannelConfig(name=pumpName)
        hw.read_config()
        sensor = SensorStream(hw, "ml/min")
        sensor.add_strategy(strategy=StreamToFile('Raw', 1, 10))
        r_pumps[pumpName] = sensor

    # Initialize CDI
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
