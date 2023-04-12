# -*- coding: utf-8 -*-
""" Application to display all sensors

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

from pyPerfusion.panel_AI import PanelAI
import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import pyPerfusion.Sensor as Sensor
from apps.app_hardware_control import SYS_HW


class SensorFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self._lgr = logging.getLogger(__name__)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=2)
        utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
        utils.configure_matplotlib_logging()

        sensor_names = ['Hepatic Artery Flow', 'Portal Vein Flow', 'Hepatic Artery Pressure', 'Portal Vein Pressure']
        self.sensors = {}
        self.panels = []
        for name in sensor_names:
            sensor = Sensor.Sensor(name)
            self.sensors[name] = sensor
            self.sensors[name].read_config()
            if name == "Hepatic Artery Flow":
                panel = PanelAI(self, sensor, reader=sensor.get_reader('MovAvg_11pt'))
            else:
                panel = PanelAI(self, sensor, reader=sensor.get_reader())
            self.panels.append(panel)
            sizer.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)

        # try:
            # self.cdi_sensor = Sensor.Sensor(name='CDI')
            # self.cdi_sensor.start()
        # except PerfusionConfig.MissingConfigSection:
            # wx.MessageBox(f'Could not find CDI config: {self.cdi.name}. CDI functionality will not be enabled')
            # self.cdi_sensor = None

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        SYS_HW.stop()
        for sensor in self.sensors.values():
            sensor.stop()
        for panel in self.panels:
            panel.Destroy()
        # if self.cdi_sensor:
            # self.cdi_sensor.stop()
        self.Destroy()


class MySensorApp(wx.App):
    def OnInit(self):
        frame = SensorFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()

    SYS_HW.load_all()
    SYS_HW.start()

    app = MySensorApp(0)
    app.MainLoop()
