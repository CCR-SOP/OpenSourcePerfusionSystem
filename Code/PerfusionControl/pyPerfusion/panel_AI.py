# -*- coding: utf-8 -*-
"""Panel class for testing and configuring AIO


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.plotting import PanelPlotting, SensorPlot
import pyPerfusion.Sensor as Sensor
import pyPerfusion.utils as utils
from pyHardware.SystemHardware import SYS_HW
from pyPerfusion.Strategy_ReadWrite import Reader


class PanelAI(wx.Panel):
    def __init__(self, parent, sensor: Sensor.Sensor, reader: Reader):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self._sensor = sensor
        self._reader = reader

        self.collapse_pane = wx.CollapsiblePane(self, wx.ID_ANY, 'Calibration')
        self._panel_plot = PanelPlotting(self)
        self._panel_cal = PanelAICalibration(self, sensor, reader)

        if self._sensor.hw is not None:
            ch_name = f'{self._sensor.hw.device.name} Channel: {self._sensor.hw.name}'
        else:
            ch_name = "NA"
        static_box = wx.StaticBox(self, wx.ID_ANY, label=ch_name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)
        self.sizer_pane = wx.BoxSizer(wx.VERTICAL)

        self._sensorplot = SensorPlot(self._sensor, self._panel_plot.axes, readout=True)
        self._panel_plot.add_plot(self._sensorplot)
        self._sensorplot.set_reader(self._reader)
        self._sensor.start()

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        win = self.collapse_pane.GetPane()
        self._panel_cal.Reparent(win)
        self.sizer_pane.Add(self._panel_cal)
        win.SetSizer(self.sizer_pane)
        self.sizer_pane.SetSizeHints(win)

        self.sizer.Add(self.collapse_pane, 0, wx.GROW | wx.ALL, 5)
        self.sizer.Add(self._panel_plot, 10, wx.GROW | wx.ALL, 5)

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.collapse_pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_pane_changed)

    def on_pane_changed(self, evt):
        self.sizer.Layout()
        self.Layout()


class PanelAICalibration(wx.Panel):
    def __init__(self, parent, sensor: Sensor, reader: Reader):
        super().__init__(parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self._sensor = sensor
        self._reader = reader

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.label_cal_pt1 = wx.StaticText(self, label="Pt 1 Target")
        self.spin_cal_pt1 = wx.SpinCtrlDouble(self, min=0, max=1000, inc=1)
        self.label_cal_pt2 = wx.StaticText(self, label="Pt 2 Target")
        self.spin_cal_pt2 = wx.SpinCtrlDouble(self, min=0, max=1000, inc=1)
        self.spin_cal_pt1.Digits = 3
        self.spin_cal_pt2.Digits = 3
        self.label_cal_pt1_val = wx.StaticText(self, label='No reading')
        self.label_cal_pt2_val = wx.StaticText(self, label='No reading')
        self.btn_cal_pt1 = wx.Button(self, label='Pt 1 Reading')
        self.btn_cal_pt2 = wx.Button(self, label='Pt 2 Reading')

        self.btn_calibrate = wx.Button(self, label='Update Calibration')
        self.btn_save_cal = wx.Button(self, label='Save Cal')
        self.btn_load_cal = wx.Button(self, label='Load Cal')
        self.btn_reset_cal = wx.Button(self, label='Reset Cal')

        self.__do_layout()
        self.__set_bindings()

        self.update_controls_from_config()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center()

        sizer = wx.GridSizer(cols=4)
        sizer.Add(self.label_cal_pt1, flags)
        sizer.Add(self.spin_cal_pt1, flags)
        sizer.Add(self.btn_cal_pt1, flags)
        sizer.Add(self.label_cal_pt1_val, flags)

        sizer.Add(self.label_cal_pt2, flags)
        sizer.Add(self.spin_cal_pt2, flags)
        sizer.Add(self.btn_cal_pt2, flags)
        sizer.Add(self.label_cal_pt2_val, flags)

        sizer.Add(self.btn_load_cal, flags)
        sizer.Add(self.btn_save_cal, flags)
        sizer.Add(self.btn_reset_cal, flags)
        sizer.Add(self.btn_calibrate, flags)
        self.sizer = sizer

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_cal_pt1.Bind(wx.EVT_BUTTON, self.on_cal_pt1)
        self.btn_cal_pt2.Bind(wx.EVT_BUTTON, self.on_cal_pt2)
        self.btn_calibrate.Bind(wx.EVT_BUTTON, self.on_calibrate)
        self.btn_reset_cal.Bind(wx.EVT_BUTTON, self.on_reset_cal)
        self.btn_load_cal.Bind(wx.EVT_BUTTON, self.on_load_cfg)
        self.btn_save_cal.Bind(wx.EVT_BUTTON, self.on_save_cfg)

    def on_reset_cal(self, evt):
        self._sensor.hw.cfg.cal_pt1_target = 0.0
        self._sensor.hw.cfg.cal_pt1_reading = 1.0
        self._sensor.hw.cfg.cal_pt2_target = 0.0
        self._sensor.hw.cfg.cal_pt2_reading = 1.0
        self.update_controls_from_config()

    def on_cal_pt1(self, evt):
        t, val = self._reader.retrieve_buffer(0, 1)
        val = float(val)
        self._lgr.debug(f'OnCalPt1: {val}')
        self.label_cal_pt1_val.SetLabel(f'{val:.3f}')

    def on_cal_pt2(self, evt):
        t, val = self._reader.retrieve_buffer(0, 1)
        val = float(val)
        self.label_cal_pt2_val.SetLabel(f'{val:.3f}')

    def on_calibrate(self, evt):
        low_pt = self.spin_cal_pt1.GetValue()
        low_read = float(self.label_cal_pt1_val.GetLabel())
        high_pt = self.spin_cal_pt2.GetValue()
        high_read = float(self.label_cal_pt2_val.GetLabel())
        self._sensor.hw.cfg.cal_pt1_target = low_pt
        self._sensor.hw.cfg.cal_pt1_reading = low_read
        self._sensor.hw.cfg.cal_pt2_target = high_pt
        self._sensor.hw.cfg.cal_pt2_reading = high_read

    def update_config_from_controls(self):
        self._sensor.hw.cfg.cal_pt1_target = self.spin_cal_pt1.GetValue()
        self._sensor.hw.cfg.cal_pt1_reading = float(self.label_cal_pt1_val.GetLabel())
        self._sensor.hw.cfg.cal_pt2_target = self.spin_cal_pt2.GetValue()
        self._sensor.hw.cfg.cal_pt2_reading = float(self.label_cal_pt2_val.GetLabel())

    def update_controls_from_config(self):
        try:
            self.spin_cal_pt1.SetValue(self._sensor.hw.cfg.cal_pt1_target)
            self.label_cal_pt1_val.SetLabel(str(self._sensor.hw.cfg.cal_pt1_reading))
            self.spin_cal_pt2.SetValue(self._sensor.hw.cfg.cal_pt2_target)
            self.label_cal_pt2_val.SetLabel(str(self._sensor.hw.cfg.cal_pt2_reading))
        except AttributeError:
            # this should only happen if the hardware didn't load
            pass

    def on_save_cfg(self, evt):
        self.update_config_from_controls()
        self._sensor.hw.write_config()

    def on_load_cfg(self, evt):
        self._sensor.hw.read_config(self._sensor.hw.name)
        self.update_controls_from_config()


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self._lgr = logging.getLogger(__name__)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        try:
            self.panel = PanelAI(self, sensor, reader=sensor.get_reader('Raw'))
        except:
            # catch any exception to properly close SYS_HW
            self.on_close(wx.Event())
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, evt):
        SYS_HW.stop()
        sensor.close()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    lgr = logging.getLogger()
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(lgr, logging.DEBUG)
    utils.configure_matplotlib_logging()

    SYS_HW.load_hardware_from_config()
    sensor = Sensor.Sensor(name='Hepatic Artery Flow')
    sensor.read_config()

    sensor.start()
    SYS_HW.start()

    app = MyTestApp(0)
    app.MainLoop()
