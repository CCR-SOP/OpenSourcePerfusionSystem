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
from pyPerfusion.panel_Syringe import PanelSyringe
from pyPerfusion.FileStrategy import StreamToFile
from pyPerfusion.ProcessingStrategy import RMSStrategy

class PanelPressureFlowControl(wx.Panel):
    def __init__(self, parent, sensor, pump, name, pumpname):
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self._sensor = sensor
        self._pump = pump
        self._name = name
        self._pumpname = pumpname

        section = LP_CFG.get_hwcfg_section(self._pumpname)
        self.dev = section['Device']
        self.line = section['LineName']
        self.desired = section['desired']
        self.tolerance = section['tolerance']
        self.increment = section['increment']
        try:
            self.divisor = section['divisor']
        except KeyError:
            self.divisor = None

        wx.Panel.__init__(self, parent, -1)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

        self.label_desired_output = wx.StaticText(self, label='Desired ' + self._name)
        self.spin_desired_output = wx.SpinCtrlDouble(self, min=0.0, max=500, initial=self.desired, inc=0.1)
        self.btn_update_desired = wx.Button(self, label='Update Desired Parameter')

        self.label_tolerance = wx.StaticText(self, label='Tolerance (' + self._sensor._unit_str + ')')
        self.spin_tolerance = wx.SpinCtrlDouble(self, min=0, max=100, initial=self.tolerance, inc=0.1)
        self.btn_update_tolerance = wx.Button(self, label='Update Tolerance')

        self.label_increment = wx.StaticText(self, label='Voltage Increment')
        self.spin_increment = wx.SpinCtrlDouble(self, min=0, max=1, initial=self.increment, inc=0.001)
        self.btn_update_increment = wx.Button(self, label='Update Voltage Increment')

        if self.divisor:
            self.label_divisor = wx.StaticText(self, label='Peak-to-Peak Divisor')
            self.spin_divisor = wx.SpinCtrlDouble(self, min=0, max=100, initial=self.divisor, inc=0.1)
            self.btn_update_divisor = wx.Button(self, label='Update Divisor')

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

        if self.divisor:
            self.sizer_divisor = wx.BoxSizer(wx.HORIZONTAL)
            self.sizer_divisor.Add(self.label_divisor, flags)
            self.sizer_divisor.Add(self.spin_divisor, flags)
            self.sizer_divisor.Add(self.btn_update_divisor, flags)

        sizer = wx.GridSizer(cols=1)
        sizer.Add(self.sizer_label)
        sizer.Add(self.sizer_tol)
        sizer.Add(self.sizer_increment, flags)
        sizer.Add(self.btn_stop, flags)
        if self.divisor:
            sizer.Add(self.sizer_divisor, flags)
        self.sizer.Add(sizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_update_desired.Bind(wx.EVT_BUTTON, self.OnDesired)
        self.btn_update_tolerance.Bind(wx.EVT_BUTTON, self.OnTolerance)
        self.btn_update_increment.Bind(wx.EVT_BUTTON, self.OnIncrement)
        self.btn_update_divisor.Bind(wx.EVT_BUTTON, self.OnDivisor)
        self.btn_stop.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartStop)

    def OnDesired(self, evt):
        self.desired = self.spin_desired_output.GetValue()

    def OnTolerance(self, evt):
        self.tolerance = self.spin_tolerance.GetValue()

    def OnIncrement(self, evt):
        self.increment = self.spin_increment.GetValue()

    def OnDivisor(self, evt):
        self.divisor = self.spin_divisor.GetValue()

    def OnStartStop(self, evt):
        state = self.btn_stop.GetLabel()
        if state == 'Start':
            self._pump.open(period_ms=100, dev=self.dev, line=self.line)
            self._pump.set_dc(1.5)
            self.desired = self.spin_desired_output.GetValue()
            self.tolerance = self.spin_tolerance.GetValue()
            self.increment = self.spin_increment.GetValue()
            if self.divisor:
                self.divisor = self.spin_divisor.GetValue()
            self.timer_adjust.Start(3000, wx.TIMER_CONTINUOUS)
            self.btn_stop.SetLabel('Stop')
        else:
            self.timer_adjust.Stop()
            self._pump.set_dc(0)
            self._pump.close()
            self._pump.halt()
            self.btn_stop.SetLabel('Start')

    def OnTimer(self, event):
        if event.GetId() == self.timer_adjust.GetId():
            self.update_output()

    def update_output(self):
        if 'Hepatic Artery' in self._sensor.name:
            t, value = self._sensor.get_file_strategy('StreamRMS').retrieve_buffer(0, 1)
        else:
            t, value = self._sensor.get_file_strategy('StreamRaw').retrieve_buffer(0, 1)
        dev = abs(self.desired - value)
        if dev > self.tolerance:
            if value < self.desired:
                new_val = self._pump._volts_offset + self.increment
                if new_val > 5:
                    new_val = 5
            else:
                new_val = self._pump._volts_offset - self.increment
                if new_val < 0:
                    new_val = 0
            if "Hepatic Artery" in self._sensor.name:
                peak = (new_val / self.divisor) / 2
                peak_high = None
                peak_low = None
                if (new_val + peak) > 5:  # Check and see if going over causes issues
                    peak_high = (5-new_val)
                    peak = peak_high
                elif (new_val - peak) < 0:
                    peak_low = new_val
                    peak = peak_low
                if peak_high and peak_low:
                    if peak_high > peak_low:
                        peak = peak_low
                    elif peak_low > peak_high:
                        peak = peak_high
                self._pump.set_sine(2 * peak, new_val, Hz=1)
            else:
                self._pump.set_dc(new_val)

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.FlexGridSizer(cols=3)

        section = LP_CFG.get_hwcfg_section('Heparin')
        com = section['commport']
        baud = section['baudrate']
        heparin_injection = PHDserial('Heparin')
        heparin_injection.open(com, baud)
        heparin_injection.ResetSyringe()
        heparin_injection.open_stream(LP_CFG.LP_PATH['stream'])
        heparin_injection.start_stream()

        section = LP_CFG.get_hwcfg_section('TPN & Bile Salts')
        com = section['commport']
        baud = section['baudrate']
        tpn_bile_salts_injection = PHDserial('TPN & Bile Salts')
        tpn_bile_salts_injection.open(com, baud)
        tpn_bile_salts_injection.ResetSyringe()
        tpn_bile_salts_injection.open_stream(LP_CFG.LP_PATH['stream'])
        tpn_bile_salts_injection.start_stream()

        self.syringes = [heparin_injection, tpn_bile_salts_injection]
        self.syringe_panels = [PanelSyringe(self, None, heparin_injection.name, heparin_injection), PanelSyringe(self, None, tpn_bile_salts_injection.name, tpn_bile_salts_injection)]

        self.acq =  NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)

        self.sensors = [SensorStream('Hepatic Artery Pressure', 'mmHg', self.acq), SensorStream('Portal Vein Pressure', 'mmHg', self.acq), SensorStream('Inferior Vena Cava Pressure', 'mmHg', self.acq), SensorStream('Hepatic Artery Flow', 'ml/min', self.acq), SensorStream('Portal Vein Flow', 'ml/min', self.acq), SensorStream('Inferior Vena Cava Flow', 'ml/min', self.acq)]

        self.hepatic_artery_pressure_control = None
        self.portal_vein_flow_control = None
        self.pumps = []

        for sensor in self.sensors:
            raw = StreamToFile('StreamRaw', None, self.acq.buf_len)
            raw.open(LP_CFG.LP_PATH['stream'], f'{sensor.name}_raw', sensor.params)
            sensor.add_strategy(raw)
            if 'Hepatic Artery' in sensor.name:
                rms = RMSStrategy('RMS', 50, self.acq.buf_len)
                save_rms = StreamToFile('StreamRMS', None, self.acq.buf_len)
                save_rms.open(LP_CFG.LP_PATH['stream'], f'{sensor.name}_rms', sensor.params)
                sensor.add_strategy(rms)
                sensor.add_strategy(save_rms)
            panel = PanelAI(self, sensor, name=sensor.name, strategy='StreamRaw')
            section = LP_CFG.get_hwcfg_section(sensor.name)
            dev = section['Device']
            line = section['LineName']
            calpt1_target = float(section['CalPt1_Target'])
            calpt1_reading = float(section['CalPt1_Reading'])
            calpt2_target = float(section['CalPt2_Target'])
            calpt2_reading = float(section['CalPt2_Reading'])
            panel._panel_cfg.choice_dev.SetStringSelection(dev)
            panel._panel_cfg.choice_line.SetSelection(float(line))
            panel._panel_cfg.choice_dev.Enable(False)
            panel._panel_cfg.choice_line.Enable(False)
            panel._panel_cfg.panel_cal.spin_cal_pt1.SetValue(calpt1_target)
            panel._panel_cfg.panel_cal.label_cal_pt1.SetValue(calpt1_reading)
            panel._panel_cfg.panel_cal.spin_cal_pt2.SetValue(calpt2_target)
            panel._panel_cfg.panel_cal.label_cal_pt2.SetValue(calpt2_reading)
            sizer.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)
            if sensor.name == 'Hepatic Artery Flow':
                section = LP_CFG.get_hwcfg_section('Epoprostenol')
                com = section['commport']
                baud = section['baudrate']
                epoprostenol_injection = PHDserial('Epoprostenol')
                epoprostenol_injection.open(com, baud)
                epoprostenol_injection.ResetSyringe()
                epoprostenol_injection.open_stream(LP_CFG.LP_PATH['stream'])
                epoprostenol_injection.start_stream()
                self.syringes.append(epoprostenol_injection)
                self.syringe_panels.append(PanelSyringe(self, sensor, epoprostenol_injection.name, epoprostenol_injection))

                section = LP_CFG.get_hwcfg_section('Phenylephrine')
                com = section['commport']
                baud = section['baudrate']
                phenylephrine_injection = PHDserial('Phenylephrine')
                phenylephrine_injection.open(com, baud)
                phenylephrine_injection.ResetSyringe()
                phenylephrine_injection.open_stream(LP_CFG.LP_PATH['stream'])
                phenylephrine_injection.start_stream()
                self.syringes.append(phenylephrine_injection)
                self.syringe_panels.append(PanelSyringe(self, sensor, phenylephrine_injection.name, phenylephrine_injection))
            if sensor.name == 'Hepatic Artery Pressure':
                self.ao_ha = NIDAQ_AO()
                self.pumps.append(self.ao_ha)
                self.hepatic_artery_pressure_control = PanelPressureFlowControl(self, sensor, self.ao_ha, name=sensor.name, pumpname='Hepatic Artery Centrifugal Pump')
            elif sensor.name == 'Portal Vein Flow':
                self.ao_pv = NIDAQ_AO()
                self.pumps.append(self.ao_pv)
                self.portal_vein_flow_control = PanelPressureFlowControl(self, sensor, self.ao_pv, name=sensor.name, pumpname='Portal Vein Centrifugal Pump')

        if self.hepatic_artery_pressure_control:
            sizer.Add(self.hepatic_artery_pressure_control, 1, wx.ALL | wx.EXPAND, border=1)

        if self.portal_vein_flow_control:
            sizer.Add(self.portal_vein_flow_control, 1, wx.ALL | wx.EXPAND, border=1)

        for panel in self.syringe_panels:
            sizer.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for panel in self.syringe_panels:
            if panel._injection.name in ['Epoprostenol', 'Phenylephrine']:
                panel._panel_feedback._syringe_timer.stop_feedback_injections()
        for syringe in self.syringes:
            infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
            syringe.stop(-1, infuse_rate, ml_volume, ml_min_rate)
            syringe.close_stream()
        for sensor in self.sensors:
            sensor.stop()
            sensor.close()
            if sensor.hw._task:  # DOes this close all other functionality on this DAQ? Check; also check on gb100
                sensor.hw.stop()
                sensor.hw.close()
        for pump in self.pumps:
            pump.set_dc(0)
            pump.close()
            pump.halt()
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
