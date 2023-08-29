# -*- coding: utf-8 -*-
""" Application to display dual Levitronix centrifugal pump controls

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.PerfusionSystem import PerfusionSystem
import pyHardware.pyWaveformGen as pyWaveformGen
from gui.panel_config import ConfigGUI


class LeviPumpPanel(wx.Panel):
    def __init__(self, parent, sensors):
        super().__init__(parent)
        self._lgr = logging.getLogger(__name__)

        self.panels = {}
        log_names = []
        for sensor in sensors:
            panel = BaseLeviPumpPanel(self, sensor)
            self.panels[sensor.name] = panel
            self._lgr.debug(f'logging to {sensor.name}')
            log_names.append(sensor.name)

        self.text_log_levi = utils.create_log_display(self, logging.INFO, log_names, use_last_name=True)
        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)
        for panel in self.panels.values():
            self.panel_sizer.Add(panel, wx.SizerFlags().Expand())

        self.sizer.Add(self.panel_sizer, wx.SizerFlags().Expand().Proportion(1))
        self.sizer.Add(self.text_log_levi, wx.SizerFlags().Expand().Proportion(1))

        # self.sizer.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.Layout()

    def __set_bindings(self):
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        for panel in self.panels.values():
            panel.pump_config.panel_config.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_pane_changed)

    def on_pane_changed(self, evt):
        # for panel in self.panels.values():
        #     panel.Layout()
        self.sizer.Layout()
        self.Layout()

    def OnClose(self, evt):
        for panel in self.panels.values():
            panel.Close()


class PumpConfig(wx.Panel):
    def __init__(self, parent, hw):
        super().__init__(parent)
        self._lgr = utils.get_object_logger(__name__, "OutputTypePanel")
        self.hw = hw

        self.sizer = None

        self.panel_config = ConfigGUI(self, hw.waveform, pane_label="Properties")
        self.panel_config.add_var('min_rpm', 'RPM (min)', limits=(0, 100, 10_000))
        self.panel_config.add_var('max_rpm', 'RPM (max)', limits=(0, 100, 10_000))
        self.panel_config.add_var('freq', 'Hz', limits=(0, 0.1, 100), decimal_places=1)

        self.panel_config.do_layout()
        self.chk_sine = wx.CheckBox(self.panel_config.GetPane(), label='Sine Output')
        self.panel_config.sizer.Prepend(self.chk_sine)
        self.panel_config.Layout()
        self.panel_config.set_bindings()

        self.__do_layout()
        self.__set_bindings()

        self.on_check_sine(evt=None)

    def __do_layout(self):
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.sizer.Add(self.panel_config, wx.SizerFlags().Proportion(0).Expand())
        # self.sizer.Add(self.chk_sine, wx.SizerFlags().Proportion(2).Expand())

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.chk_sine.Bind(wx.EVT_CHECKBOX, self.on_check_sine)

    def on_check_sine(self, evt):
        self.panel_config.spins['max_rpm'].Enable(self.chk_sine.IsChecked())
        self.panel_config.spins['freq'].Enable(self.chk_sine.IsChecked())

        if self.chk_sine.IsChecked():
            self.panel_config.labels['min_rpm'].SetLabel('RPM (min):')
        else:
            self.panel_config.labels['min_rpm'].SetLabel('RPM:')

    def update_from_waveform(self, waveform):
        if type(waveform) == pyWaveformGen.ConstantGen:
            self.chk_sine.SetValue(False)
            self.panel_config.spins['min_rpm'].SetValue(waveform.min_rpm)
            self.panel_config.spins['max_rpm'].SetValue(0)
            self.panel_config.spins['freq'].SetValue(0)
        elif type(waveform) == pyWaveformGen.SineGen:
            self.chk_sine.SetValue(True)
            self.panel_config.spins['min_rpm'].SetValue(waveform.min_rpm)
            self.panel_config.spins['max_rpm'].SetValue(waveform.max_rpm)
            self.panel_config.spins['freq'].SetValue(waveform.freq)
        self.on_check_sine()

    def manual_control(self, manual=True):
        self.panel_config.spins['min_rpm'].Enable(manual)
        self.panel_config.spins['max_rpm'].Enable(manual)
        self.panel_config.spins['freq'].Enable(manual)
        self.chk_sine.Enable(manual)

    def get_waveform(self):
        sine_checked = self.chk_sine.IsChecked()
        if sine_checked:
            cfg = pyWaveformGen.SineConfig(min_rpm=self.panel_config.spins['min_rpm'].GetValue(),
                                           max_rpm=self.panel_config.spins['max_rpm'].GetValue(),
                                           freq=self.panel_config.spins['freq'].GetValue())
            waveform = pyWaveformGen.SineGen()
            waveform.cfg = cfg
        else:
            cfg = pyWaveformGen.ConstantConfig(min_rpm=self.panel_config.spins['min_rpm'].GetValue())
            waveform =  pyWaveformGen.ConstantGen()
            waveform.cfg = cfg

        return waveform


class BaseLeviPumpPanel(wx.Panel):
    def __init__(self, parent, sensor):
        super().__init__(parent)
        self.name = sensor.name
        self._lgr = utils.get_object_logger(__name__, self.name)

        self.autolevipump = sensor

        font = wx.Font()
        font.SetPointSize(int(12))

        self.static_box = wx.StaticBox(self, wx.ID_ANY, label=self.name)
        self.static_box.SetFont(utils.get_header_font())
        self.sizer = wx.StaticBoxSizer(self.static_box, wx.HORIZONTAL)

        self.pump_config = PumpConfig(self, sensor.hw)
        # Buttons for functionality
        self.btn_update = wx.Button(self, label='Update')
        self.btn_start = wx.ToggleButton(self, label='Start')
        self.chk_auto = wx.CheckBox(self, label='Maintain\nFlow')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        sizer_btn = wx.BoxSizer(wx.VERTICAL)
        sizer_btn.Add(self.btn_update, wx.SizerFlags().Proportion(1).Expand())
        sizer_btn.Add(self.btn_start, wx.SizerFlags().Proportion(1).Expand())
        sizer_btn.Add(self.chk_auto, wx.SizerFlags().Proportion(1).Expand())

        self.sizer.Add(sizer_btn, wx.SizerFlags().Proportion(1))
        self.sizer.Add(self.pump_config, wx.SizerFlags().Proportion(4).Expand())

        self.SetSizer(self.sizer)
        self.sizer.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_update.Bind(wx.EVT_BUTTON, self.OnUpdate)
        self.btn_start.Bind(wx.EVT_TOGGLEBUTTON, self.OnStart)
        self.chk_auto.Bind(wx.EVT_CHECKBOX, self.OnAuto)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnAuto(self, evt):
        in_auto_mode = self.chk_auto.IsChecked()
        if in_auto_mode:
            self.autolevipump.start()
        else:
            self.autolevipump.stop()
        self.pump_config.manual_control(not in_auto_mode)
        self.btn_update.Enable(not in_auto_mode)
        self.btn_update.Enable(not in_auto_mode)

    def OnClose(self, evt):
        self.autolevipump.hw.stop()

    def OnStart(self, evt):
        in_start_mode = self.btn_start.GetValue()
        in_auto_mode = self.chk_auto.IsChecked()
        if in_start_mode:
            self.btn_start.SetLabel('Stop')
            if in_auto_mode:
                self.autolevipump.hw.start()
            else:
                self.autolevipump.start()
        else:
            self.btn_start.SetLabel('Start')
            if in_auto_mode:
                self.autolevipump.hw.stop()
            else:
                self.autolevipump.stop()

    def OnUpdate(self, evt):
        waveform = self.pump_config.get_waveform()
        self.autolevipump.hw.cfg.waveform = waveform
        self._lgr.info(f'Updating {self.autolevipump.hw.name} to {waveform.cfg}')


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        # TODO: Change to automations eventually
        sensor_names = ['Arterial PuraLev', 'Venous PuraLev']
        sensors = []
        for name in sensor_names:
            sensors.append(SYS_PERFUSION.get_sensor(name))

        self.panel = LeviPumpPanel(self, sensors)
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
    utils.setup_default_logging('panel_levitronix_pumps', logging.DEBUG)

    SYS_PERFUSION = PerfusionSystem()
    try:
        SYS_PERFUSION.open()
        SYS_PERFUSION.load_all()
        SYS_PERFUSION.load_automations()
    except Exception as e:
        # if anything goes wrong loading the perfusion system close the hardware and exit the program
        SYS_PERFUSION.close()
        raise e

    app = MyTestApp(0)
    app.MainLoop()
    SYS_PERFUSION.close()
