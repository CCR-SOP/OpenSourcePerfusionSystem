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
    def __init__(self, parent, aio, name):
        self.parent = parent
        self._ao = aio
        self._name = name
        wx.Panel.__init__(self, parent, -1)

        self._avail_dev = DEV_LIST
        self._avail_lines = LINE_LIST

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)
        self.label_dev = wx.StaticText(self, label='NI Device Name')
        self.choice_dev = wx.Choice(self, wx.ID_ANY, choices=self._avail_dev)

        self.label_line = wx.StaticText(self, label='Line Number')
        self.choice_line = wx.Choice(self, wx.ID_ANY, choices=self._avail_lines)

        self.btn_open = wx.ToggleButton(self, label='Open')
        self.btn_update = wx.Button(self, label='Update')

        self.check_sine = wx.CheckBox(self, label='Sine output')
        self.spin_pk2pk = wx.SpinCtrlDouble(self, min=0.0, max=5.0, initial=2.5, inc=0.1)
        self.lbl_pk2pk = wx.StaticText(self, label='Pk-Pk Voltage')
        self.spin_offset = wx.SpinCtrlDouble(self, min=0.0, max=5.0, initial=2.5, inc=0.1)
        self.lbl_offset = wx.StaticText(self, label='Offset Voltage')
        self.spin_hz = wx.SpinCtrlDouble(self, min=0.0, max=1000.0, initial=1.0)
        self.lbl_hz = wx.StaticText(self, label='Hz')
        self.spin_hz.Digits = 3
        self.spin_offset.Digits = 3
        self.spin_pk2pk.Digits = 3

        self.OnSine(wx.EVT_CHECKBOX)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center().Proportion(0)
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
        sizer.AddSpacer(20)
        sizer.Add(self.btn_open, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(10)

        self.sizer.AddSpacer(20)

        self.sizer.Add(self.check_sine)
        self.sizer.AddSpacer(10)
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
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.btn_update, flags)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_open.Bind(wx.EVT_TOGGLEBUTTON, self.OnOpen)
        self.btn_update.Bind(wx.EVT_BUTTON, self.OnUpdate)
        self.check_sine.Bind(wx.EVT_CHECKBOX, self.OnSine)

    def OnOpen(self, evt):
        state = self.btn_open.GetValue()
        if state:
            dev = self.choice_dev.GetStringSelection()
            line = self.choice_line.GetStringSelection()
            print(f'dev is {dev}, line is {line}')
            self._ao.open(line, period_ms=10, dev=dev)
            self.btn_open.SetLabel('Close',)
            self._ao.start()
        else:
            self._ao.close()
            self.btn_open.SetLabel('Open')

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

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.ao = NIDAQ_AO()
        self.panel = PanelAO(self, self.ao, name='Analog Output')


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    app = MyTestApp(0)
    app.MainLoop()
