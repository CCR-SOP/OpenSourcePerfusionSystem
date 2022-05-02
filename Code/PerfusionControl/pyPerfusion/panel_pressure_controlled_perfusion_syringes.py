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
from pyPerfusion.FileStrategy import StreamToFile
from pyPerfusion.ProcessingStrategy import RMSStrategy

class PanelPressureFlowControl(wx.Panel):
    def __init__(self, parent, sensor, name, dev, line):
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self._sensor = sensor
        self._name = name
        self._dev = dev
        self._line = line
        self._ao = NIDAQ_AO()

        self._desired = None
        self._tolerance = None
        self._increment = None
        self._divisor = None

        wx.Panel.__init__(self, parent, -1)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

        self.label_desired_output = wx.StaticText(self, label='Desired ' + self._name)
        if 'Pressure' in self._name:
            desired = 65
        elif 'Flow' in self._name:
            desired = 200
        else:
            desired = 0
        self.spin_desired_output = wx.SpinCtrlDouble(self, min=0.0, max=500, initial=desired, inc=0.1)
        self.btn_update_desired = wx.Button(self, label='Update Desired Parameter')

        self.label_tolerance = wx.StaticText(self, label='Tolerance (' + self._sensor._unit_str + ')')
        self.spin_tolerance = wx.SpinCtrlDouble(self, min=0, max=100, initial=0, inc=0.01)
        self.btn_update_tolerance = wx.Button(self, label='Update Tolerance')

        self.label_increment = wx.StaticText(self, label='Voltage Increment')
        self.spin_increment = wx.SpinCtrlDouble(self, min=0, max=1, initial=0.05, inc=0.001)
        self.btn_update_increment = wx.Button(self, label='Update Voltage Increment')

        self.label_divisor = wx.StaticText(self, label='Peak-to-Peak Divisor')
        self.spin_divisor = wx.SpinCtrlDouble(self, min=0, max=100, initial=10, inc=0.1)
        self.btn_update_divisor = wx.Button(self, label='Update Divisor')
        if 'Portal Vein' in self._name:
            self.btn_update_divisor.Enable(False)

        self.btn_stop = wx.ToggleButton(self, label='Start')

        self.__do_layout()
        self.__set_bindings()

        self.timer_adjust = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Left().Proportion(0)

        self.sizer_label = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_label.Add(self.label_desired_output, flags)
        self.sizer_label.Add(self.spin_desired_output, flags)
        self.sizer_label.Add(self.btn_update_desired, flags)

        self.sizer_tol = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_tol.Add(self.label_tolerance, flags)
        self.sizer_tol.Add(self.spin_tolerance, flags)
        self.sizer_tol.Add(self.btn_update_tolerance, flags)

        self.sizer_increment = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_increment.Add(self.label_increment, flags)
        self.sizer_increment.Add(self.spin_increment, flags)
        self.sizer_increment.Add(self.btn_update_increment, flags)

        self.sizer_divisor = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_divisor.Add(self.label_divisor, flags)
        self.sizer_divisor.Add(self.spin_divisor, flags)
        self.sizer_divisor.Add(self.btn_update_divisor, flags)

        sizer = wx.GridSizer(cols=1)
        sizer.Add(self.sizer_label)
        sizer.Add(self.sizer_tol)
        sizer.Add(self.sizer_increment, flags)
        sizer.Add(self.btn_stop, flags)
        sizer.Add(self.sizer_divisor, flags)
        self.sizer.Add(sizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_stop.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartStop)
        self.btn_update_desired.Bind(wx.EVT_BUTTON, self.OnDesired)
        self.btn_update_tolerance.Bind(wx.EVT_BUTTON, self.OnTolerance)
        self.btn_update_increment.Bind(wx.EVT_BUTTON, self.OnIncrement)
        self.btn_update_divisor.Bind(wx.EVT_BUTTON, self.OnDivisor)

    def OnStartStop(self, evt):
        state = self.btn_stop.GetLabel()
        if state == 'Start':
            self._ao.open(period_ms=100, dev=self._dev, line=self._line)
            self._ao.set_dc(1)
            self.timer_adjust.Start(3000, wx.TIMER_CONTINUOUS)
            self.btn_stop.SetLabel('Stop')
            self._desired = self.spin_desired_output.GetValue()
            self._tolerance = self.spin_tolerance.GetValue()
            self._increment = self.spin_increment.GetValue()
            self._divisor = self.spin_divisor.GetValue()
        else:
            self.timer_adjust.Stop()
            self._ao.set_dc(0)
            self._ao.close()
            self._ao.halt()
            self.btn_stop.SetLabel('Start')

    def OnDesired(self, evt):
        self._desired = self.spin_desired_output.GetValue()

    def OnTolerance(self, evt):
        self._tolerance = self.spin_tolerance.GetValue()

    def OnIncrement(self, evt):
        self._increment = self.spin_increment.GetValue()

    def OnDivisor(self, evt):
        self._divisor = self.spin_divisor.GetValue()

    def OnTimer(self, event):
        if event.GetId() == self.timer_adjust.GetId():
            self.update_output()

    def update_output(self):
        if 'Hepatic Artery' in self._sensor.name:
            t, value = self._sensor.get_file_strategy('StreamRMS').retrieve_buffer(0, 1)
        else:
            t, value = self._sensor.get_file_strategy('StreamRaw').retrieve_buffer(0, 1)
        dev = abs(self._desired - value)
      #  print(f'Pressure is {value:.3f}, desired is {desired:.3f}')
      #  print(f'Deviation is {dev}, tol is {tol}')
        if dev > self._tolerance:
            if value < self._desired:
                new_val = self._ao._volts_offset + self._increment
                if new_val > 5:
                    new_val = 5
            else:
                new_val = self._ao._volts_offset - self._increment
                if new_val < 0:
                    new_val = 0
            if "Hepatic Artery" in self._sensor.name:
                peak = (new_val / self._divisor) / 2
                if 5 < new_val + peak:
                    peak = (4.9-new_val)
                elif 0 > new_val - peak:
                    peak = (new_val - 0.1)
                self._ao.set_sine(2 * peak, new_val, Hz=1)
            else:
                self._ao.set_dc(new_val)

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.FlexGridSizer(cols=3)
        self.acq =  NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)

        self._sensors = [SensorStream('Hepatic Artery Pressure', 'mmHg', self.acq), SensorStream('Portal Vein Pressure', 'mmHg', self.acq), SensorStream('Hepatic Artery Flow', 'ml/min', self.acq), SensorStream('Portal Vein Flow', 'ml/min', self.acq), SensorStream('Inferior Vena Cava Pressure', 'mmHg', self.acq)]

        for sensor in self._sensors:
            raw = StreamToFile('StreamRaw', None, self.acq.buf_len)
            raw.open(LP_CFG.LP_PATH['stream'], f'{sensor.name}_raw', sensor.params)
            sensor.add_strategy(raw)
            if 'Hepatic Artery' in sensor.name:
                rms = RMSStrategy('RMS', 50, self.acq.buf_len)
                save_rms = StreamToFile('StreamRMS', None, self.acq.buf_len)
                save_rms.open(LP_CFG.LP_PATH['stream'], f'{sensor.name}_rms', sensor.params)
                sensor.add_strategy(rms)
                sensor.add_strategy(save_rms)

        HA_pressure = PanelAI(self, self._sensors[0], name=self._sensors[0].name, strategy='StreamRaw')
        HA_pressure._panel_cfg.choice_dev.SetStringSelection('Dev1')
        HA_pressure._panel_cfg.choice_line.SetSelection(0)
        HA_pressure._panel_cfg.choice_dev.Enable(False)
        HA_pressure._panel_cfg.choice_line.Enable(False)
        HA_pressure._panel_cfg.panel_cal.OnLoadCfg(True)
        sizer.Add(HA_pressure, 1, wx.ALL | wx.EXPAND, border=1)
        HA_flow = PanelAI(self, self._sensors[2], name=self._sensors[2].name, strategy='StreamRaw')
        HA_flow._panel_cfg.choice_dev.SetStringSelection('Dev1')
        HA_flow._panel_cfg.choice_line.SetSelection(3)
        HA_flow._panel_cfg.choice_dev.Enable(False)
        HA_flow._panel_cfg.choice_line.Enable(False)
        HA_flow._panel_cfg.panel_cal.OnLoadCfg(True)
        sizer.Add(HA_flow, 1, wx.ALL | wx.EXPAND, border=1)
        sizer.Add(PanelPressureFlowControl(self, self._sensors[0], name=self._sensors[0].name, dev='Dev3', line=1), 1, wx.ALL | wx.EXPAND, border=1)

        PV_pressure = PanelAI(self, self._sensors[1], name=self._sensors[1].name, strategy='StreamRaw')
        PV_pressure._panel_cfg.choice_dev.SetStringSelection('Dev1')
        PV_pressure._panel_cfg.choice_line.SetSelection(1)
        PV_pressure._panel_cfg.choice_dev.Enable(False)
        PV_pressure._panel_cfg.choice_line.Enable(False)
        PV_pressure._panel_cfg.panel_cal.OnLoadCfg(True)
        sizer.Add(PV_pressure, 1, wx.ALL | wx.EXPAND, border=1)
        PV_flow = PanelAI(self, self._sensors[3], name=self._sensors[3].name, strategy='StreamRaw')
        PV_flow._panel_cfg.choice_dev.SetStringSelection('Dev1')
        PV_flow._panel_cfg.choice_line.SetSelection(4)
        PV_flow._panel_cfg.choice_dev.Enable(False)
        PV_flow._panel_cfg.choice_line.Enable(False)
        PV_flow._panel_cfg.panel_cal.OnLoadCfg(True)
        sizer.Add(PV_flow, 1, wx.ALL | wx.EXPAND, border=1)
        sizer.Add(PanelPressureFlowControl(self, self._sensors[3], name=self._sensors[3].name, dev='Dev3', line=0), 1, wx.ALL | wx.EXPAND, border=1)


        IVC_pressure = PanelAI(self, self._sensors[4], name=self._sensors[4].name, strategy='StreamRaw')
        IVC_pressure._panel_cfg.choice_dev.SetStringSelection('Dev1')
        IVC_pressure._panel_cfg.choice_line.SetSelection(2)
        IVC_pressure._panel_cfg.choice_dev.Enable(False)
        IVC_pressure._panel_cfg.choice_line.Enable(False)
        IVC_pressure._panel_cfg.panel_cal.OnLoadCfg(True)
        sizer.Add(IVC_pressure, 1, wx.ALL | wx.EXPAND, border=1)

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
        self.sizer_syringes.Add(PanelTestVasoactiveSyringe(self, self._sensors[2], 'Epoprostenol Syringe', epoprostenol_injection), 1, wx.ALL | wx.EXPAND, border=1)
        self.sizer_syringes.Add(PanelTestVasoactiveSyringe(self, self._sensors[2], 'Phenylephrine Syringe', phenylephrine_injection), 1, wx.ALL | wx.EXPAND, border=1)
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
        for sensor in self._sensors:
            sensor.stop()
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