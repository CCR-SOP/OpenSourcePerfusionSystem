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
from pyPerfusion.panel_gas_mixers import GasMixerPanel
from pyHardware.SystemHardware import SYS_HW
from pyPerfusion.Sensor import Sensor

class HardwarePanel(wx.Panel):
    def __init__(self, parent, cdi_Sensor):
        self.parent = parent
        self.cdi_sensor = cdi_Sensor

        self.pump_names = ['Dialysate Inflow', 'Dialysate Outflow', 'Dialysis Blood', 'Glucose Circuit']

        # self.cdi_sensor = SYS_HW.get_hw('CDI')  # TODO: it doesn't like this here for some reason?
        # self.cdi_sensor.read_config()
        # wx.MessageBox(f'CDI hardware loaded')
        wx.Panel.__init__(self, parent)

        drugs = ['TPN + Bile Salts', 'Insulin', 'Zosyn', 'Methylprednisone', 'Phenylephrine', 'Epoprostenol']
        self.ha_mixer = SYS_HW.get_hw('Arterial Gas Mixer')
        self.pv_mixer = SYS_HW.get_hw('Venous Gas Mixer')

        self.panel_syringes = SyringePanel(self, drugs)
        self.panel_dialysate_pumps = DialysisPumpPanel(self, self.pump_names, self.cdi_sensor)
        self.panel_gas_mixers = GasMixerPanel(self, self.ha_mixer, self.pv_mixer, self.cdi_sensor)

        static_box = wx.StaticBox(self, wx.ID_ANY, label="Hardware Control App")
        self.wrapper = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()

        self.sizer = wx.GridSizer(cols=2)

        self.sizer.Add(self.panel_syringes, flags.Proportion(2))
        self.sizer.Add(self.panel_dialysate_pumps, flags.Proportion(2))
        self.sizer.Add(self.panel_gas_mixers, flags.Proportion(2))

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

        # Load CDI sensor
        cdi_sensor = Sensor(name='CDI')
        cdi_sensor.read_config()
        wx.MessageBox(f'CDI loaded')

        self.panel = HardwarePanel(self, cdi_sensor)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        SYS_HW.stop()
        self.panel.panel_syringes.OnClose(self)
        self.panel.panel_dialysate_pumps.close()
        self.panel.panel_dialysate_pumps.cdi_timer.Stop()
        self.panel.cdi_sensor.stop()
        for sensor in self.panel.panel_dialysate_pumps.sensors:
            sensor.stop()

        self.panel.panel_gas_mixers._panel_HA.sync_with_hw_timer.Stop()
        self.panel.panel_gas_mixers._panel_PV.sync_with_hw_timer.Stop()
        self.panel.panel_gas_mixers._panel_HA.cdi_timer.Stop()
        self.panel.panel_gas_mixers._panel_PV.cdi_timer.Stop()
        self.panel.panel_gas_mixers._panel_HA.gas_device.set_working_status(turn_on=False)
        self.panel.panel_gas_mixers._panel_PV.gas_device.set_working_status(turn_on=False)

        self.Destroy()


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
    SYS_HW.start()

    app = MyHardwareApp(0)
    app.MainLoop()
