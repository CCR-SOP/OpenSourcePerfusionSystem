# -*- coding: utf-8 -*-
"""
@author: Allen Luna
Test app for adjusting pump speeds to maintain desired perfusion pressures
"""
import wx
import logging
import pyPerfusion.utils as utils

from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.panel_AI import PanelAI
from pyPerfusion.SensorStream import SensorStream
from pyHardware.PHDserial import PHDserial
import pyPerfusion.PerfusionConfig as LP_CFG
from pytests.test_vasoactive_syringe import PanelTestVasoactiveSyringe

class PanelTestPressure(wx.Panel):
    def __init__(self, parent, sensor, name, dev, line):
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self._sensor = sensor
        self._name = name
        self._dev = dev
        self._line = line
        self._ao = NIDAQ_AO()

        wx.Panel.__init__(self, parent, -1)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

        self.label_desired_output = wx.StaticText(self, label='Desired ' + self._name)
        self.spin_desired_output = wx.SpinCtrlDouble(self, min=0.0, max=200, initial=65, inc=0.1)

        self.label_tolerance = wx.StaticText(self, label='Tolerance (mmHg)')
        self.spin_tolerance = wx.SpinCtrlDouble(self, min=0, max=100, initial=2, inc=0.01)

        self.label_increment = wx.StaticText(self, label='Voltage Increment')
        self.spin_increment = wx.SpinCtrlDouble(self, min=0, max=1, initial=0.05, inc=0.001)

        self.btn_stop = wx.ToggleButton(self, label='Start')

        self.__do_layout()
        self.__set_bindings()

        self.timer_pressure_adjust = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Left().Proportion(0)

        self.sizer_label = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_label.Add(self.label_desired_output, flags)
        self.sizer_label.Add(self.spin_desired_output, flags)

        self.sizer_tol = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_tol.Add(self.label_tolerance, flags)
        self.sizer_tol.Add(self.spin_tolerance, flags)

        self.sizer_increment = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_increment.Add(self.label_increment, flags)
        self.sizer_increment.Add(self.spin_increment, flags)

        sizer = wx.GridSizer(cols=1)
        sizer.Add(self.sizer_label)
        sizer.Add(self.sizer_tol)
        sizer.Add(self.sizer_increment, flags)
        sizer.Add(self.btn_stop, flags)
        self.sizer.Add(sizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_stop.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartStop)

    def OnStartStop(self, evt):
        state = self.btn_stop.GetLabel()
        if state == 'Start':
            self._ao.open(period_ms=100, dev=self._dev, line=self._line)
            self._ao.set_dc(1)
            self.timer_pressure_adjust.Start(3000, wx.TIMER_CONTINUOUS)
            self.btn_stop.SetLabel('Stop')
        else:
            self.timer_pressure_adjust.Stop()
            self._ao.set_dc(0)
            self._ao.close()
            self._ao.halt()
            self.btn_stop.SetLabel('Start')

    def OnTimer(self, event):
        if event.GetId() == self.timer_pressure_adjust.GetId():
            self.update_output()

    def update_output(self):
        pressure = float(self._sensor.get_current())
        desired = float(self.spin_desired_output.GetValue())
        tol = float(self.spin_tolerance.GetValue())
        inc = float(self.spin_increment.GetValue())
        dev = abs(desired - pressure)
      #  print(f'Pressure is {pressure:.3f}, desired is {desired:.3f}')
      #  print(f'Deviation is {dev}, tol is {tol}')
        if dev > tol:
            if pressure < desired:
                new_val = self._ao._volts_offset + inc
                if new_val > 5:
                    new_val = 5
            else:
                new_val = self._ao._volts_offset - inc
                if new_val < 0:
                    new_val = 0
            if "Hepatic Artery" in self._sensor.name:
                self._ao.set_sine(new_val/12, new_val, Hz=1)
            else:
                self._ao.set_dc(new_val)

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.FlexGridSizer(cols=3)
        self.acq =  NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
        self.pressure_sensors = {
            SensorStream('Hepatic Artery Pressure', 'mmHg', self.acq): ['Dev3', 1],
            SensorStream('Portal Vein Pressure', 'mmHg', self.acq): ['Dev3', 0]
        }

        self.flow_sensors = [SensorStream('Portal Vein Flow', 'L/min', self.acq), SensorStream('Hepatic Artery Flow', 'ml/min', self.acq)]

        for sensor, pump in self.pressure_sensors.items():
            sizer.Add(PanelAI(self, sensor, name=sensor.name), 1, wx.ALL | wx.EXPAND, border=1)
            sizer.Add(PanelAI(self, self.flow_sensors[pump[1]], name=self.flow_sensors[pump[1]].name), 1, wx.ALL | wx.EXPAND, border=1)
            sizer.Add(PanelTestPressure(self, sensor, name=sensor.name, dev=pump[0], line=pump[1]), 1, wx.ALL | wx.EXPAND, border=1)

        self._IVC_pressure = SensorStream('Inferior Vena Cava Pressure', 'mmHg', self.acq)

        sizer.Add(PanelAI(self, self._IVC_pressure, name=self._IVC_pressure.name), 1, wx.ALL | wx.EXPAND, border=1)

        heparin_methylprednisolone_injection = PHDserial('Heparin and Methylprednisolone')
        heparin_methylprednisolone_injection.open('COM13', 9600)
        heparin_methylprednisolone_injection.ResetSyringe()
        heparin_methylprednisolone_injection.open_stream(LP_CFG.LP_PATH['stream'])
        heparin_methylprednisolone_injection.start_stream()

        tpn_bilesalts_injection = PHDserial('TPN and Bile Salts')
        tpn_bilesalts_injection.open('COM10', 9600)
        tpn_bilesalts_injection.ResetSyringe()
        tpn_bilesalts_injection.open_stream(LP_CFG.LP_PATH['stream'])
        tpn_bilesalts_injection.start_stream()

        epoprostenol_injection = PHDserial('Epoprostenol')
        epoprostenol_injection.open('COM11', 9600)
        epoprostenol_injection.ResetSyringe()
        epoprostenol_injection.open_stream(LP_CFG.LP_PATH['stream'])
        epoprostenol_injection.start_stream()

        phenylephrine_injection = PHDserial('Phenylephrine')
        phenylephrine_injection.open('COM4', 9600)
        phenylephrine_injection.ResetSyringe()
        phenylephrine_injection.open_stream(LP_CFG.LP_PATH['stream'])
        phenylephrine_injection.start_stream()

        self._syringes = [heparin_methylprednisolone_injection, tpn_bilesalts_injection, epoprostenol_injection, phenylephrine_injection]
        self.sizer_syringes = wx.GridSizer(cols=2)
        self.sizer_syringes.Add(PanelTestVasoactiveSyringe(self, None, 'Heparin and Methylprednisolone Syringe', heparin_methylprednisolone_injection), 1, wx.ALL | wx.EXPAND, border=1)
        self.sizer_syringes.Add(PanelTestVasoactiveSyringe(self, None, 'TPN and Bile Salts Syringe', tpn_bilesalts_injection), 1, wx.ALL | wx.EXPAND, border=1)
        sizer.Add(self.sizer_syringes, 1, wx.EXPAND, border=2)
        self.sizer_syringes = wx.GridSizer(cols=2)
        self.sizer_syringes.Add(PanelTestVasoactiveSyringe(self, self.flow_sensors[1], 'Epoprostenol Syringe', epoprostenol_injection), 1, wx.ALL | wx.EXPAND, border=1)
        self.sizer_syringes.Add(PanelTestVasoactiveSyringe(self, self.flow_sensors[1], 'Phenylephrine Syringe', phenylephrine_injection), 1, wx.ALL | wx.EXPAND, border=1)
        sizer.Add(self.sizer_syringes, 1, wx.EXPAND, border=2)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for syringe in self._syringes:
            infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
            syringe.stop(-1, infuse_rate, ml_volume, ml_min_rate)
            syringe.stop_stream()
        for sensor in self.pressure_sensors.keys():
            sensor.stop()
        self._IVC_pressure.stop()
        self.Destroy()

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    LP_CFG.set_base(basepath='~/Documents/LPTEST')
    LP_CFG.update_stream_folder()
    utils.setup_default_logging(filename='panel_pressure_controlled_perfusion_syringes')
    app = MyTestApp(0)
    app.MainLoop()
