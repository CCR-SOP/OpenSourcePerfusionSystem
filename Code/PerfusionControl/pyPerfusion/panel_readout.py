# -*- coding: utf-8 -*-
"""Panel class for showing a single value


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from pathlib import Path
import logging

import wx

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.SensorStream import SensorStream
from pyHardware.pyAI import AI
from pyPerfusion.FileStrategy import StreamToFile


class PanelReadout(wx.Panel):
    def __init__(self, parent, sensor: SensorStream):
        self._logger = logging.getLogger(__name__)
        super().__init__(parent, -1)
        self._sensor = sensor
        self._parent = parent

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer_value = wx.BoxSizer(wx.HORIZONTAL)
        self.label_name = wx.StaticText(self, label=sensor.name)
        self.label_value = wx.StaticText(self, label='000')
        self.label_units = wx.StaticText(self, label=sensor.unit_str)

        self.__do_layout()
        # self.__set_bindings()

    def __do_layout(self):

        font = self.label_name.GetFont()
        font.SetPointSize(10)
        self.label_name.SetFont(font)
        font = self.label_value.GetFont()
        font.SetPointSize(15)
        self.label_value.SetFont(font)

        self.sizer.Add(self.label_name, wx.SizerFlags().CenterHorizontal())
        self.sizer_value.Add(self.label_value, wx.SizerFlags().CenterVertical())
        self.sizer_value.AddSpacer(10)
        self.sizer_value.Add(self.label_units, wx.SizerFlags().CenterVertical())
        self.sizer.Add(self.sizer_value, wx.SizerFlags().CenterHorizontal())

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

        self.timer_update = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer_update.Start(3000, wx.TIMER_CONTINUOUS)

    def OnTimer(self, event):
        if event.GetId() == self.timer_update.GetId():
            self.update_value()

    def update_value(self):
        t, val = self._sensor.get_file_strategy('Raw').retrieve_buffer(0, 1)
        if val is not []:
            val = val[0]
            self.label_value.SetLabel(f'{val:0.3}')

    def __set_bindings(self):
        pass


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.acq = AI(100)
        self.acq.open()
        self.acq.add_channel('0')
        self.acq.set_demo_properties('0', demo_amp=10, demo_offset=5)
        self.sensor = SensorStream('HA Flow', 'bpm', self.acq)
        self.sensor.set_ch_id('0')
        self.panel = PanelReadout(self, self.sensor)
        self.raw = StreamToFile('Raw', None, self.acq.buf_len)
        self.raw.open(LP_CFG.LP_PATH['stream'], f'{self.sensor.name}_raw', self.sensor.params)
        self.sensor.add_strategy(self.raw)
        self.sensor.open()
        self.sensor.start()
        self.acq.start()



class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    LP_CFG.set_base(basepath='~/Documents/LPTEST')
    LP_CFG.update_stream_folder()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    app = MyTestApp(0)
    app.MainLoop()
