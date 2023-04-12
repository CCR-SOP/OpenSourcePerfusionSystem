# -*- coding: utf-8 -*-
"""Panel class for testing and configuring Pump 11 Elite syringe pump


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from time import sleep
import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import pyPerfusion.pyPump11Elite as pyPump11Elite
from pyHardware.SystemHardware import SYS_HW
from pyPerfusion.Sensor import Sensor


BAUD_RATES = ['9600', '38400', '57600', '115200']


class PanelSyringe(wx.Panel):
    def __init__(self, parent, sensor):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self.sensor = sensor
        syringe = self.sensor.hw

        self._panel_cfg = PanelSyringeConfig(self, syringe)
        self._panel_ctrl = PanelSyringeControls(self, syringe, self.sensor)
        static_box = wx.StaticBox(self, wx.ID_ANY, label=syringe.name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()

        self.sizer.Add(self._panel_cfg, flags.Proportion(2))
        self.sizer.Add(self._panel_ctrl, flags.Proportion(2))
        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass


class PanelSyringeConfig(wx.Panel):
    def __init__(self, parent, syringe: pyPump11Elite.Pump11Elite):
        super().__init__(parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
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

        sizer_cfg = wx.GridSizer(cols=2)
        sizer_cfg.Add(self.label_port, flags)
        sizer_cfg.Add(self.combo_port, flags)

        sizer_cfg.Add(self.label_baud, flags)
        sizer_cfg.Add(self.choice_baud, flags)

        sizer_cfg.Add(self.btn_open, flags)
        sizer_cfg.AddSpacer(2)

        sizer_cfg.Add(self.label_manufacturer, flags)
        sizer_cfg.Add(self.label_sizes, flags)
        sizer_cfg.Add(self.combo_manufacturer, flags)
        sizer_cfg.Add(self.combo_sizes, flags)

        # sizer_cfg.Add(self.btn_load_cfg, flags)
        # sizer_cfg.Add(self.btn_save_cfg, flags)
        self.sizer.Add(sizer_cfg)

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_open.Bind(wx.EVT_TOGGLEBUTTON, self.OnOpen)
        self.combo_port.Bind(wx.EVT_COMBOBOX_DROPDOWN, self.OnPortDropDown)
        self.combo_manufacturer.Bind(wx.EVT_COMBOBOX, self.OnManufacturer)
        # self.btn_save_cfg.Bind(wx.EVT_BUTTON, self.on_save_cfg)
        # self.btn_load_cfg.Bind(wx.EVT_BUTTON, self.on_load_cfg)

    def OnPortDropDown(self, evt):
        ports = utils.get_avail_com_ports()
        self._lgr.info(f'Available com ports are {ports}')
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
            self.syringe.open(self.syringe.cfg)

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
    def __init__(self, parent, syringe: pyPump11Elite.Pump11Elite, sensor):
        super().__init__(parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self.syringe = syringe
        self.sensor = sensor
        self.reader = self.sensor.get_reader()
        self._inc = 1
        self._vol_inc = 100

        font = wx.Font()
        font.SetPointSize(int(12))

        static_box = wx.StaticBox(self, wx.ID_ANY, label=self.syringe.name)
        static_box.SetFont(font)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.spin_rate = wx.SpinCtrlDouble(self, min=0, max=100000, inc=self._inc)
        self.spin_rate.SetFont(font)
        self.label_rate = wx.StaticText(self, label='Infusion Rate (ul/min)')
        self.label_rate.SetFont(font)
        self.btn_basal = wx.ToggleButton(self, label='Start Basal')
        self.btn_basal.SetFont(font)

        self.spin_volume = wx.SpinCtrlDouble(self, min=0, max=100000, inc=self._vol_inc)
        self.spin_volume.SetFont(font)
        self.label_volume = wx.StaticText(self, label='Target Volume (ul)')
        self.label_volume.SetFont(font)
        self.btn_bolus = wx.Button(self, label='Bolus')
        self.btn_bolus.SetFont(font)

        # self.btn_save_cfg = wx.Button(self, label='Save')
        # self.btn_load_cfg = wx.Button(self, label='Load')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center()

        sizer_cfg = wx.GridSizer(cols=3)

        sizer_cfg.Add(self.label_rate, flags)
        sizer_cfg.Add(self.spin_rate, flags)
        sizer_cfg.Add(self.btn_basal, flags)

        sizer_cfg.Add(self.label_volume, flags)
        sizer_cfg.Add(self.spin_volume, flags)
        sizer_cfg.Add(self.btn_bolus, flags)

        # sizer_cfg.Add(self.btn_save_cfg, flags)
        # sizer_cfg.Add(self.btn_load_cfg, flags)


        self.sizer.Add(sizer_cfg)

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_basal.Bind(wx.EVT_TOGGLEBUTTON, self.OnBasal)
        self.btn_bolus.Bind(wx.EVT_BUTTON, self.OnBolus)
        # self.btn_save_cfg.Bind(wx.EVT_BUTTON, self.on_save_cfg)
        # self.btn_load_cfg.Bind(wx.EVT_BUTTON, self.on_load_cfg)


    def OnBasal(self, evt):
        infusion_rate = self.spin_rate.GetValue()
        if self.syringe.is_infusing:
            self.syringe.set_target_volume(0)
            self.btn_basal.SetLabel('Start Basal')
            self.btn_basal.SetValue(True)
            self.syringe.stop()
            self._lgr.info(f'Basal syringe infusion halted')
        else:
            self.syringe.set_infusion_rate(infusion_rate)
            self.syringe.set_target_volume(0)
            # self._lgr.debug(f'Infusion rate: {infusion_rate}')
            # self._lgr.debug(f'Target volume: {0}')
            self.syringe.start_constant_infusion()
            self.btn_basal.SetLabel('Stop Basal')
            self.btn_basal.SetValue(False)
            self._lgr.info(f'Basal syringe infusion at rate {infusion_rate} uL/min started')

    def OnBolus(self, evt):
        infusion_rate = self.spin_rate.GetValue()
        target_vol = self.spin_volume.GetValue()
        self.syringe.set_infusion_rate(infusion_rate)
        self.syringe.set_target_volume(target_vol)
        self.syringe.infuse_to_target_volume()

        sleep(1)
        ts, last_samples = self.reader.retrieve_buffer(5000, 5)
        for ts, samples in zip(ts, last_samples):
            self._lgr.info(f' At time {ts}, {self.sensor.name} infused a bolus at rate {samples[0]} uL/min with '
                           f'target volume of {samples[1]} uL')

    def update_config_from_controls(self):
        self.syringe.cfg.initial_injection_rate = int(self.spin_rate.GetValue())
        self.syringe.cfg.initial_target_volume = int(self.spin_volume.GetValue())

    def update_controls_from_config(self):
        self._lgr.debug(f'config is {self.syringe.cfg}')
        self.spin_volume.SetValue(self.syringe.cfg.initial_target_volume)
        self.spin_rate.SetValue(self.syringe.cfg.initial_injection_rate)

    def on_save_cfg(self, evt):
        self.update_config_from_controls()
        self.syringe.write_config()

    def on_load_cfg(self, evt):
        self.syringe.read_config()
        self.update_controls_from_config()


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = PanelSyringe(self, trial_sensor)
        self.trial_sensor = trial_sensor
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        SYS_HW.stop()
        self.trial_sensor.stop()
        self.Destroy()

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()

    SYS_HW.load_hardware_from_config()
    SYS_HW.load_mocks()

    name = 'Insulin'
    try:
        trial_sensor = Sensor(name=name)
        trial_sensor.read_config()
        trial_sensor.start()
    except PerfusionConfig.MissingConfigSection:
        print(f'Could not find sensor called {name} in sensors.ini')
        SYS_HW.stop()
        exit()
        trial_sensor = None

    app = MyTestApp(0)
    app.MainLoop()
