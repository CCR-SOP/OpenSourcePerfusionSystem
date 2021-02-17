# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for testing and configuring AIO
"""
from pathlib import Path

from configparser import ConfigParser
import wx
import time

from pyHardware.pyAO_NIDAQ import NIDAQ_AO
import pyPerfusion.PerfusionConfig as LP_CFG


DEV_LIST = ['Dev1', 'Dev2', 'Dev3', 'Dev4', 'Dev5']
LINE_LIST = [f'{line}' for line in range(0, 9)]


class PanelAO(wx.Panel):
    def __init__(self, parent, aio, name):
        self.parent = parent
        self._ao = aio
        self._name = name
        wx.Panel.__init__(self, parent, -1)

        self._avail_dev = DEV_LIST
        self._avail_lines = LINE_LIST

        self._panel_cfg = PanelAO_Config(self, self._ao, name, 'Configuration')
        self._panel_settings = PanelAO_Settings(self, self._ao, name, 'Settings')
        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand()

        self.sizer.Add(self._panel_cfg, flags)
        self.sizer.AddSpacer(5)
        self.sizer.Add(self._panel_settings)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass


class PanelAO_Config(wx.Panel):
    def __init__(self, parent, aio, name, sizer_name):
        self.parent = parent
        self._ao = aio
        self._name = name
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

        self.sizer.Add(self.btn_open, flags)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_save_cfg, flags)
        sizer.AddSpacer(5)
        sizer.Add(self.btn_load_cfg, flags)
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
            self._ao.open(line, period_ms=10, dev=dev)
            self._ao.set_dc(0)  # Some of the peristaltic pumps need to be set to run at 0 V to activate their analog control
            self.btn_open.SetLabel('Close')
            self._ao.start()
        else:
            self._ao.set_dc(0)  # Turn off voltage when closing the channel
            time.sleep(0.1)  # Make sure thread updates voltage to 0 prior to closing channel
            self._ao.close()
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

class PanelAO_Settings(wx.Panel):
    def __init__(self, parent, aio, name, sizer_name):
        self.parent = parent
        self._ao = aio
        self._name = name
        wx.Panel.__init__(self, parent, -1)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=sizer_name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

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
        flags = wx.SizerFlags(0)
        self.sizer.Add(self.btn_update, flags)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_save_cfg, flags)
        sizer.AddSpacer(5)
        sizer.Add(self.btn_load_cfg, flags)
        self.sizer.Add(sizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_update.Bind(wx.EVT_BUTTON, self.OnUpdate)
        self.check_sine.Bind(wx.EVT_CHECKBOX, self.OnSine)
        self.btn_save_cfg.Bind(wx.EVT_BUTTON, self.OnSaveCfg)
        self.btn_load_cfg.Bind(wx.EVT_BUTTON, self.OnLoadCfg)

    def OnUpdate(self, evt):
        volts = self.spin_pk2pk.GetValue()
        hz = self.spin_hz.GetValue()
        offset = self.spin_offset.GetValue()
        want_sine = self.check_sine.IsChecked()

        if want_sine:
            self._ao.set_sine(volts_p2p=volts, volts_offset=offset, Hz=hz)
        else:
            self._ao.set_dc(offset)

    def OnSine(self, evt):
        want_sine = self.check_sine.IsChecked()
        self.spin_hz.Enable(want_sine)
        self.spin_pk2pk.Enable(want_sine)

    def OnSaveCfg(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        section['VoltsPk2Pk'] = f'{self.spin_pk2pk.GetValue():.3f}'
        section['VoltsOffset'] = f'{self.spin_offset.GetValue():.3f}'
        section['Frequency'] = f'{self.spin_hz.GetValue():.3f}'
        section['SineOutput'] = f'{self.check_sine.IsChecked()}'
        LP_CFG.update_hwcfg_section(self._name, section)

    def OnLoadCfg(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        self.spin_pk2pk.SetValue(section.getfloat('VoltsPk2Pk'))
        self.spin_offset.SetValue(section.getfloat('VoltsOffset'))
        self.spin_hz.SetValue(section.getfloat('Frequency'))
        self.check_sine.SetValue(section.getboolean('SineOutput'))
        self.OnSine(wx.EVT_CHECKBOX)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.ao = NIDAQ_AO()
        ao_name = 'Analog Output'
        self.panel = PanelAO(self, self.ao, name=ao_name)
        # self.panel = PanelAO_Config(self, self.ao, name='Configuration', sizer_name='Configuration')
        # self.panel = PanelAO_Settings(self, self.ao, name=ao_name, sizer_name='Settings')


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    app = MyTestApp(0)
    app.MainLoop()
