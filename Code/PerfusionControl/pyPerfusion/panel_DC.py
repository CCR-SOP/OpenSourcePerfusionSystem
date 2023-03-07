# -*- coding: utf-8 -*-
""" Panel class for controlling analog output

@project: LiverPerfusion NIH
@author: Stephie Lux NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.utils as utils
from pyHardware.pyDC_NIDAQ import NIDAQDCDevice
import pyHardware.pyDC as pyDC
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.FileStrategy import StreamToFile


DEV_LIST = ['Dev1', 'Dev2', 'Dev3', 'Dev4', 'Dev5']
LINE_LIST = [f'{line}' for line in range(0, 9)]


class PanelDC(wx.Panel):
    def __init__(self, parent, sensor):
        wx.Panel.__init__(self, parent, -1)
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self.sensor = sensor

        self._panel_dc = PanelDCControl(self, self.sensor)

        font = wx.Font()
        font.SetPointSize(int(20))
        static_box = wx.StaticBox(self, wx.ID_ANY, label=self.sensor.name)
        static_box.SetFont(font)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.__do_layout()
        self.__set_bindings()

    def close(self):
        self.sensor.hw.stop()
        self.sensor.stop()

    def __do_layout(self):

        self.sizer.Add(self._panel_dc, wx.SizerFlags(1).Expand())

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass


class PanelDCControl(wx.Panel):
    def __init__(self, parent, sensor):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self.sensor = sensor

        font = wx.Font()
        font.SetPointSize(int(20))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.label_offset = wx.StaticText(self, label='Pump Speed (mL/min)')
        self.entered_offset = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=50, inc=.5)
        self.label_offset.SetFont(font)
        self.entered_offset.SetFont(font)

        self.btn_change_rate = wx.Button(self, label='Update Rate')
        self.btn_change_rate.SetFont(font)

        self.btn_stop = wx.Button(self, label='Stop')
        self.btn_stop.SetFont(font)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_offset, wx.SizerFlags().CenterHorizontal())
        sizer.Add(self.entered_offset, wx.SizerFlags(1).Expand())
        self.sizer.Add(sizer, wx.SizerFlags(0).Expand())

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_change_rate)
        sizer.Add(self.btn_stop)
        self.sizer.Add(sizer, wx.SizerFlags(0).CenterHorizontal().Top())

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_change_rate.Bind(wx.EVT_BUTTON, self.on_update)
        self.btn_stop.Bind(wx.EVT_BUTTON, self.on_stop)

    def on_stop(self, evt):
        self.sensor.hw.set_output(int(0))

    def on_update(self, evt):
        self._lgr.debug('on_update called')
        new_flow = self.entered_offset.GetValue() / 10
        self.sensor.hw.set_output(new_flow)

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelDC(self, temp_sensor)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.Destroy()
        temp_hw.stop()
        temp_sensor.stop()

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

    temp_name = 'Dialysate Inflow Pump'
    temp_hw = NIDAQDCDevice()
    temp_hw.cfg = pyDC.DCChannelConfig(name=temp_name)
    temp_hw.read_config()

    temp_sensor = SensorStream(temp_hw, 'ml/min')
    temp_sensor.add_strategy(strategy=StreamToFile('Raw', 1, 10))

    app = MyTestApp(0)
    app.MainLoop()
