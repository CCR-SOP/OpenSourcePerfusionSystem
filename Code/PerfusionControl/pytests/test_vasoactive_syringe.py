# -*- coding: utf-8 -*-
"""
@author: Allen Luna
Test app for initiating syringe injections based on pressure/flow conditions
"""
import wx
import pyPerfusion.utils as utils
import logging

from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.panel_AI import PanelAI
from pyPerfusion.syringe_timer import SyringeTimer
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.FileStrategy import StreamToFile
from pyHardware.PHDserial import PHDserial

class PanelTestVasoactiveSyringe(wx.Panel):
    def __init__(self, parent, sensor, name, injection):
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self._sensor = sensor
        self._name = name
        self._injection = injection
        self._syringe_timer = SyringeTimer(self._injection.name, self._sensor, self._injection)
        self._inc = 0.1

        wx.Panel.__init__(self, parent, -1)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.btn_basal_infusion = wx.ToggleButton(self, label='Basal Infusion Active')

        self.label_manu = wx.StaticText(self, label='Manufacturer')
        self.choice_manu = wx.Choice(self, choices=[])

        self.label_types = wx.StaticText(self, label='Syringe Type')
        self.choice_types = wx.Choice(self, choices=[])

        self.label_rate = wx.StaticText(self, label='Basal Infusion Rate')
        self.spin_rate = wx.SpinCtrlDouble(self, min=0, max=100000, inc=self._inc)
        self.spin_rate.SetValue(1)
        self.choice_rate = wx.Choice(self, choices=['ul/min', 'ml/min'])
        self.choice_rate.SetSelection(1)

        self.label_flow = wx.StaticText(self, label='Inject When')
        self.btn_direction = wx.ToggleButton(self, label='Greater Than')
        self.spin_flow = wx.SpinCtrlDouble(self, min=0, max=1000, initial=0, inc=self._inc)
        self.btn_update_threshold = wx.Button(self, label='Update Threshold')

        self.label_tolerance = wx.StaticText(self, label='Tolerance (mL/min): ')
        self.spin_tolerance = wx.SpinCtrlDouble(self, min=0, max=100, initial=0, inc=self._inc)
        self.btn_update_tolerance = wx.Button(self, label='Update Tolerance')

        self.label_injection_volume = wx.StaticText(self, label='Bolus Injection Volume (uL): ')
        self.spin_injection_volume = wx.SpinCtrlDouble(self, min=0, max=10000, initial=0, inc=1)
        self.btn_update_injection_volume = wx.Button(self, label='Update Volume')

        self.label_time_between_checks = wx.StaticText(self, label='Time Between Checks (s): ')
        self.spin_time_between_checks = wx.SpinCtrlDouble(self, min=0, max=10000, initial=0, inc=1)

        self.label_cooldown_time = wx.StaticText(self, label='Cooldown Time (s): ')
        self.spin_cooldown_time = wx.SpinCtrlDouble(self, min=0, max=10000, initial=0, inc=1)

        self.btn_start_basal = wx.ToggleButton(self, label='Start Basal Infusion')
        self.btn_start_timer = wx.ToggleButton(self, label='Start Bolus Injections')

        self.spin_1TB_volume = wx.SpinCtrlDouble(self, min=0, max=100000, inc=self._inc)
        self.spin_1TB_volume.SetValue(1)
        self.choice_1TB_unit = wx.Choice(self, choices=['ul', 'ml'])
        self.choice_1TB_unit.SetSelection(1)
        self.btn_start_1TB = wx.ToggleButton(self, label='Start Bolus')

        syringe_list = '%s' % injection.name
        self.label_syringes = wx.StaticText(self, label='Syringe In Use: %s' % syringe_list)

        self.load_info()
        self.set_syringe()

        self.__do_layout()
        self.__set_bindings()

    def load_info(self):
        codes, volumes = LP_CFG.open_syringe_info()
        self._injection.manufacturers = codes
        self._injection.syringes = volumes
        self.update_syringe_choices()

    def update_syringe_choices(self):
        self.choice_manu.Clear()
        manu = self._injection.manufacturers
        manu_str = [f'({code}) {desc}' for code, desc in manu.items()]
        self.choice_manu.Append(manu_str)

    def __do_layout(self):
        flags = wx.SizerFlags().Expand()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_basal_infusion, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_manu, flags)
        sizer.AddSpacer(20)
        sizer.Add(self.choice_manu, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_types, flags)
        sizer.AddSpacer(20)
        sizer.Add(self.choice_types, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_rate, flags)
        sizer.AddSpacer(10)
        sizer.Add(self.spin_rate, flags)
        sizer.AddSpacer(10)
        sizer.Add(self.choice_rate, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_syringes, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_flow, flags)
        sizer.Add(self.btn_direction, flags)
        sizer.Add(self.spin_flow, flags)
        sizer.Add(self.btn_update_threshold, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_tolerance, flags)
        sizer.Add(self.spin_tolerance, flags)
        sizer.Add(self.btn_update_tolerance, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_injection_volume, flags)
        sizer.Add(self.spin_injection_volume, flags)
        sizer.Add(self.btn_update_injection_volume, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_time_between_checks, flags)
        sizer.Add(self.spin_time_between_checks, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_cooldown_time, flags)
        sizer.Add(self.spin_cooldown_time, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_start_basal, flags)
        sizer.AddSpacer(20)
        sizer.Add(self.btn_start_timer)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.spin_1TB_volume, flags)
        sizer.AddSpacer(10)
        sizer.Add(self.choice_1TB_unit, flags)
        sizer.AddSpacer(10)
        sizer.Add(self.btn_start_1TB, flags)
        self.sizer.Add(sizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_basal_infusion.Bind(wx.EVT_TOGGLEBUTTON, self.OnBasalInfusion)
        # self.choice_manu.Bind(wx.EVT_CHOICE, self.OnManu)
        self.btn_direction.Bind(wx.EVT_TOGGLEBUTTON, self.OnDirection)
        self.btn_start_basal.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartBasal)
        self.btn_start_timer.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartBolus)
        self.btn_start_1TB.Bind(wx.EVT_TOGGLEBUTTON, self.OnOneTimeBolus)
        self.btn_update_injection_volume.Bind(wx.EVT_BUTTON, self.OnUpdateInjectionVolume)
        self.btn_update_threshold.Bind(wx.EVT_BUTTON, self.OnUpdateThreshold)
        self.btn_update_tolerance.Bind(wx.EVT_BUTTON, self.OnUpdateTolerance)

    def set_syringe(self):
        section = LP_CFG.get_hwcfg_section(self._injection.name)
        manucode = section['manucode']
        volume = section['volume']
        self.choice_manu.SetSelection(manucode)
        self.update_syringe_types()
        self.choice_types.SetSelection(volume)
        self.choice_manu.Enable(False)
        self.choice_types.Enable(False)

    def OnBasalInfusion(self, evt):
        state = self.btn_basal_infusion.GetLabel()
        if state == 'Basal Infusion Active':
            self.btn_basal_infusion.SetLabel('Basal Infusion Inactive')
        elif state == 'Basal Infusion Inactive':
            self.btn_basal_infusion.SetLabel('Basal Infusion Active')

 #   def OnManu(self, evt):
 #       self.update_syringe_types()

    def get_selected_code(self):
        sel = self.choice_manu.GetString(self.choice_manu.GetSelection())
        code = sel[1:4]
        return code

    def update_syringe_types(self):
        code = self.get_selected_code()
        self.choice_types.Clear()
        syringes = self._injection.syringes
        types = syringes[code]
        self.choice_types.Append(types)

    def OnDirection(self, evt):
        state = self.btn_direction.GetLabel()
        if state == 'Greater Than':
            self.btn_direction.SetLabel('Less Than')
        elif state == 'Less Than':
            self.btn_direction.SetLabel('Greater Than')

    def OnStartBasal(self, evt):
        state = self.btn_start_basal.GetLabel()
        if state == 'Start Basal Infusion':
            if self.btn_basal_infusion.GetLabel() == 'Basal Infusion Active':
                self._injection.ResetSyringe()
                code = self.get_selected_code()
                syr_size = self.choice_types.GetString(self.choice_types.GetSelection())
                self._injection.set_syringe_manufacturer_size(code, syr_size)
                rate = self.spin_rate.GetValue()
                unit = self.choice_rate.GetString(self.choice_rate.GetSelection())
                self._injection.set_infusion_rate(rate, unit)
                self.choice_manu.Enable(False)
                self.choice_types.Enable(False)
                self.spin_rate.Enable(False)
                self.choice_rate.Enable(False)
                self.btn_basal_infusion.Enable(False)
                self.btn_start_timer.Enable(False)
                self.btn_direction.Enable(False)
                self.btn_start_1TB.Enable(False)
                self.choice_1TB_unit.Enable(False)
                self.btn_update_injection_volume.Enable(False)
                self.btn_update_threshold.Enable(False)
                self.btn_update_tolerance.Enable(False)
                infuse_rate, ml_min_rate, ml_volume = self._injection.get_stream_info()
                self._injection.infuse(-2, infuse_rate, ml_volume, ml_min_rate)
                self.btn_start_basal.SetLabel('Stop Basal Infusion')
            elif self.btn_basal_infusion.GetLabel() == 'Basal Infusion Inactive':
                pass
        else:
            infuse_rate, ml_min_rate, ml_volume = self._injection.get_stream_info()
            self._injection.stop(-1, infuse_rate, ml_volume, ml_min_rate)
            self.choice_manu.Enable(True)
            self.choice_types.Enable(True)
            self.spin_rate.Enable(True)
            self.choice_rate.Enable(True)
            self.btn_basal_infusion.Enable(True)
            self.btn_start_timer.Enable(True)
            self.btn_direction.Enable(True)
            self.btn_start_1TB.Enable(True)
            self.choice_1TB_unit.Enable(True)
            self.btn_update_injection_volume.Enable(True)
            self.btn_update_threshold.Enable(True)
            self.btn_update_tolerance.Enable(True)
            self.btn_start_basal.SetLabel('Start Basal Infusion')

    def OnStartBolus(self, evt):
        state = self.btn_start_timer.GetLabel()
        if state == 'Start Bolus Injections':
            self._injection.ResetSyringe()
            code = self.get_selected_code()
            syr_size = self.choice_types.GetString(self.choice_types.GetSelection())
            self._injection.set_syringe_manufacturer_size(code, syr_size)
            rate = self.spin_rate.GetValue()
            unit = self.choice_rate.GetString(self.choice_rate.GetSelection())
            self._injection.set_infusion_rate(rate, unit)
            self.choice_manu.Enable(False)
            self.choice_types.Enable(False)
            self.spin_rate.Enable(False)
            self.choice_rate.Enable(False)
            self.btn_basal_infusion.Enable(False)
            self.btn_start_basal.Enable(False)
            self.btn_direction.Enable(False)
            self.btn_start_1TB.Enable(False)
            self.choice_1TB_unit.Enable(False)
            if self.btn_basal_infusion.GetLabel() == 'Basal Infusion Active':
                infuse_rate, ml_min_rate, ml_volume = self._injection.get_stream_info()
                self._injection.infuse(-2, infuse_rate, ml_volume, ml_min_rate)
                self._syringe_timer.basal = True
            else:
                self._syringe_timer.basal = False
            self._syringe_timer.threshold_value = self.spin_flow.GetValue()
            self._syringe_timer.tolerance = self.spin_tolerance.GetValue()
            self._syringe_timer.injection_volume = self.spin_injection_volume.GetValue()
            self._syringe_timer.time_between_checks = self.spin_time_between_checks.GetValue()
            self._syringe_timer.cooldown_time = self.spin_cooldown_time.GetValue()
            self._syringe_timer.start_bolus_injections()
            self.btn_start_timer.SetLabel('Stop Bolus Injections')
        elif state == 'Stop Bolus Injections':
            self._syringe_timer.stop_bolus_injections()
            self.choice_manu.Enable(True)
            self.choice_types.Enable(True)
            self.spin_rate.Enable(True)
            self.choice_rate.Enable(True)
            self.btn_basal_infusion.Enable(True)
            self.btn_start_basal.Enable(True)
            self.btn_direction.Enable(True)
            self.btn_start_1TB.Enable(True)
            self.choice_1TB_unit.Enable(True)
            if self.btn_basal_infusion.GetLabel() == 'Basal Infusion Active':
                infuse_rate, ml_min_rate, ml_volume = self._injection.get_stream_info()
                self._injection.stop(-1, infuse_rate, ml_volume, ml_min_rate)
            self.btn_start_timer.SetLabel('Start Bolus Injections')

    def OnOneTimeBolus(self, evt):
        self._injection.ResetSyringe()
        code = self.get_selected_code()
        syr_size = self.choice_types.GetString(self.choice_types.GetSelection())
        self._injection.set_syringe_manufacturer_size(code, syr_size)
        self._injection.set_infusion_rate(25, 'ml/min')
        volume = self.spin_1TB_volume.GetValue()
        unit = self.choice_1TB_unit.GetString(self.choice_1TB_unit.GetSelection())
        self._injection.set_target_volume(volume, unit)
        if 'ul' in unit:
            unit = False
        self._injection.infuse(volume, 25, unit, True)

    def OnUpdateInjectionVolume(self, evt):
        self._syringe_timer.injection_volume = self.spin_injection_volume.GetValue()

    def OnUpdateThreshold(self, evt):
        self._syringe_timer.threshold_value = self.spin_flow.GetValue()

    def OnUpdateTolerance(self, evt):
        self._syringe_timer.tolerance = self.spin_tolerance.GetValue()

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=3)
        self.acq = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
        self.sensor = SensorStream('Flow Sensor', 'mL/min', self.acq)
        raw = StreamToFile('StreamRaw', None, self.acq.buf_len)
        raw.open(LP_CFG.LP_PATH['stream'], f'{self.sensor.name}_raw', self.sensor.params)
        self.sensor.add_strategy(raw)
        sizer.Add(PanelAI(self, self.sensor, self.sensor.name, 'StreamRaw'), 1, wx.ALL | wx.EXPAND, border=1)

        section = LP_CFG.get_hwcfg_section('Phenylephrine')
        com = section['commport']
        baud = section['baudrate']
        vasoconstrictor_injection = PHDserial('Phenylephrine')
        vasoconstrictor_injection.open(com, baud)
        vasoconstrictor_injection.ResetSyringe()
        vasoconstrictor_injection.open_stream(LP_CFG.LP_PATH['stream'])
        vasoconstrictor_injection.start_stream()

        section = LP_CFG.get_hwcfg_section('Epoprostenol')
        com = section['commport']
        baud = section['baudrate']
        vasodilator_injection = PHDserial('Epoprostenol')
        vasodilator_injection.open(com, baud)
        vasodilator_injection.ResetSyringe()
        vasodilator_injection.open_stream(LP_CFG.LP_PATH['stream'])
        vasodilator_injection.start_stream()

        self._syringes = [vasoconstrictor_injection, vasodilator_injection]
        sizer.Add(PanelTestVasoactiveSyringe(self, self.sensor, 'Vasoconstrictor Syringe Testing', vasoconstrictor_injection), 1, wx.ALL | wx.EXPAND, border=1)
        sizer.Add(PanelTestVasoactiveSyringe(self, self.sensor, 'Vasodilator Syringe Testing', vasodilator_injection), 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for syringe in self._syringes:
            syringe.stop_stream()
        self.sensor.stop()
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
    utils.setup_default_logging(filename='test_vasoactive_syringe')
    app = MyTestApp(0)
    app.MainLoop()
