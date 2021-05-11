# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for testing and configuring DIO
"""
import logging
import pyPerfusion.utils as utils

import wx

from pyHardware.pyDIO import DIODeviceException
from pyHardware.pyDIO_NIDAQ import NIDAQ_DIO
import pyPerfusion.PerfusionConfig as LP_CFG

DEV_LIST = ['Dev1', 'Dev2', 'Dev3', 'Dev4', 'Dev5']
PORT_LIST = [f'port{p}' for p in range(0, 5)]
LINE_LIST = [f'line{line}' for line in range(0, 9)]


class PanelDIO(wx.Panel):
    def __init__(self, parent, dio, name):
        wx.Panel.__init__(self, parent, -1)
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self._dio = dio
        self._name = name

        self._avail_dev = DEV_LIST
        self._avail_ports = PORT_LIST
        self._avail_lines = LINE_LIST

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self._panel_cfg = PanelDIOConfig(self, self._dio, self._name)
        self._panel_controls = PanelDIOControls(self, self._dio, self._name, display_config=True)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        self.sizer.Add(self._panel_cfg)
        self.sizer.Add(self._panel_controls)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self._panel_cfg.btn_open.Bind(wx.EVT_TOGGLEBUTTON, self.OnOpen)

    def OnOpen(self, evt):
        self._panel_cfg.OnOpen(evt)
        self._panel_controls.update_label()
        self._logger.debug(f'is_open is {self._dio.is_open} readonly = {self._dio.read_only}')
        self._panel_controls.Enable(self._dio.is_open and not self._dio.read_only)


class PanelDIOConfig(wx.Panel):
    def __init__(self, parent, dio, name):
        wx.Panel.__init__(self, parent, -1)
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self._dio = dio
        self._name = name

        self._avail_dev = DEV_LIST
        self._avail_ports = PORT_LIST
        self._avail_lines = LINE_LIST

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.btn_open = wx.ToggleButton(self, label='Open')

        self.label_dev = wx.StaticText(self, label='Device')
        self.choice_dev = wx.Choice(self, wx.ID_ANY, choices=self._avail_dev)

        self.label_port = wx.StaticText(self, label='Port')
        self.choice_port = wx.Choice(self, wx.ID_ANY, choices=self._avail_ports)

        self.label_line = wx.StaticText(self, label='Line')
        self.choice_line = wx.Choice(self, wx.ID_ANY, choices=self._avail_lines)

        self.choice_active = wx.Choice(self, choices=['Active Low', 'Active High'])
        self.choice_active.SetSelection(1)
        self.check_read_only = wx.CheckBox(self, label='Read Only')

        self.btn_save = wx.Button(self, label='Save Config')
        self.btn_load = wx.Button(self, label='Load Config')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center().Proportion(0)
        gridflags = wx.SizerFlags(0).Border(wx.LEFT | wx.RIGHT, 3)
        sizer_dev = wx.GridSizer(cols=3, hgap=5, vgap=2)
        sizer_dev.Add(self.label_dev, gridflags)
        sizer_dev.Add(self.label_port, gridflags)
        sizer_dev.Add(self.label_line, gridflags)
        sizer_dev.Add(self.choice_dev, gridflags)
        sizer_dev.Add(self.choice_port, gridflags)
        sizer_dev.Add(self.choice_line, gridflags)

        sizer_config = wx.BoxSizer(wx.HORIZONTAL)
        sizer_config.Add(self.btn_open, flags)
        sizer_config.Add(self.btn_save, flags)
        sizer_config.Add(self.btn_load, flags)

        sizer_params = wx.BoxSizer(wx.VERTICAL)
        sizer_params.Add(self.choice_active, flags)
        sizer_params.Add(self.check_read_only, flags)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(sizer_dev)
        sizer.Add(sizer_params)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(5)
        self.sizer.Add(sizer_config)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_open.Bind(wx.EVT_TOGGLEBUTTON, self.OnOpen)
        self.btn_save.Bind(wx.EVT_BUTTON, self.OnSaveConfig)
        self.btn_load.Bind(wx.EVT_BUTTON, self.OnLoadConfig)

    def OnOpen(self, evt):
        state = self.btn_open.GetLabel()
        if state == 'Open':
            dev = self.choice_dev.GetStringSelection()
            port = self.choice_port.GetStringSelection()
            line = self.choice_line.GetStringSelection()
            active_high = self.choice_active.GetSelection() == 1
            read_only = self.check_read_only.GetValue()
            try:
                self._dio.open(port, line, active_high, read_only, dev)
            except DIODeviceException as e:
                dlg = wx.MessageDialog(parent=self, message=str(e), caption='DIO Device Error', style=wx.OK)
                dlg.ShowModal()
            else:
                self._dio.deactivate()  # Make sure lines are turned off upon opening; due to fact that sometimes when the DAQ is first powered on, all lines will be open
                self.btn_open.SetLabel('Close')
                self.btn_load.Enable(False)
        else:
            self._dio.deactivate()
            self._dio.close()
            self.btn_open.SetLabel('Open')
        self._disable_controls_on_open()

    def _disable_controls_on_open(self):
        enable = not self._dio.is_open
        self._logger.debug(enable)
        ctrls = [self.btn_load, self.choice_active, self.check_read_only,
                 self.choice_dev, self.choice_port, self.choice_line]
        for ctrl in ctrls:
            ctrl.Enable(enable)

    def OnSaveConfig(self, evt):
         section = LP_CFG.get_hwcfg_section(self._name)
         section['Device'] = self.choice_dev.GetStringSelection()
         section['Port'] = self.choice_port.GetStringSelection()
         section['Line'] = self.choice_line.GetStringSelection()
         section['Active High'] = str(self.choice_active.GetSelection() == 1)
         section['Read Only'] = str(self.check_read_only.GetValue())
         LP_CFG.update_hwcfg_section(self._name, section)

    def OnLoadConfig(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        self.choice_dev.SetStringSelection(section['Device'])
        self.choice_port.SetStringSelection(section['Port'])
        self.choice_line.SetStringSelection(section['Line'])
        active_high_state = (section['Active High'] != 'True')
        self.choice_active.SetSelection(active_high_state)
        read_only_state = (section['Read Only'] == 'True')
        self.check_read_only.SetValue(read_only_state)


class PanelDIOControls(wx.Panel):
    def __init__(self, parent, dio, name, display_config=False):
        wx.Panel.__init__(self, parent, -1)
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self._dio = dio
        self._name = name
        self._display_config = display_config
        self._timer = wx.Timer()

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self._label_cfg = wx.StaticText(self, label='')
        self._label_cfg.Show(self._display_config)
        self._label_active = wx.StaticText(self, label='')
        self._label_active.Show(self._display_config)

        self.btn_activate = wx.ToggleButton(self, label='Activate')

        self.btn_pulse = wx.Button(self, label='Pulse')
        self.spin_pulse = wx.SpinCtrl(self, min=1, max=20000, initial=10)
        self.lbl_pulse = wx.StaticText(self, label='ms')

        self.__do_layout()
        self.__set_bindings()

        self._timer.Start(milliseconds=1000)

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 2).Center().CenterVertical().Proportion(0)

        sizer_pulse = wx.BoxSizer(wx.HORIZONTAL)
        sizer_pulse.Add(self.spin_pulse, flags)
        sizer_pulse.Add(self.lbl_pulse, flags)

        sizer_test = wx.BoxSizer(wx.HORIZONTAL)
        sizer_test.Add(self.btn_activate, flags)
        sizer_test.Add(self.btn_pulse, flags)
        sizer_test.Add(sizer_pulse, flags)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self._label_active, flags)
        sizer.AddSpacer(5)
        sizer.Add(self._label_cfg, flags)
        self.sizer.Add(sizer)
        self.sizer.Add(sizer_test)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_activate.Bind(wx.EVT_TOGGLEBUTTON, self.OnActivate)
        self.btn_pulse.Bind(wx.EVT_BUTTON, self.OnPulse)
        self._timer.Bind(wx.EVT_TIMER, self._update_active)

    def OnActivate(self, evt):
        state = self.btn_activate.GetLabel()
        if state == 'Activate':
            self._dio.activate()
            self.btn_activate.SetLabel('Deactivate')
        else:
            self._dio.deactivate()
            self.btn_activate.SetLabel('Activate')

    def OnPulse(self, evt):
        ms = self.spin_pulse.GetValue()
        self._logger.info(f'Pulsing for {ms} ms')
        self._dio.pulse(ms)

    def update_label(self):
        active_str = str(self._dio.active_state)
        read_str = 'Read Only' if self._dio.read_only else 'Write Only'
        cfg_str = f'{self._dio.devname} {active_str} {read_str}'
        self._label_cfg.SetLabel(cfg_str)
        self.Layout()

    def _update_active(self, evt):
        color = wx.GREEN if self._dio.value else wx.RED
        lbl = 'Active' if self._dio.value else 'Inactive'
        self._label_active.SetLabel(lbl)
        self._label_active.SetBackgroundColour(color)
        self.Layout()

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.dio = NIDAQ_DIO()
        self.panel = PanelDIO(self, self.dio, 'DIO')


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    LP_CFG.set_base(basepath='~/Documents/LPTEST')
    LP_CFG.update_stream_folder()
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    utils.setup_stream_logger(logger, logging.DEBUG)
    app = MyTestApp(0)
    app.MainLoop()
