# -*- coding: utf-8 -*-
"""Panel class for testing and configuring Pump 11 Elite syringe pump


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import pyHardware.pyPump11Elite as pyPump11Elite
from pyPerfusion.PerfusionSystem import PerfusionSystem


BAUD_RATES = ['9600', '38400', '57600', '115200']


class PanelSyringe(wx.Panel):
    def __init__(self, parent, automation):
        super().__init__(parent)
        self._lgr = logging.getLogger(__name__)
        self.automation = automation

        self._panel_cfg = PanelSyringeConfig(self, self.automation.device.hw)
        self._panel_ctrl = PanelSyringeControls(self, self.automation)
        self.static_box = wx.StaticBox(self, wx.ID_ANY, label=self.automation.device.name)
        self.static_box.SetFont(utils.get_header_font())
        self.sizer = wx.StaticBoxSizer(self.static_box, wx.VERTICAL)
        self.static_box.SetFont(utils.get_header_font())

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()

        self.sizer.Add(self._panel_cfg, flags.Proportion(2))
        self.sizer.Add(self._panel_ctrl, flags.Proportion(2))
        self.sizer.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.Layout()

    def __set_bindings(self):
        pass


class PanelSyringeConfig(wx.Panel):
    def __init__(self, parent, syringe: pyPump11Elite.Pump11Elite):
        super().__init__(parent)
        self._lgr = logging.getLogger(__name__)
        self.syringe = syringe

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.label_port = wx.StaticText(self, label='COM Port')
        avail_ports = utils.get_avail_com_ports()
        self.combo_port = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY, choices=avail_ports)

        self.label_baud = wx.StaticText(self, label='Baud')
        self.choice_baud = wx.Choice(self, wx.ID_ANY, choices=BAUD_RATES)
        self.choice_baud.SetSelection(0)

        self.btn_open = wx.ToggleButton(self, label='Open')

        self.label_manufacturer = wx.StaticText(self, label='Manufacturer')
        self.combo_manufacturer = wx.ComboBox(self, wx.ID_ANY, choices=pyPump11Elite.get_available_manufacturer_names())
        self.label_sizes = wx.StaticText(self, label='Syringe Sizes')
        self.combo_sizes = wx.ComboBox(self, wx.ID_ANY, choices=[])

        # self.btn_save_cfg = wx.Button(self, label='Save')
        # self.btn_load_cfg = wx.Button(self, label='Load')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center()

        self.sizer_cfg = wx.GridSizer(cols=2)
        self.sizer_cfg.Add(self.label_port, flags)
        self.sizer_cfg.Add(self.combo_port, flags)

        self.sizer_cfg.Add(self.label_baud, flags)
        self.sizer_cfg.Add(self.choice_baud, flags)

        self.sizer_cfg.Add(self.btn_open, flags)
        self.sizer_cfg.AddSpacer(2)

        self.sizer_cfg.Add(self.label_manufacturer, flags)
        self.sizer_cfg.Add(self.label_sizes, flags)
        self.sizer_cfg.Add(self.combo_manufacturer, flags)
        self.sizer_cfg.Add(self.combo_sizes, flags)

        # self.sizer_cfg.Add(self.btn_load_cfg, flags)
        # self.sizer_cfg.Add(self.btn_save_cfg, flags)
        self.sizer.Add(self.sizer_cfg)

        self.sizer.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.Layout()

    def __set_bindings(self):
        self.btn_open.Bind(wx.EVT_TOGGLEBUTTON, self.OnOpen)
        self.combo_port.Bind(wx.EVT_COMBOBOX_DROPDOWN, self.OnPortDropDown)
        self.combo_manufacturer.Bind(wx.EVT_COMBOBOX, self.OnManufacturer)
        # self.btn_save_cfg.Bind(wx.EVT_BUTTON, self.on_save_cfg)
        # self.btn_load_cfg.Bind(wx.EVT_BUTTON, self.on_load_cfg)

    def OnPortDropDown(self, evt):
        ports = utils.get_avail_com_ports()
        self.combo_port.Set(ports)

    def OnManufacturer(self, evt):
        if self.syringe.is_open():
            self.syringe.clear_syringe()
            target = self.combo_manufacturer.GetStringSelection()
            code = pyPump11Elite.get_code_from_name(target)
            if code:
                sizes = self.syringe.get_available_syringes(code)
                self.combo_sizes.Set(sizes)

    def OnOpen(self, evt):
        port = self.combo_port.GetStringSelection()
        baud = int(self.choice_baud.GetStringSelection())

        if not self.syringe.is_open():
            self.syringe.cfg.com_port = port
            self.syringe.cfg.baud = baud
            self.syringe.open()

            self.btn_open.SetLabel('Close')
        else:
            self._lgr.info(f'Closing syringe at {port}, {baud}')
            self.syringe.close()
            self.btn_open.SetLabel('Open')

    def update_config_from_controls(self):
        self.syringe.cfg.com_port = self.combo_port.GetStringSelection()
        self.syringe.cfg.baud = int(self.choice_baud.GetStringSelection())
        manu_name = self.combo_manufacturer.GetStringSelection()
        self.syringe.cfg.manufacturer_code = pyPump11Elite.get_code_from_name(manu_name)
        self.syringe.cfg.size = self.combo_sizes.GetStringSelection()

    def update_controls_from_config(self):
        self.combo_port.SetStringSelection(self.syringe.cfg.com_port)
        self.choice_baud.SetStringSelection(str(self.syringe.cfg.baud))
        manu_name = pyPump11Elite.get_name_from_code(self.syringe.cfg.manufacturer_code)
        self.combo_manufacturer.SetStringSelection(manu_name)
        self.OnManufacturer(None)
        self.combo_sizes.SetStringSelection(self.syringe.cfg.size)

    def on_save_cfg(self, evt):
        self.update_config_from_controls()
        self.syringe.write_config()

    def on_load_cfg(self, evt):
        self.syringe.read_config()  # this apparently also opens the comport
        self.update_controls_from_config()


class PanelSyringeControls(wx.Panel):
    def __init__(self, parent, automation):
        super().__init__(parent)
        self._lgr = logging.getLogger(__name__)
        self.automation = automation

        self._inc = 1
        self._vol_inc = 100

        font = wx.Font()
        font.SetPointSize(int(12))
        font_smaller = wx.Font()
        font_smaller.SetPointSize((int(10)))

        if self.automation and self.automation.device:
            name = self.automation.device.name
        else:
            raise Exception(f'Missing automation {self.automation.name} {self.automation.device}')

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        static_box.SetFont(utils.get_header_font())
        self.sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

        self.spin_rate = wx.SpinCtrlDouble(self, min=0, max=100000, inc=self._inc, initial=int(self.automation.cfg.ul_per_min))
        self.spin_rate.SetFont(font)
        self.label_rate = wx.StaticText(self, label='Infusion Rate\nul/min', style=wx.ALIGN_CENTER)
        self.label_rate.SetFont(font_smaller)
        self.btn_basal = wx.ToggleButton(self, label='Start Basal')
        self.btn_basal.SetFont(font_smaller)

        self.spin_volume = wx.SpinCtrlDouble(self, min=0, max=100000, inc=self._vol_inc, initial=int(self.automation.cfg.volume_ul))
        self.spin_volume.SetFont(font)
        self.label_volume = wx.StaticText(self, label='Bolus Volume\nul', style=wx.ALIGN_CENTER)
        self.label_volume.SetFont(font_smaller)
        self.btn_bolus = wx.Button(self, label='Bolus')
        self.btn_bolus.SetFont(font_smaller)

        self.timer_gui_update = wx.Timer(self)
        self.timer_gui_update.Start(milliseconds=500, oneShot=wx.TIMER_CONTINUOUS)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        sizer_rate = wx.BoxSizer(wx.VERTICAL)
        sizer_rate.Add(self.label_rate)
        sizer_rate.Add(self.spin_rate)

        sizer_vol = wx.BoxSizer(wx.VERTICAL)
        sizer_vol.Add(self.label_volume)
        sizer_vol.Add(self.spin_volume)

        sizer_buttons = wx.BoxSizer(wx.VERTICAL)
        sizer_buttons.Add(self.btn_basal, wx.SizerFlags().Proportion(1).Expand())
        sizer_buttons.Add(self.btn_bolus, wx.SizerFlags().Proportion(1).Expand())

        self.sizer.Add(sizer_rate, wx.SizerFlags().CenterVertical())
        self.sizer.Add(sizer_vol, wx.SizerFlags().CenterVertical())
        self.sizer.Add(sizer_buttons, wx.SizerFlags().Expand())

        self.sizer.SetSizeHints(self.GetParent())
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()
        self.btn_basal.SetBackgroundColour(wx.Colour(153, 204, 255))
        self.btn_bolus.SetBackgroundColour(wx.Colour(153, 204, 255))

    def __set_bindings(self):
        self.btn_basal.Bind(wx.EVT_TOGGLEBUTTON, self.OnBasal)
        self.btn_bolus.Bind(wx.EVT_BUTTON, self.OnBolus)
        self.Bind(wx.EVT_TIMER, self.update_controls_from_hardware, self.timer_gui_update)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnBasal(self, evt):
        infusion_rate = self.spin_rate.GetValue()
        sensor = self.automation.device
        if sensor.hw.is_infusing:
            sensor.hw.set_target_volume(0)
            self.spin_volume.SetValue(0)
            self.btn_basal.SetLabel('Start Basal')
            self.btn_basal.SetBackgroundColour(wx.Colour(153, 204, 255))
            self.btn_bolus.SetBackgroundColour(wx.Colour(153, 204, 255))
            self.btn_basal.SetValue(True)
            sensor.hw.stop()
            self._lgr.info(f'Basal syringe infusion halted')
            self.spin_volume.Enable()
        else:
            sensor.hw.set_infusion_rate(infusion_rate)
            sensor.hw.set_target_volume(0)
            self.spin_volume.SetValue(0)
            sensor.hw.start_constant_infusion()
            self.btn_basal.SetLabel('Stop Basal')
            self.btn_basal.SetBackgroundColour(wx.Colour(102, 153, 255))
            self.btn_basal.SetValue(False)
            self._lgr.info(f'Basal syringe infusion at rate {infusion_rate} uL/min started')
            self.spin_volume.Disable()

    def OnBolus(self, evt):
        sensor = self.automation.device
        infusion_rate = self.spin_rate.GetValue()
        target_vol = self.spin_volume.GetValue()
        sensor.hw.set_infusion_rate(infusion_rate)
        sensor.hw.set_target_volume(target_vol)
        sensor.hw.infuse_to_target_volume()
        self.btn_basal.SetLabel('Stop Bolus')
        self.btn_bolus.SetBackgroundColour(wx.Colour(102, 153, 255))
        self._lgr.info(f'Bolus syringe infusion at rate {infusion_rate} uL/min to target volume {target_vol} started')

    def update_controls_from_hardware(self, evt=None):
        enable = not self.automation.device.hw.is_infusing
        self.btn_bolus.Enable(enable)

    def update_config_from_controls(self):
        self.automation.cfg.ul_per_min = int(self.spin_rate.GetValue())
        self.automation.cfg.volume_ul = int(self.spin_volume.GetValue())

    def update_controls_from_config(self):
        self.spin_volume.SetValue(self.automation.cfg.volume_ul)
        self.spin_rate.SetValue(self.automation.cfg.ul_per_min)

    def on_save_cfg(self, evt):
        self.update_config_from_controls()
        self.automation.device.hw.write_config()

    def on_load_cfg(self, evt):
        self.automation.device.hw.read_config()
        self.update_controls_from_config()

    def OnClose(self, evt):
        self.timer_gui_update.Stop()
        self.automation.device.hw.stop()


class PanelSyringeControlsSimple(wx.CollapsiblePane):
    def __init__(self, parent, sensor):
        super().__init__(parent, label=sensor.name)
        self._lgr = logging.getLogger(__name__)
        self.sensor = sensor

        self._inc = 1
        self._vol_inc = 100

        font = wx.Font()
        font.SetPointSize(int(12))
        font_smaller = wx.Font()
        font_smaller.SetPointSize((int(10)))

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.Expand()

        self.spin_rate = wx.SpinCtrlDouble(self.GetPane(), min=0, max=100000, inc=self._inc, initial=0)
        self.spin_rate.SetFont(font)
        self.label_rate = wx.StaticText(self.GetPane(), label='Infusion Rate\nul/min', style=wx.ALIGN_CENTER)
        self.label_rate.SetFont(font_smaller)
        self.btn_basal = wx.ToggleButton(self.GetPane(), label='Start Basal')
        self.btn_basal.SetFont(font_smaller)

        self.spin_volume = wx.SpinCtrlDouble(self.GetPane(), min=0, max=100000, inc=self._vol_inc, initial=0)
        self.spin_volume.SetFont(font)
        self.label_volume = wx.StaticText(self.GetPane(), label='Bolus Volume\nul', style=wx.ALIGN_CENTER)
        self.label_volume.SetFont(font_smaller)
        self.btn_bolus = wx.Button(self.GetPane(), label='Bolus')
        self.btn_bolus.SetFont(font_smaller)

        self.timer_gui_update = wx.Timer(self.GetPane())
        self.timer_gui_update.Start(milliseconds=500, oneShot=wx.TIMER_CONTINUOUS)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        sizer_rate = wx.BoxSizer(wx.VERTICAL)
        sizer_rate.Add(self.label_rate)
        sizer_rate.Add(self.spin_rate)

        sizer_vol = wx.BoxSizer(wx.VERTICAL)
        sizer_vol.Add(self.label_volume)
        sizer_vol.Add(self.spin_volume)

        sizer_buttons = wx.BoxSizer(wx.VERTICAL)
        sizer_buttons.Add(self.btn_basal, wx.SizerFlags().Proportion(1).Expand())
        sizer_buttons.Add(self.btn_bolus, wx.SizerFlags().Proportion(1).Expand())

        self.sizer.Add(sizer_rate, wx.SizerFlags().CenterVertical())
        self.sizer.Add(sizer_vol, wx.SizerFlags().CenterVertical())
        self.sizer.Add(sizer_buttons, wx.SizerFlags().Expand())

        self.sizer.SetSizeHints(self.GetParent())
        self.GetPane().SetSizer(self.sizer)
        self.Layout()
        self.Fit()
        self.btn_basal.SetBackgroundColour(wx.Colour(153, 204, 255))
        self.btn_bolus.SetBackgroundColour(wx.Colour(153, 204, 255))

    def __set_bindings(self):
        self.btn_basal.Bind(wx.EVT_TOGGLEBUTTON, self.OnBasal)
        self.btn_bolus.Bind(wx.EVT_BUTTON, self.OnBolus)
        self.Bind(wx.EVT_TIMER, self.update_controls_from_hardware, self.timer_gui_update)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnBasal(self, evt):
        infusion_rate = self.spin_rate.GetValue()
        if self.sensor.hw.is_infusing:
            self.sensor.hw.set_target_volume(0)
            self.btn_basal.SetLabel('Start Basal')
            self.btn_basal.SetBackgroundColour(wx.Colour(153, 204, 255))
            self.btn_bolus.SetBackgroundColour(wx.Colour(153, 204, 255))
            self.btn_basal.SetValue(True)
            self.sensor.hw.stop()
            self._lgr.info(f'Basal syringe infusion halted')
            self.spin_volume.Enable()
            self.btn_bolus.Enable()
        else:
            self.sensor.hw.set_infusion_rate(infusion_rate)
            self.sensor.hw.set_target_volume(0)
            self.sensor.hw.start_constant_infusion()
            self.btn_basal.SetLabel('Stop Basal')
            self.btn_basal.SetBackgroundColour(wx.Colour(102, 153, 255))
            self.btn_basal.SetValue(False)
            self._lgr.info(f'Basal syringe infusion at rate {infusion_rate} uL/min started')
            self.spin_volume.Disable()
            self.btn_bolus.Disable()

    def OnBolus(self, evt):
        infusion_rate = self.spin_rate.GetValue()
        target_vol = self.spin_volume.GetValue()
        self.sensor.hw.set_infusion_rate(infusion_rate)
        self.sensor.hw.set_target_volume(target_vol)
        self.sensor.hw.infuse_to_target_volume()
        self.btn_basal.SetLabel('Stop Bolus')
        self.btn_bolus.SetBackgroundColour(wx.Colour(102, 153, 255))
        self._lgr.info(f'Bolus syringe infusion at rate {infusion_rate} uL/min to target volume {target_vol} started')

    def update_controls_from_hardware(self, evt=None):
        enable = not self.sensor.hw.is_infusing
        self.btn_bolus.Enable(enable)

    def OnClose(self, evt):
        self.timer_gui_update.Stop()


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        automation = SYS_PERFUSION.get_automation('Phenylephrine Automation')
        self.panel = PanelSyringe(self, automation)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel.Close()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None)
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('panel_syringe', logging.DEBUG)

    SYS_PERFUSION = PerfusionSystem()
    try:
        SYS_PERFUSION.open()
        SYS_PERFUSION.load_all()
        SYS_PERFUSION.load_automations()
    except Exception as e:
        # if anything goes wrong loading the perfusion system
        # close the hardware and exit the program
        SYS_PERFUSION.close()
        raise e

    app = MyTestApp(0)
    app.MainLoop()
    SYS_PERFUSION.close()
