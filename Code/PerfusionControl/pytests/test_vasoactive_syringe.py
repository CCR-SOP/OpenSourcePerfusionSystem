# -*- coding: utf-8 -*-
"""
@author: Allen Luna
Test app for initiating syringe injections based on pressure/flow conditions
"""
import wx

from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.panel_AI import PanelAI
from pyPerfusion.syringe_timer import SyringeTimer
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG

class PanelTestVasoactiveSyringe(wx.Panel):
    def __init__(self, parent, sensor, name, injection):
        self.parent = parent
        self._sensor = sensor
        self._name = name
        self._injection = injection
        self._inc = 1.0

        wx.Panel.__init__(self, parent, -1)

        syringe_list = '%s' % injection.name

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.btn_basal_infusion = wx.ToggleButton(self, label='Basal Infusion Active')

        self.label_manu = wx.StaticText(self, label='Manufacturer')
        self.choice_manu = wx.Choice(self, choices=[])

        self.label_types = wx.StaticText(self, label='Syringe Type')
        self.choice_types = wx.Choice(self, choices=[])

        self.label_rate = wx.StaticText(self, label='Basal Infusion Rate')
        self.spin_rate = wx.SpinCtrl(self, min=1, max=100000)
        self.spin_rate.SetValue(1)
        self.choice_rate = wx.Choice(self, choices=['ul/min', 'ml/min'])
        self.choice_rate.SetSelection(1)

        self.label_flow = wx.StaticText(self, label='Inject When Flow is')
        self.btn_direction = wx.ToggleButton(self, label='Greater Than')
        self.spin_flow = wx.SpinCtrlDouble(self, min=0, max=1000, initial=0.0, inc=self._inc)

        self.label_tolerance = wx.StaticText(self, label='Tolerance (mL/min): ')
        self.spin_tolerance = wx.SpinCtrl(self, min=0, max=20, initial=0)

        self.btn_start_basal = wx.ToggleButton(self, label='Start Basal Infusion')
        self.btn_start_timer = wx.ToggleButton(self, label='Start Bolus Injections')

        self.label_1TB = wx.StaticText(self, label='Bolus Volume')
        self.spin_1TB_volume = wx.SpinCtrl(self, min=1, max=100000)
        self.spin_1TB_volume.SetValue(1)
        self.choice_1TB_unit = wx.Choice(self, choices=['ul', 'ml'])
        self.choice_1TB_unit.SetSelection(1)
        self.btn_start_1TB = wx.ToggleButton(self, label='Start Bolus')

        self.label_syringes = wx.StaticText(self, label='Syringe In Use: %s' % syringe_list)

        self.load_info()

        self.__do_layout()
        self.__set_bindings()

    def load_info(self):
        codes, volumes = LP_CFG.open_syringe_info()
        self._injection.syringe.manufacturers = codes
        self._injection.syringe.syringes = volumes
        self.update_syringe_choices()

    def update_syringe_choices(self):
        self.choice_manu.Clear()
        manu = self._injection.syringe.manufacturers
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
        sizer.AddSpacer(20)
        sizer.Add(self.spin_rate, flags)
        sizer.AddSpacer(20)
        sizer.Add(self.choice_rate, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_syringes, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_flow, flags)
        sizer.AddSpacer(20)
        sizer.Add(self.btn_direction, flags)
        sizer.AddSpacer(20)
        sizer.Add(self.spin_flow, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_tolerance, flags)
        sizer.Add(self.spin_tolerance, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_start_basal, flags)
        sizer.AddSpacer(20)
        sizer.Add(self.btn_start_timer)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_1TB, flags)
        sizer.AddSpacer(10)
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
        self.choice_manu.Bind(wx.EVT_CHOICE, self.OnManu)
        self.btn_direction.Bind(wx.EVT_TOGGLEBUTTON, self.OnDirection)
        self.btn_start_basal.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartBasal)
        self.btn_start_timer.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartBolus)
        self.btn_start_1TB.Bind(wx.EVT_TOGGLEBUTTON, self.OnOneTimeBolus)

    def OnBasalInfusion(self, evt):
        state = self.btn_basal_infusion.GetLabel()
        if state == 'Basal Infusion Active':
            self.btn_basal_infusion.SetLabel('Basal Infusion Inactive')
        elif state == 'Basal Infusion Inactive':
            self.btn_basal_infusion.SetLabel('Basal Infusion Active')

    def OnManu(self, evt):
        self.update_syringe_types()

    def get_selected_code(self):
        sel = self.choice_manu.GetString(self.choice_manu.GetSelection())
        code = sel[1:4]
        return code

    def update_syringe_types(self):
        code = self.get_selected_code()
        self.choice_types.Clear()
        syringes = self._injection.syringe.syringes
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
                self._injection.syringe.ResetSyringe()
                code = self.get_selected_code()
                syr_size = self.choice_types.GetString(self.choice_types.GetSelection())
                self._injection.syringe.set_syringe_manufacturer_size(code, syr_size)
                rate = self.spin_rate.GetValue()
                unit = self.choice_rate.GetString(self.choice_rate.GetSelection())
                self._injection.syringe.set_infusion_rate(rate, unit)
                self.choice_manu.Enable(False)
                self.choice_types.Enable(False)
                self.spin_rate.Enable(False)
                self.choice_rate.Enable(False)
                self.btn_basal_infusion.Enable(False)
                self.btn_start_timer.Enable(False)
                self.btn_direction.Enable(False)
                self.btn_start_1TB.Enable(False)
                self.choice_1TB_unit.Enable(False)
                infuse_rate, ml_min_rate, ml_volume = self._injection.syringe.get_stream_info()
                self._injection.syringe.infuse(2222, infuse_rate, ml_volume, ml_min_rate)
                self.btn_start_basal.SetLabel('Stop Basal Infusion')
            elif self.btn_basal_infusion.GetLabel() == 'Basal Infusion Inactive':
                pass
        else:
            infuse_rate, ml_min_rate, ml_volume = self._injection.syringe.get_stream_info()
            self._injection.syringe.stop(1111, infuse_rate, ml_volume, ml_min_rate)
            self.choice_manu.Enable(True)
            self.choice_types.Enable(True)
            self.spin_rate.Enable(True)
            self.choice_rate.Enable(True)
            self.btn_basal_infusion.Enable(True)
            self.btn_start_timer.Enable(True)
            self.btn_direction.Enable(True)
            self.btn_start_1TB.Enable(True)
            self.choice_1TB_unit.Enable(True)
            self.btn_start_basal.SetLabel('Start Basal Infusion')

    def OnStartBolus(self, evt):
        state = self.btn_start_timer.GetLabel()
        if state == 'Start':
            self.btn_start_timer.SetLabel('Stop')
            self._injection.syringe.ResetSyringe()
            code = self.get_selected_code()
            syr_size = self.choice_types.GetString(self.choice_types.GetSelection())
            self._injection.syringe.set_syringe_manufacturer_size(code, syr_size)
            rate = self.spin_rate.GetValue()
            unit = self.choice_rate.GetString(self.choice_rate.GetSelection())
            self._injection.syringe.set_infusion_rate(rate, unit)
            self.choice_manu.Enable(False)
            self.choice_types.Enable(False)
            self.spin_rate.Enable(False)
            self.choice_rate.Enable(False)
            self.btn_basal_infusion.Enable(False)
            if self.btn_basal_infusion.GetLabel() == 'Basal Infusion Active':
                infuse_rate, ml_min_rate, ml_volume = self._injection.syringe.get_stream_info()
                self._injection.syringe.infuse(2222, infuse_rate, ml_volume, ml_min_rate)
                self._injection.basal = True
            else:
                self._injection.basal = False
            self._injection.threshold_value = self.spin_flow.GetValue()
            self._injection.tolerance = self.spin_tolerance.GetValue()
            self._injection.start_injection_timer()
        else:
            self._injection.stop_injection_timer()
            self.choice_manu.Enable(True)
            self.choice_types.Enable(True)
            self.spin_rate.Enable(True)
            self.choice_rate.Enable(True)
            self.btn_basal_infusion.Enable(True)
            if self._injection.wait is True:  # If injections were terminated in the middle of a bolus injection, the injection will not stop; thus, stop syringe, and clear target volume
                infuse_rate, ml_min_rate, ml_volume = self._injection.syringe.get_stream_info()
                self._injection.syringe.stop(8888, infuse_rate, ml_volume, ml_min_rate)
                self._injection.syringe.reset_target_volume()
            if self.btn_basal_infusion.GetLabel() == 'Basal Infusion Active':
                infuse_rate, ml_min_rate, ml_volume = self._injection.syringe.get_stream_info()
                self._injection.syringe.stop(1111, infuse_rate, ml_volume, ml_min_rate)
            self.btn_start_timer.SetLabel('Start')

    def OnOneTimeBolus(self, evt):
        self._injection.syringe.ResetSyringe()
        code = self.get_selected_code()
        syr_size = self.choice_types.GetString(self.choice_types.GetSelection())
        self._injection.syringe.set_syringe_manufacturer_size(code, syr_size)
        self._injection.syringe.set_infusion_rate(25, 'ml/min')
        volume = self.spin_1TB_volume.GetValue()
        unit = self.choice_1TB_unit.GetString(self.choice_1TB_unit.GetSelection())
        self._injection.syringe.set_target_volume(volume, unit)
        if 'ul' in unit:
            unit = False
        self._injection.syringe.infuse(volume, 25, unit, True)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=3)
        self.acq = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
        self.sensor = SensorStream('Flow Sensor', 'mL/min', self.acq)
        sizer.Add(PanelAI(self, self.sensor, self.sensor.name), 1, wx.ALL | wx.EXPAND, border=1)
        vasoconstrictor_injection = SyringeTimer('Phenylephrine', 'COM4', 9600, 0, 0, self.sensor)
        vasodilator_injection = SyringeTimer('Epoprostenol', 'COM11', 9600, 0, 0, self.sensor)
        self._syringes = [vasoconstrictor_injection, vasodilator_injection]
        sizer.Add(PanelTestVasoactiveSyringe(self, self.sensor, 'Vasoconstrictor Syringe Testing', vasoconstrictor_injection), 1, wx.ALL | wx.EXPAND, border=1)
        sizer.Add(PanelTestVasoactiveSyringe(self, self.sensor, 'Vasodilator Syringe Testing', vasodilator_injection), 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for syringe in self._syringes:
            syringe.syringe.stop_stream()
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
    app = MyTestApp(0)
    app.MainLoop()
