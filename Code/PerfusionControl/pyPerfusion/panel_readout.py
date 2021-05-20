# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for showing single number readout
"""
from pathlib import Path
import logging

import wx

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.SensorStream import SensorStream
from pyHardware.pyAI import AI


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
        val = int(self._sensor.get_current())
        self.label_value.SetLabel(f'{val:3}')

    # def __set_bindings(self):
        # add bindings, if needed


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.sensor = SensorStream('HA Flow', 'bpm', AI(100))
        self.panel = PanelReadout(self, self.sensor)
        self.sensor.start()
        self.sensor.open(Path('./__data__'), Path('2020-09-14'))


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    LP_CFG.set_base(basepath='~/Documents/LPTEST')
    LP_CFG.update_stream_folder()
    utils.setup_default_logging(filename='panel_readout')
    app = MyTestApp(0)
    app.MainLoop()
