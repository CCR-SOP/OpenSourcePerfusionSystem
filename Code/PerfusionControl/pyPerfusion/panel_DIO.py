# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for testing and configuring DIO
"""
import wx

DEV_LIST = ['Dev1', 'Dev2', 'Dev3', 'Dev4', 'Dev5']
PORT_LIST = ['0', '1', '2', '3', '4']
LINE_LIST = ['0', '1', '2', '3', '4', '5', '6', '7', '8']

class PanelDIO(wx.Panel):
    def __init__(self, parent):
        self.parent = parent
        wx.Panel.__init__(self, parent, -1)

        self._avail_dev = DEV_LIST
        self._avail_ports = PORT_LIST
        self._avail_lines = LINE_LIST

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.label_dev = wx.StaticText(self, label='NI Device Name')
        self.choice_dev = wx.Choice(self, wx.ID_ANY, choices=self._avail_dev)

        self.label_port = wx.StaticText(self, label='Port Number')
        self.choice_port = wx.Choice(self, wx.ID_ANY, choices=self._avail_ports)

        self.label_line = wx.StaticText(self, label='Line Number')
        self.choice_line = wx.Choice(self, wx.ID_ANY, choices=self._avail_lines)

        self.radio_active_high = wx.RadioButton(self, label='Active High', style=wx.RB_GROUP)
        self.radio_active_low = wx.RadioButton(self, label='Active Low')

        self.check_read_only = wx.CheckBox(self, label='Read Only')

        self.btn_open = wx.ToggleButton(self, label='Open')
        self.btn_activate = wx.ToggleButton(self, label='Activate')
        self.btn_pulse = wx.Button(self, label='Pulse')
        self.spin_pulse = wx.SpinCtrl(self, min=1, max=20000, initial=10)
        self.lbl_pulse = wx.StaticText(self, label='ms')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        self.sizer_dev = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_dev.Add(self.label_dev)
        self.sizer_dev.Add(self.choice_dev)

        self.sizer_port = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_port.Add(self.label_port)
        self.sizer_port.Add(self.choice_port)

        self.sizer_line = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_line.Add(self.label_line)
        self.sizer_line.Add(self.choice_line)

        self.sizer_active = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_active.Add(self.radio_active_high)
        self.sizer_active.Add(self.radio_active_low)

        self.sizer_pulse = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_pulse.Add(self.spin_pulse)
        self.sizer_pulse.Add(self.lbl_pulse)
        self.sizer_pulse.Add(self.btn_pulse)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sizer_dev)
        sizer.Add(self.sizer_port)
        sizer.Add(self.sizer_line)
        self.sizer.Add(sizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer_active)
        sizer.Add(self.check_read_only)
        self.sizer.Add(sizer)

        self.sizer.AddSpacer(10)

        self.sizer.Add(self.btn_open)
        self.sizer.Add(self.btn_activate)
        self.sizer.Add(self.sizer_pulse)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_open.Bind(wx.EVT_TOGGLEBUTTON, self.OnOpen)
        self.btn_activate.Bind(wx.EVT_TOGGLEBUTTON, self.OnActivate)
        self.btn_pulse.Bind(wx.EVT_BUTTON, self.OnPulse)

    def OnOpen(self, evt):
        state = self.btn_open.GetValue()
        if state:
            self.btn_open.SetLabel('Close')
        else:
            self.btn_open.SetLabel('Open')

    def OnActivate(self, evt):
        state = self.btn_activate.GetValue()
        if state:
            self.btn_activate.SetLabel('Deactivate')
        else:
            self.btn_activate.SetLabel('Activate')

    def OnPulse(self, evt):
        ms = self.spin_pulse.GetValue()
        print(f'Pulsing for {ms} ms')


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelDIO(self)


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    app = MyTestApp(0)
    app.MainLoop()
