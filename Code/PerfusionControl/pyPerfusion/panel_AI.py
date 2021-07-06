# -*- coding: utf-8 -*-
"""Panel class for testing and configuring AIO


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

from pyHardware.pyAI import AIDeviceException
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.panel_plotting import PanelPlotting
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.utils as utils
from pyPerfusion.ProcessingStrategy import RMSStrategy
from pyPerfusion.FileStrategy import StreamToFile

DEV_LIST = ['Dev1', 'Dev2', 'Dev3', 'Dev4', 'Dev5']
LINE_LIST = [f'{line}' for line in range(0, 9)]


class PanelAI(wx.Panel):
    def __init__(self, parent, sensor, name):
        wx.Panel.__init__(self, parent, -1)
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self._sensor = sensor
        self._name = name
        self._dev = None

        self._avail_dev = DEV_LIST
        self._avail_lines = LINE_LIST

        self._panel_plot = PanelPlotting(self)
        self._panel_cfg = PanelAI_Config(self, self._sensor, name, 'Configuration', plot=self)
        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.__do_layout()
        self.__set_bindings()

        self._panel_plot.add_sensor(self._sensor, self._sensor.get_file_strategy())
        self._sensor.start()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()

        self.sizer.Add(self._panel_cfg, flags.Proportion(2))
        self.sizer.SetSizeHints(self.parent)
        self.sizer.Add(self._panel_plot, flags.Proportion(3))
        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass

    def force_device(self, dev):
        self._dev = dev
        self._panel_cfg.choice_dev.SetStringSelection(self._dev)
        self._panel_cfg.choice_dev.Enable(False)


class PanelAI_Config(wx.Panel):
    def __init__(self, parent, sensor, name, sizer_name, plot):
        super().__init__(parent, -1)
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self._sensor = sensor
        self._name = name

        self._update_plot = plot

        self._avail_dev = DEV_LIST
        self._avail_lines = LINE_LIST

        # static_box = wx.StaticBox(self, wx.ID_ANY, label=sizer_name)
        # self.sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.label_dev = wx.StaticText(self, label='NI Device Name')
        self.choice_dev = wx.Choice(self, wx.ID_ANY, choices=self._avail_dev)

        self.label_line = wx.StaticText(self, label='Line Number')
        self.choice_line = wx.Choice(self, wx.ID_ANY, choices=self._avail_lines)

        self.btn_open = wx.ToggleButton(self, label='Open')

        self.btn_save_cfg = wx.Button(self, label='Save')
        self.btn_load_cfg = wx.Button(self, label='Load')

        self.panel_cal = PanelAICalibration(self, sensor, self._name)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center()

        sizer_cfg = wx.GridSizer(cols=2)
        sizer_cfg.Add(self.label_dev, flags)
        sizer_cfg.Add(self.choice_dev, flags)

        sizer_cfg.Add(self.label_line, flags)
        sizer_cfg.Add(self.choice_line, flags)

        sizer_cfg.Add(self.btn_open, flags)
        sizer_cfg.AddSpacer(2)
        sizer_cfg.Add(self.btn_load_cfg, flags)
        sizer_cfg.Add(self.btn_save_cfg, flags)
        self.sizer.Add(sizer_cfg)

        self.sizer.Add(self.panel_cal, 1, wx.EXPAND | wx.ALL)
        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_open.Bind(wx.EVT_TOGGLEBUTTON, self.OnOpen)
        self.btn_save_cfg.Bind(wx.EVT_BUTTON, self.OnSaveCfg)
        self.btn_load_cfg.Bind(wx.EVT_BUTTON, self.OnLoadCfg)

    def OnOpen(self, evt):
        state = self.btn_open.GetValue()
        dev = self.choice_dev.GetStringSelection()
        line = self.choice_line.GetStringSelection()
        if state:
            self._logger.debug(f'Opening device {dev}, {line}')
            try:
                self._sensor.hw.open(dev=dev)
                self._sensor.hw.add_channel(line)
                self._sensor.set_ch_id(line)

            except AIDeviceException as e:
                dlg = wx.MessageDialog(parent=self, message=str(e), caption='AI Device Error', style=wx.OK)
                dlg.ShowModal()
            if self._sensor.hw.is_open():
                self.btn_open.SetLabel('Close')
                self._sensor.hw.start()
            else:
                self._sensor.hw.remove_channel(line)
                self.btn_open.SetValue(0)
        else:
            self._logger.debug(f'Closing device {dev}, {line}')
            self._sensor.hw.remove_channel(line)
            self.btn_open.SetLabel('Open')


    def OnSaveCfg(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        section['DevName'] = self.choice_dev.GetStringSelection()
        section['LineName'] = self.choice_line.GetStringSelection()
        LP_CFG.update_hwcfg_section(self._name, section)

    def OnLoadCfg(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        self.choice_dev.SetStringSelection(section['DevName'])
        self.choice_line.SetStringSelection(section['LineName'])


class PanelAICalibration(wx.Panel):
    def __init__(self, parent, sensor, name):
        super().__init__(parent, -1)
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self._sensor = sensor
        self._name = name

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.label_cal_pt1 = wx.StaticText(self, label="Cal Pt 1")
        self.spin_cal_pt1 = wx.SpinCtrlDouble(self, min=0, max=1000, inc=1)
        self.label_cal_pt2 = wx.StaticText(self, label="Cal Pt 2")
        self.spin_cal_pt2 = wx.SpinCtrlDouble(self, min=0, max=1000, inc=1)
        self.spin_cal_pt1.Digits = 3
        self.spin_cal_pt2.Digits = 3
        self.label_cal_pt1_val = wx.StaticText(self, label='No reading')
        self.label_cal_pt2_val = wx.StaticText(self, label='No reading')
        self.btn_cal_pt1 = wx.Button(self, label='Read Cal Pt 1')
        self.btn_cal_pt2 = wx.Button(self, label='Read Cal Pt 2')

        self.btn_calibrate = wx.Button(self, label='Calibrate')
        self.btn_reset_cal = wx.Button(self, label='Reset Cal')
        self.btn_save_cal = wx.Button(self, label='Save Cal')
        self.btn_load_cal = wx.Button(self, label='Load Cal')

        self.__do_layout()
        self.__set_bindings()

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

        sizer.Add(self.btn_calibrate, flags)
        sizer.Add(self.btn_reset_cal, flags)
        sizer.Add(self.btn_load_cal, flags)
        sizer.Add(self.btn_save_cal, flags)
        self.sizer = sizer

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_cal_pt1.Bind(wx.EVT_BUTTON, self.OnCalPt1)
        self.btn_cal_pt2.Bind(wx.EVT_BUTTON, self.OnCalPt2)
        self.btn_calibrate.Bind(wx.EVT_BUTTON, self.OnCalibrate)
        self.btn_reset_cal.Bind(wx.EVT_BUTTON, self.OnResetCalibration)
        self.btn_load_cal.Bind(wx.EVT_BUTTON, self.OnLoadCfg)
        self.btn_save_cal.Bind(wx.EVT_BUTTON, self.OnSaveCfg)

    def OnCalPt1(self, evt):
        val = self._sensor.get_current()
        self.label_cal_pt1_val.SetLabel(f'{val:.3f}')

    def OnCalPt2(self, evt):
        val = self._sensor.get_current()
        self.label_cal_pt2_val.SetLabel(f'{val:.3f}')

    def OnCalibrate(self, evt):
        low_pt = self.spin_cal_pt1.GetValue()
        low_read = float(self.label_cal_pt1_val.GetLabel())
        high_pt = self.spin_cal_pt2.GetValue()
        high_read = float(self.label_cal_pt2_val.GetLabel())
        channel = self._sensor.ch_id
        self._sensor.hw.set_calibration(channel, low_pt, low_read, high_pt, high_read)

    def OnResetCalibration(self, evt):
        channel = self._sensor.ch_id
        self._sensor.hw.set_calibration(channel, 0, 0, 1, 1)
        self.spin_cal_pt1.SetValue(0)
        self.spin_cal_pt2.SetValue(1)
        self.label_cal_pt1_val.SetLabel('0')
        self.label_cal_pt2_val.SetLabel('1')

    def OnSaveCfg(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        section['CalPt1_Target'] = f'{self.spin_cal_pt1.GetValue():.3f}'
        section['CalPt1_Reading'] = self.label_cal_pt1_val.GetLabel()
        section['CalPt2_Target'] = f'{self.spin_cal_pt2.GetValue():.3f}'
        section['CalPt2_Reading'] = self.label_cal_pt2_val.GetLabel()
        LP_CFG.update_hwcfg_section(self._name, section)

    def OnLoadCfg(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        self.spin_cal_pt1.SetValue(float(section['CalPt1_Target']))
        self.label_cal_pt1_val.SetLabel(section['CalPt1_Reading'])
        self.spin_cal_pt2.SetValue(float(section['CalPt2_Target']))
        self.label_cal_pt2_val.SetLabel(section['CalPt2_Reading'])


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        ai_name = 'Analog Input'
        self.acq = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
        self.sensor = SensorStream('Analog Input 1', 'Volts', self.acq)
        self.raw = StreamToFile('StreamRaw', None, self.acq.buf_len)
        self.raw.open(LP_CFG.LP_PATH['stream'], f'{self.sensor.name}_raw', self.sensor.params)
        self.sensor.add_strategy(self.raw)
        self.panel = PanelAI(self, self.sensor, name=ai_name)

        # self.panel = PanelAI_Config(self, self.sensor, 'test', 'test', None)
        # self.panel = PanelAICalibration(self, self.sensor)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.sensor.stop()
        self.Destroy()

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
    utils.configure_matplotlib_logging()
    app = MyTestApp(0)
    app.MainLoop()
