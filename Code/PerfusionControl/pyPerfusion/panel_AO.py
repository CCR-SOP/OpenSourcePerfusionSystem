# -*- coding: utf-8 -*-
""" Panel class for controlling analog output

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.utils as utils
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

        self._panel_dc = PanelAODCControl(self, self.ao_ch)
        name = f'{self.ao_ch.cfg.name}'
        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.__do_layout()
        self.__set_bindings()

    def close(self):
        self.ao_ch.close()

    def __do_layout(self):

        self.sizer.Add(self._panel_dc, wx.SizerFlags(1).Expand())

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass


class PanelAODCControl(wx.Panel):
    def __init__(self, parent, ao_ch):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self.ao_ch = ao_ch

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.label_offset = wx.StaticText(self, label='Speed (mL/min)')
        self.entered_offset = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=50, initial=0, inc=.001)

        self.btn_save_cfg = wx.Button(self, label='Save Default')
        self.btn_load_cfg = wx.Button(self, label='Load Default')
        self.btn_change_rate = wx.Button(self, label='Update Rate')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_offset, wx.SizerFlags().CenterHorizontal())
        sizer.Add(self.entered_offset, wx.SizerFlags(1).Expand())
        self.sizer.Add(sizer, wx.SizerFlags(0).Expand())

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_change_rate)
        sizer.AddSpacer(5)
        sizer.Add(self.btn_save_cfg)
        sizer.AddSpacer(5)
        sizer.Add(self.btn_load_cfg)
        self.sizer.Add(sizer, wx.SizerFlags(0).CenterHorizontal().Top())

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_change_rate.Bind(wx.EVT_BUTTON, self.on_update)
        self.btn_save_cfg.Bind(wx.EVT_BUTTON, self.on_save_cfg)
        self.btn_load_cfg.Bind(wx.EVT_BUTTON, self.on_load_cfg)

    def on_update(self, evt):
        output_type = pyAO.DCOutput()
        output_type.offset_volts = self.entered_offset.GetValue() / 10
        # self._lgr.debug(f'offset is {output_type.offset_volts}')
        self.ao_ch.cfg.output_type = output_type
        self.ao_ch.set_output(self.ao_ch.cfg.output_type)

    def on_save_cfg(self, evt):
        self.update_config_from_controls()
        self.ao_ch.write_config()

    def on_load_cfg(self, evt):
        self.ao_ch.device.read_config()  # ch_name=self.ao_ch.cfg.name
        self.update_controls_from_config()

    def update_config_from_controls(self):
        output_type = pyAO.DCOutput()
        output_type.offset_volts = self.spin_offset.GetValue()
        self.ao_ch.cfg.output_type = output_type

    def update_controls_from_config(self):
        self.entered_offset.SetValue(self.ao_ch.cfg.offset_volts)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelAO(self, ao_channel)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        # TODO: stop the pump??
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

    dev = NIDAQAODevice()
    dev.cfg = pyAO.AODeviceConfig(name='Dev1Output')
    dev.read_config()
    channel_names = list(dev.ao_channels)
    ao_channel = dev.ao_channels[channel_names[1]]
    app = MyTestApp(0)
    app.MainLoop()
