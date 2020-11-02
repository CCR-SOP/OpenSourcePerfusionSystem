# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for testing and configuring AIO
"""
import wx
from pyHardware.pyAO_NIDAQ import NIDAQ_AO

DEV_LIST = ['Dev1', 'Dev2', 'Dev3', 'Dev4', 'Dev5']
LINE_LIST = [f'{line}' for line in range(0, 9)]


class PanelAIO(wx.Panel):
    def __init__(self, parent, aio):
        self.parent = parent
        self._aio = aio
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
            self._aio.open(line, period_ms=10, volt_range=[0, 5], dev=dev)
            self.btn_open.SetLabel('Close',)
        else:
            self._aio.close()
            self.btn_open.SetLabel('Open')

    def OnVolts(self, evt):
        volts = self.spin_volts.GetValue()
        print(f'Updating for {volts} volts')
        self._aio.set_voltage(volts)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.aio = NIDAQ_AO()
        self.panel = PanelAIO(self, self.aio)


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    app = MyTestApp(0)
    app.MainLoop()
