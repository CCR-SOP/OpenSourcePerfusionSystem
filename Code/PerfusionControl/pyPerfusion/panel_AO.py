# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for testing and configuring AIO
"""
import logging
import pyPerfusion.utils as utils

import wx

from pyHardware.pyAO_NIDAQ import NIDAQAODevice
import pyHardware.pyAO as pyAO
import pyPerfusion.PerfusionConfig as PerfusionConfig


DEV_LIST = ['Dev1', 'Dev2', 'Dev3', 'Dev4', 'Dev5']
LINE_LIST = [f'{line}' for line in range(0, 9)]


class PanelAO(wx.Panel):
    def __init__(self, parent, ao_ch):
        wx.Panel.__init__(self, parent, -1)
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self.ao_ch = ao_ch

        self._panel_settings = PanelAOSettings(self, self.ao_ch)
        name = f'{self.ao_ch.device.cfg.name} - {self.ao_ch.cfg.name}'
        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.__do_layout()
        self.__set_bindings()

    def close(self):
        self.ao_ch.close()

    def __do_layout(self):

        self.sizer.Add(self._panel_settings)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass


class PanelAOSettings(wx.Panel):
    def __init__(self, parent, ao_ch):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self.ao_ch = ao_ch

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.btn_update = wx.Button(self, label='Update')

        self.check_sine = wx.CheckBox(self, label='Sine output')
        self.spin_pk2pk = wx.SpinCtrlDouble(self, min=0.0, max=5.0, initial=0, inc=0.1)
        self.lbl_pk2pk = wx.StaticText(self, label='Pk-Pk Voltage')
        self.spin_offset = wx.SpinCtrlDouble(self, min=0.0, max=5.0, initial=0, inc=0.1)
        self.lbl_offset = wx.StaticText(self, label='Offset Voltage')
        self.spin_hz = wx.SpinCtrlDouble(self, min=0.0, max=1000.0, initial=1.0)
        self.lbl_hz = wx.StaticText(self, label='Hz')
        self.spin_hz.Digits = 3
        self.spin_offset.Digits = 3
        self.spin_pk2pk.Digits = 3

        self.btn_save_cfg = wx.Button(self, label='Save Settings')
        self.btn_load_cfg = wx.Button(self, label='Load Settings')

        self.OnSine(wx.EVT_CHECKBOX)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        self.sizer.Add(self.check_sine)

        self.sizer_sine = wx.GridSizer(cols=3, hgap=5, vgap=2)
        flags = wx.SizerFlags(0).Expand()
        self.sizer_sine.Add(self.lbl_pk2pk, flags)
        self.sizer_sine.Add(self.lbl_offset, flags)
        self.sizer_sine.Add(self.lbl_hz, flags)
        self.sizer_sine.Add(self.spin_pk2pk, flags)
        self.sizer_sine.Add(self.spin_offset, flags)
        self.sizer_sine.Add(self.spin_hz, flags)

        self.sizer.Add(self.sizer_sine, flags)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.SizerFlags(0)
        sizer.Add(self.btn_update, flags)
        sizer.Add(self.btn_save_cfg, flags)
        sizer.AddSpacer(5)
        sizer.Add(self.btn_load_cfg, flags)
        self.sizer.Add(sizer)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_update.Bind(wx.EVT_BUTTON, self.on_update)
        self.check_sine.Bind(wx.EVT_CHECKBOX, self.OnSine)
        self.btn_save_cfg.Bind(wx.EVT_BUTTON, self.on_save_cfg)
        self.btn_load_cfg.Bind(wx.EVT_BUTTON, self.on_load_cfg)

    def on_update(self, evt):
        volts = self.spin_pk2pk.GetValue()
        hz = self.spin_hz.GetValue()
        offset = self.spin_offset.GetValue()
        want_sine = self.check_sine.IsChecked()

        if want_sine:
            try:

                self.ao_ch.set_sine(pk2pk_volts=volts, offset_volts=offset, hz=hz)
                self.ao_ch.update_buffer()
            except pyAO.AODeviceException as e:
                dlg = wx.MessageDialog(parent=self, message=str(e), caption='AO Device Error', style=wx.OK)
                dlg.ShowModal()
                self.check_sine.SetValue(0)
        else:
            self.ao_ch.set_dc(offset_volts=offset)
        self.ao_ch.device.stop()
        self.ao_ch.device.start()

    def OnSine(self, evt):
        want_sine = self.check_sine.IsChecked()
        self.spin_hz.Enable(want_sine)
        self.spin_pk2pk.Enable(want_sine)

    def on_save_cfg(self, evt):
        self.update_config_from_controls()
        self.ao_ch.write_config()

    def on_load_cfg(self, evt):
        self.ao_ch.device.read_config(ch_name=self.ao_ch.cfg.name)
        self.update_controls_from_config()

    def update_config_from_controls(self):
        want_sine = self.check_sine.IsChecked()
        if want_sine:
            new_cfg = pyAO.AOSineChannelConfig(name=self.ao_ch.cfg.name,
                                               line=self.ao_ch.cfg.line,
                                               max_accel_volts_per_s=self.ao_ch.cfg.max_accel_volts_per_s)

            new_cfg.pk2pk_volts = self.spin_pk2pk.GetValue()
            new_cfg.hz = self.spin_hz.GetValue()
            self.ao_ch.cfg = new_cfg
        else:
            new_cfg = pyAO.AOChannelConfig(name=self.ao_ch.cfg.name,
                                           line=self.ao_ch.cfg.line,
                                           max_accel_volts_per_s=self.ao_ch.cfg.max_accel_volts_per_s)
            self.ao_ch.cfg = new_cfg
        self.ao_ch.cfg.offset_volts = self.spin_offset.GetValue()

    def update_controls_from_config(self):
        if type(self.ao_ch.cfg) == pyAO.AOSineChannelConfig:
            self.check_sine.SetValue(True)
            self.spin_pk2pk.SetValue(self.ao_ch.cfg.pk2pk_volts)
            self.spin_hz.SetValue(self.ao_ch.cfg.hz)
        else:
            self.check_sine.SetValue(False)
        self.spin_offset.SetValue(self.ao_ch.cfg.offset_volts)
        self.OnSine(wx.CommandEvent())

    def update_config_from_controls(self):
        want_sine = self.check_sine.IsChecked()
        if want_sine:
            new_cfg = pyAO.AOSineChannelConfig(name=self.ao_ch.cfg.name,
                                               line=self.ao_ch.cfg.line,
                                               max_accel_volts_per_s=self.ao_ch.cfg.max_accel_volts_per_s)

            new_cfg.pk2pk_volts = self.spin_pk2pk.GetValue()
            new_cfg.hz = self.spin_hz.GetValue()
            self.ao_ch.cfg = new_cfg
        else:
            new_cfg = pyAO.AOChannelConfig(name=self.ao_ch.cfg.name,
                                           line=self.ao_ch.cfg.line,
                                           max_accel_volts_per_s=self.ao_ch.cfg.max_accel_volts_per_s)
            self.ao_ch.cfg = new_cfg
        self.ao_ch.cfg.offset_volts = self.spin_offset.GetValue()

    def update_controls_from_config(self):
        if type(self.ao_ch.cfg) == pyAO.AOSineChannelConfig:
            self.check_sine.SetValue(True)
            self.spin_pk2pk.SetValue(self.ao_ch.cfg.pk2pk_volts)
            self.spin_hz.SetValue(self.ao_ch.cfg.hz)
        else:
            self.check_sine.SetValue(False)
        self.spin_offset.SetValue(self.ao_ch.cfg.offset_volts)
        self.OnSine(wx.CommandEvent())

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelAO(self, ao_channel)


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
    PerfusionConfig.set_test_config()

    dev = NIDAQAODevice()
    dev.cfg = pyAO.AODeviceConfig(name='TestAnalogOutputDevice')
    dev.read_config()
    channel_names = list(dev.ao_channels)
    ao_channel = dev.ao_channels[channel_names[0]]

    app = MyTestApp(0)
    app.MainLoop()
