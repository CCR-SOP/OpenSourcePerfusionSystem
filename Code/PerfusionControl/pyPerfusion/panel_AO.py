# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for testing and configuring AIO
"""
import wx
from pyHardware.pyAO_NIDAQ import NIDAQ_AO

DEV_LIST = ['Dev1', 'Dev2', 'Dev3', 'Dev4', 'Dev5']
LINE_LIST = [f'{line}' for line in range(0, 9)]


class PanelAO(wx.Panel):
    def __init__(self, parent, aio):
        self.parent = parent
        self._ao = aio
        wx.Panel.__init__(self, parent, -1)

        self._avail_dev = DEV_LIST
        self._avail_lines = LINE_LIST

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.label_dev = wx.StaticText(self, label='NI Device Name')
        self.choice_dev = wx.Choice(self, wx.ID_ANY, choices=self._avail_dev)

        self.label_line = wx.StaticText(self, label='Line Number')
        self.choice_line = wx.Choice(self, wx.ID_ANY, choices=self._avail_lines)

        self.btn_open = wx.ToggleButton(self, label='Open')
        self.btn_volts = wx.Button(self, label='Update')
        self.spin_volts = wx.SpinCtrlDouble(self, min=0, max=5, initial=2.5)
        self.lbl_volts = wx.StaticText(self, label='Volts')

        self.check_sine = wx.CheckBox(self, label='Sine output')
        self.spin_pk2pk = wx.SpinCtrlDouble(self, min=0.0, max=5.0, initial=2.5, inc=0.1)
        self.lbl_pk2pk = wx.StaticText(self, label='Pk-Pk Voltage', style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.spin_offset = wx.SpinCtrlDouble(self, min=0.0, max=5.0, initial=2.5, inc=0.1)
        self.lbl_offset = wx.StaticText(self, label='Offset Voltage', style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.spin_hz = wx.SpinCtrlDouble(self, min=0.0, max=1000.0, initial=1.0)
        self.lbl_hz = wx.StaticText(self, label='Hz', style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.spin_hz.Digits = 3
        self.spin_offset.Digits = 3
        self.spin_pk2pk.Digits = 3

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        self.sizer_dev = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_dev.Add(self.label_dev)
        self.sizer_dev.Add(self.choice_dev)

        self.sizer_line = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_line.Add(self.label_line)
        self.sizer_line.Add(self.choice_line)

        self.sizer_volts = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_volts.Add(self.spin_volts)
        self.sizer_volts.Add(self.lbl_volts)
        self.sizer_volts.Add(self.btn_volts)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sizer_dev)
        sizer.Add(self.sizer_line)
        self.sizer.Add(sizer)

        self.sizer.AddSpacer(10)

        self.sizer.Add(self.btn_open)
        self.sizer.Add(self.sizer_volts)

        self.sizer.AddSpacer(20)

        self.sizer.Add(self.check_sine)
        self.sizer.AddSpacer(10)
        self.sizer_sine = wx.GridSizer(cols=3, hgap=5, vgap=2)
        self.sizer_sine.Add(self.lbl_pk2pk, 2, wx.EXPAND)
        self.sizer_sine.Add(self.lbl_offset, 1, wx.EXPAND)
        self.sizer_sine.Add(self.lbl_hz, 1, wx.EXPAND)

        self.sizer_sine.Add(self.spin_pk2pk, 2, wx.EXPAND)
        self.sizer_sine.Add(self.spin_offset, 1, wx.EXPAND)
        self.sizer_sine.Add(self.spin_hz, 1, wx.EXPAND)

        self.sizer.Add(self.sizer_sine)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_open.Bind(wx.EVT_TOGGLEBUTTON, self.OnOpen)
        self.btn_volts.Bind(wx.EVT_BUTTON, self.OnVolts)

    def OnOpen(self, evt):
        state = self.btn_open.GetValue()
        if state:
            dev = self.choice_dev.GetStringSelection()
            line = self.choice_line.GetStringSelection()
            print(f'dev is {dev}, line is {line}')
            self._ao.open(line, period_ms=10, volt_range=[0, 5], dev=dev)
            self.btn_open.SetLabel('Close',)
        else:
            self._ao.close()
            self.btn_open.SetLabel('Open')

    def OnVolts(self, evt):
        volts = self.spin_volts.GetValue()
        print(f'Updating for {volts} volts')
        self._ao.set_voltage(volts)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.ao = NIDAQ_AO()
        self.panel = PanelAO(self, self.ao)


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    app = MyTestApp(0)
    app.MainLoop()
