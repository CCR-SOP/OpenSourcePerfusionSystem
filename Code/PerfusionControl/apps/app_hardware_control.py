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
from pyPerfusion.PerfusionSystem import PerfusionSystem
from pyPerfusion.Sensor import Sensor
from pyPerfusion.pyAutoGasMixer import AutoGasMixerVenous, AutoGasMixerArterial
from pyPerfusion.pyAutoDialysis import AutoDialysisInflow, AutoDialysisOutflow


class HardwarePanel(wx.Panel):
    def __init__(self, parent, perfusion_system):
        self.parent = parent
        wx.Panel.__init__(self, parent)
        self._lgr = logging.getLogger('HardwareControl')

        pump_names = ['Dialysate Inflow Pump', 'Dialysate Outflow Pump', 'Dialysis Blood Pump', 'Glucose Circuit Pump']
        pumps = []
        for pump_name in pump_names:
            temp_sensor = Sensor(name=pump_name)
            temp_sensor.read_config()
            pumps.append(temp_sensor)

        self.ha_autogasmixer = AutoGasMixerArterial(name='HA Auto Gas Mixer',
                                                    gas_device=perfusion_system.get_sensor('Arterial Gas Mixer').hw,
                                                    cdi_reader=perfusion_system.get_sensor('CDI').get_reader())
        self.pv_autogasmixer = AutoGasMixerVenous(name='PV Auto Gas Mixer',
                                                  gas_device=perfusion_system.get_sensor('Venous Gas Mixer').hw,
                                                  cdi_reader=perfusion_system.get_sensor('CDI').get_reader())

        drugs = ['TPN + Bile Salts', 'Insulin', 'Zosyn', 'Methylprednisone', 'Phenylephrine', 'Epoprostenol']
        syringes = []
        for drug in drugs:
            syringes.append(perfusion_system.get_sensor(drug))

        self.auto_inflow = AutoDialysisInflow(name='Dialysate Inflow Automation')
        self.auto_inflow.pump = perfusion_system.get_sensor('Dialysate Inflow Pump').hw
        self.auto_inflow.cdi_reader = perfusion_system.get_sensor('CDI').get_reader()
        self.auto_inflow.read_config()

        self.auto_outflow = AutoDialysisOutflow(name='Dialysate Outflow Automation')
        self.auto_outflow.pump = perfusion_system.get_sensor('Dialysate Outflow Pump').hw
        self.auto_outflow.cdi_reader = perfusion_system.get_sensor('CDI').get_reader()
        self.auto_outflow.read_config()

        self.panel_syringes = SyringePanel(self, syringes)
        self.panel_dialysate_pumps = DialysisPumpPanel(self,
                                                       pumps,
                                                       perfusion_system.get_sensor('CDI').get_reader(),
                                                       auto_inflow=self.auto_inflow,
                                                       auto_outflow=self.auto_outflow)
        self.panel_gas_mixers = GasMixerPanel(self, self.ha_autogasmixer, self.pv_autogasmixer,
                                              cdi_reader=perfusion_system.get_sensor('CDI').get_reader())

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
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self._lgr.debug('closing')
        self.ha_autogasmixer.stop()
        self._lgr.debug('stopped ha_autogasmixer')
        self.pv_autogasmixer.stop()
        self._lgr.debug('stopped pv_autogasmixer')
        self.auto_inflow.stop()
        self._lgr.debug('stopped auto_inflow')
        self.auto_outflow.stop()
        self._lgr.debug('stopped auto_outflow')
        self._lgr.debug('closing')
        self.panel_syringes.Close()
        self._lgr.debug(' panel_syringes closed')
        self.panel_gas_mixers.Close()
        self._lgr.debug(' panel_gas_mixers closed')
        self.panel_dialysate_pumps.Close()
        self._lgr.debug(' panel_dialysate_pumps closed')
        self.Destroy()


class HardwareFrame(wx.Frame):
    def __init__(self, perfusion_system, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)

        self.sys = perfusion_system
        self.panel = HardwarePanel(self, self.sys)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.sys.close()
        self.Destroy()


class MyHardwareApp(wx.App):
    def OnInit(self):
        frame = HardwareFrame(sys, None, wx.ID_ANY, "")
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

    app = MyHardwareApp(0)
    app.MainLoop()
    sys.close()
