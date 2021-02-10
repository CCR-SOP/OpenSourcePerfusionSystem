# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for testing and configuring AIO
"""
import wx

from pyHardware.pyAI_NIDAQ import NIDAQ_AI
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.panel_plotting import PanelPlotting
from pyPerfusion.SensorStream import SensorStream


DEV_LIST = ['Dev1', 'Dev2', 'Dev3', 'Dev4', 'Dev5']
LINE_LIST = [f'{line}' for line in range(0, 9)]


class PanelAI(wx.Panel):
    def __init__(self, parent, sensor, name):
        self.parent = parent
        self._sensor = sensor
        self._name = name
        wx.Panel.__init__(self, parent, -1)

        self._avail_dev = DEV_LIST
        self._avail_lines = LINE_LIST

        self._panel_plot = PanelPlotting(self)
        self._panel_cfg = PanelAI_Config(self, self._sensor, name, 'Configuration', plot=self)
        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.__do_layout()
        self.__set_bindings()

        self._panel_plot.add_sensor(self._sensor)
        self._sensor.start()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand()

        self.sizer.Add(self._panel_cfg, flags)
        self.sizer.AddSpacer(5)
        self.sizer.Add(self._panel_plot, 1, wx.ALL | wx.EXPAND, border=1)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass


class PanelAI_Config(wx.Panel):
    def __init__(self, parent, sensor, name, sizer_name, plot):
        self.parent = parent
        self._sensor = sensor
        self._name = name
        wx.Panel.__init__(self, parent, -1)
        self._update_plot = plot

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

        self._sensor.open(LP_CFG.LP_PATH['stream'])

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
        dev = self.choice_dev.GetStringSelection()
        line = self.choice_line.GetStringSelection()
        if state:

            print(f'dev is {dev}, line is {line}')
            self._sensor.hw.add_channel(line)
            self._sensor.hw.open(dev=dev)
            self._sensor.hw.start()
            self._sensor.set_ch_id(line)
            self.btn_open.SetLabel('Close',)
        else:
            self._sensor.hw.stop()
            self._sensor.hw.remove_channel(line)
            self._sensor.hw.close()
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


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        ai_name = 'Analog Input'
        self.acq = NIDAQ_AI(period_ms=1, volts_p2p=5, volts_offset=2.5)
        self.sensor = SensorStream('Analog Input 1', 'Volts', self.acq)
        self.panel = PanelAI(self, self.sensor, name=ai_name)
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
    app = MyTestApp(0)
    app.MainLoop()
