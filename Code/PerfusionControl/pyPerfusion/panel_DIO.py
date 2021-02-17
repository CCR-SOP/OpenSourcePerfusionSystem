# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for testing and configuring DIO
"""
import wx
from pyHardware.pyDIO_NIDAQ import NIDAQ_DIO
import pyPerfusion.PerfusionConfig as LP_CFG

DEV_LIST = ['Dev1', 'Dev2', 'Dev3', 'Dev4', 'Dev5']
PORT_LIST = [f'port{p}' for p in range(0, 5)]
LINE_LIST = [f'line{line}' for line in range(0, 9)]


class PanelDIO(wx.Panel):
    def __init__(self, parent, dio, name):
        self.parent = parent
        self._dio = dio
        self._name = name
        wx.Panel.__init__(self, parent, -1)

        self._avail_dev = DEV_LIST
        self._avail_ports = PORT_LIST
        self._avail_lines = LINE_LIST

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_dev = wx.StaticText(self, label='NI Device Name')
        self.choice_dev = wx.Choice(self, wx.ID_ANY, choices=self._avail_dev)

        self.label_port = wx.StaticText(self, label='Port Number')
        self.choice_port = wx.Choice(self, wx.ID_ANY, choices=self._avail_ports)

        self.label_line = wx.StaticText(self, label='Line Number')
        self.choice_line = wx.Choice(self, wx.ID_ANY, choices=self._avail_lines)

        self.radio_active_sel = wx.RadioBox(self, label='Active State Selection',
                                            choices=['Active High', 'Active Low'])

        self.check_read_only = wx.CheckBox(self, label='Read Only')

        self.btn_save = wx.Button(self, label='Save Config')
        self.btn_load = wx.Button(self, label='Load Config')

        self.btn_open = wx.ToggleButton(self, label='Open')
        self.btn_activate = wx.ToggleButton(self, label='Activate')
        self.btn_activate.Enable(False)

        self.btn_pulse = wx.Button(self, label='Pulse')
        self.spin_pulse = wx.SpinCtrl(self, min=1, max=20000, initial=10)
        self.lbl_pulse = wx.StaticText(self, label='ms')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center().Proportion(0)
        gridflags = wx.SizerFlags(0).Border(wx.LEFT | wx.RIGHT, 5)
        sizer_dev = wx.GridSizer(cols=3, hgap=5, vgap=2)
        sizer_dev.Add(self.label_dev, gridflags)
        sizer_dev.Add(self.label_port, gridflags)
        sizer_dev.Add(self.label_line, gridflags)
        sizer_dev.Add(self.choice_dev, gridflags)
        sizer_dev.Add(self.choice_port, gridflags)
        sizer_dev.Add(self.choice_line, gridflags)

        sizer_pulse = wx.BoxSizer(wx.HORIZONTAL)
        sizer_pulse.Add(self.spin_pulse, flags)
        sizer_pulse.Add(self.lbl_pulse, flags)

        sizer_config = wx.BoxSizer(wx.HORIZONTAL)
        sizer_config.Add(self.btn_save, flags)
        sizer_config.Add(self.btn_load, flags)

        sizer_params = wx.BoxSizer(wx.HORIZONTAL)
        sizer_params.Add(self.radio_active_sel, flags)
        sizer_params.Add(self.check_read_only, flags)

        sizer_test = wx.GridSizer(cols=2, hgap=5, vgap=5)
        sizer_test.Add(self.btn_open, gridflags)
        sizer_test.Add(self.btn_activate, gridflags)
        sizer_test.Add(sizer_pulse, gridflags)
        sizer_test.Add(self.btn_pulse, gridflags)

        self.sizer.Add(sizer_dev)
        self.sizer.AddSpacer(5)
        self.sizer.Add(sizer_config)
        self.sizer.AddSpacer(5)
        self.sizer.Add(sizer_params)
        self.sizer.AddSpacer(5)
        self.sizer.Add(sizer_test)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_open.Bind(wx.EVT_TOGGLEBUTTON, self.OnOpen)
        self.btn_activate.Bind(wx.EVT_TOGGLEBUTTON, self.OnActivate)
        self.btn_pulse.Bind(wx.EVT_BUTTON, self.OnPulse)
        self.btn_save.Bind(wx.EVT_BUTTON, self.OnSaveConfig)
        self.btn_load.Bind(wx.EVT_BUTTON, self.OnLoadConfig)

    def OnOpen(self, evt):
        state = self.btn_open.GetLabel()
        if state == 'Open':
            dev = self.choice_dev.GetStringSelection()
            port = self.choice_port.GetStringSelection()
            line = self.choice_line.GetStringSelection()
            active_high = self.radio_active_sel.GetSelection() == 0
            read_only = self.check_read_only.GetValue()
            try:
                self._dio.open(port, line, active_high, read_only, dev)
                self._dio.deactivate()  # Make sure lines are turned off upon opening; due to fact that sometimes when the DAQ is first powered on, all lines will be open
                self.btn_open.SetLabel('Close')
                self.btn_activate.Enable(True)
            except AttributeError:
                wx.MessageBox('Line Could Not be Opened; it is Already in Use', 'Error', wx.OK | wx.ICON_ERROR)
                return
        else:
            self._dio.deactivate()
            self._dio.close()
            self.btn_open.SetLabel('Open')
            self.btn_activate.SetLabel('Activate')
            self.btn_activate.Enable(False)

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
        print(f'Pulsing for {ms} ms')
        self._dio.pulse(ms)

    def OnSaveConfig(self, evt):
         section = LP_CFG.get_hwcfg_section(self._name)
         section['Device'] = self.choice_dev.GetStringSelection()
         section['Port'] = self.choice_port.GetStringSelection()
         section['Line'] = self.choice_line.GetStringSelection()
         section['Active High'] = str(self.radio_active_sel.GetSelection() == 0)
         section['Read Only'] = str(self.check_read_only.GetValue())
         LP_CFG.update_hwcfg_section(self._name, section)

    def OnLoadConfig(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        self._dio.deactivate()  # If a config is loaded in on when a DIO channel is already open, close this channel
        self._dio.close()
        self.btn_open.SetLabel('Open')
        self.btn_activate.SetLabel('Activate')
        self.btn_activate.Enable(False)
        self.choice_dev.SetStringSelection(section['Device'])
        self.choice_port.SetStringSelection(section['Port'])
        self.choice_line.SetStringSelection(section['Line'])
        active_high_state = (section['Active High'] != 'True')
        self.radio_active_sel.SetSelection(active_high_state)
        read_only_state = (section['Read Only'] == 'True')
        self.check_read_only.SetValue(read_only_state)

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
    app = MyTestApp(0)
    app.MainLoop()
