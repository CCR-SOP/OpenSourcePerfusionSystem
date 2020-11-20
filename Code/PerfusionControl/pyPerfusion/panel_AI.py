# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for testing and configuring AIO
"""
from pathlib import Path

from configparser import ConfigParser
import wx

from pyHardware.pyAI_NIDAQ import NIDAQ_AI
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.panel_plotting import PanelPlotting
from pyPerfusion.SensorStream import SensorStream


DEV_LIST = ['Dev1', 'Dev2', 'Dev3', 'Dev4', 'Dev5']
LINE_LIST = [f'{line}' for line in range(0, 9)]


class PanelAI(wx.Panel):
    def __init__(self, parent, name, sensor):
        self.parent = parent
        self._name = name
        self._sensor = sensor
        wx.Panel.__init__(self, parent, -1)

        LP_CFG.set_base()
        LP_CFG.update_stream_folder()

        self._avail_dev = DEV_LIST
        self._avail_lines = LINE_LIST

        self._panel_cfg = PanelAI_Config(self, name, 'Configuration', self._sensor)
        self._panel_settings = PanelAI_Settings(self, self._sensor, name, 'Settings')
        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.panel_plot = PanelPlotting(self)
        self.panel_plot.add_sensor(self._sensor)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand()

        self.sizer.Add(self._panel_cfg, flags)
        self.sizer.AddSpacer(5)
        self.sizer.Add(self._panel_settings, flags)

        self.sizer.Add(self.panel_plot, 1, wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass


class PanelAI_Config(wx.Panel):
    def __init__(self, parent, name, sizer_name, sensor):
        self.parent = parent
        self._name = name
        self._sensor = sensor
        wx.Panel.__init__(self, parent, -1)

        self._avail_dev = DEV_LIST
        self._avail_lines = LINE_LIST

        static_box = wx.StaticBox(self, wx.ID_ANY, label=sizer_name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)
        self.label_dev = wx.StaticText(self, label='NI Device Name')
        self.choice_dev = wx.Choice(self, wx.ID_ANY, choices=self._avail_dev)

        self.label_line = wx.StaticText(self, label='Line Number')
        self.choice_line = wx.Choice(self, wx.ID_ANY, choices=self._avail_lines)

        self.btn_open = wx.ToggleButton(self, label='Open')
        self.btn_save_cfg = wx.Button(self, label='Save Config')
        self.btn_load_cfg = wx.Button(self, label='Load Config')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Left().Proportion(0)
        self.sizer_dev = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_dev.Add(self.label_dev, flags)
        self.sizer_dev.Add(self.choice_dev, flags)

        self.sizer_line = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_line.Add(self.label_line, flags)
        self.sizer_line.Add(self.choice_line, flags)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sizer_dev)
        sizer.AddSpacer(10)
        sizer.Add(self.sizer_line)
        self.sizer.Add(sizer)

        self.sizer.AddSpacer(5)
        self.sizer.Add(self.btn_open, flags)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_save_cfg, flags)
        sizer.AddSpacer(5)
        sizer.Add(self.btn_load_cfg, flags)
        self.sizer.AddSpacer(5)
        self.sizer.Add(sizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_open.Bind(wx.EVT_TOGGLEBUTTON, self.OnOpen)
        self.btn_save_cfg.Bind(wx.EVT_BUTTON, self.OnSaveCfg)
        self.btn_load_cfg.Bind(wx.EVT_BUTTON, self.OnLoadCfg)

    def OnOpen(self, evt):
        state = self.btn_open.GetValue()
        if state:
            dev = self.choice_dev.GetStringSelection()
            line = self.choice_line.GetStringSelection()
            print(f'dev is {dev}, line is {line}')
            self._sensor.hw.open(period_ms=10, line=line, dev=dev)
            self.btn_open.SetLabel('Close',)
            self._sensor.start()
        else:
            self._sensor.close()
            self.btn_open.SetLabel('Open')

    def OnSaveCfg(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        section['DevName'] = self.choice_dev.GetStringSelection()
        section['LineName'] = self.choice_line.GetStringSelection()
        LP_CFG.update_hwcfg_section(self._name, section)

    def OnLoadCfg(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        # _period_ms = int(section['SamplingPeriod_ms'])
        # _bits = int(section['SampleDepth'])
        self.choice_dev.SetStringSelection(section['DevName'])
        self.choice_line.SetStringSelection(section['LineName'])

class PanelAI_Settings(wx.Panel):
    def __init__(self, parent, sensor, name, sizer_name):
        self.parent = parent
        self._sensor = sensor
        self._name = name
        wx.Panel.__init__(self, parent, -1)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=sizer_name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_cal_pt1 = wx.StaticText(self, label="Calibration Pt 1")
        self.spin_cal_pt1 = wx.SpinCtrlDouble(self, min=0, max=1000, inc=1)
        self.label_cal_pt2 = wx.StaticText(self, label="Calibration Pt 2")
        self.spin_cal_pt2 = wx.SpinCtrlDouble(self, min=0, max=1000, inc=1)
        self.spin_cal_pt1.Digits = 3
        self.spin_cal_pt2.Digits = 3
        self.label_cal_pt1_val = wx.StaticText(self, label='No reading')
        self.label_cal_pt2_val = wx.StaticText(self, label='No reading')
        self.btn_cal_pt1 = wx.Button(self, label='Read Cal Pt 1')
        self.btn_cal_pt2 = wx.Button(self, label='Read Cal Pt 2')
        # self.spin_period_ms = wx.SpinCtrl(self, min=0, max=1000, initial=100)
        # self.lbl_period_ms = wx.StaticText(self, label='Sampling Period (ms)')

        self.btn_save_cfg = wx.Button(self, label='Save Settings')
        self.btn_load_cfg = wx.Button(self, label='Load Settings')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags(0).Expand()

        # sizer = wx.GridSizer(cols=3, hgap=5, vgap=2)
        # sizer.Add(self.spin_period_ms, flags)
        # sizer.Add(self.lbl_period_ms, flags)
        # self.sizer.Add(sizer, flags)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_save_cfg, flags)
        sizer.AddSpacer(5)
        sizer.Add(self.btn_load_cfg, flags)
        self.sizer.AddSpacer(10)
        self.sizer.Add(sizer)

        # Calibration
        sizer = wx.GridSizer(cols=4)
        sizer.Add(self.label_cal_pt1, flags)
        sizer.Add(self.spin_cal_pt1, flags)
        sizer.Add(self.btn_cal_pt1, flags)
        sizer.Add(self.label_cal_pt1_val, flags)
        sizer.Add(self.label_cal_pt2, flags)
        sizer.Add(self.spin_cal_pt2, flags)
        sizer.Add(self.btn_cal_pt2, flags)
        sizer.Add(self.label_cal_pt2_val, flags)
        self.sizer.Add(sizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_save_cfg.Bind(wx.EVT_BUTTON, self.OnSaveCfg)
        self.btn_load_cfg.Bind(wx.EVT_BUTTON, self.OnLoadCfg)
        self.btn_cal_pt1.Bind(wx.EVT_BUTTON, self.OnCalPt1)
        self.btn_cal_pt2.Bind(wx.EVT_BUTTON, self.OnCalPt2)


    def OnCalPt1(self, evt):
        val = self._sensor.get_current()
        print(f'{val}')
        self.label_cal_pt1_val.SetLabel(f'{val:.3f}')

    def OnCalPt2(self, evt):
        val = self._sensor.get_current()
        self.label_cal_pt2_val.SetLabel(f'{val:.3f}')

    def OnSaveCfg(self, evt):
        pass

    def OnLoadCfg(self, evt):
        pass


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        LP_CFG.set_base()
        LP_CFG.update_stream_folder()
        self.ai = NIDAQ_AI()
        self.sensor = SensorStream('Flow', 'ml/min', self.ai)
        self.sensor.open(LP_CFG.LP_PATH['stream'])
        ao_name = 'Analog Input'
        self.panel = PanelAI(self, name=ao_name, sensor=self.sensor)
        # self.panel = PanelAI_Config(self, name='Analog Input', sizer_name='Configuration', sensor=self.sensor)
        # self.panel = PanelAI_Settings(self, name=ao_name, sizer_name='Settings', sensor=self.sensor)


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    app = MyTestApp(0)
    app.MainLoop()
