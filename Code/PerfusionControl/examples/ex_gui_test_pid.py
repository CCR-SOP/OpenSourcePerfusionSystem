# -*- coding: utf-8 -*-
""" Example to test PID

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import wx

from simple_pid import PID


class PanelPID(wx.Panel):
    def __init__(self, parent):
        self.parent = parent
        wx.Panel.__init__(self, parent)
        self._pid = None

        self.label_p = wx.StaticText(self, label='Proportional')
        self.spin_p = wx.SpinCtrlDouble(self, min=0, max=100, initial=10, inc=0.001)
        self.spin_p.Digits = 3

        self.label_i = wx.StaticText(self, label='Integral')
        self.spin_i = wx.SpinCtrlDouble(self, min=0, max=100, initial=10, inc=0.001)
        self.spin_i.Digits = 3

        self.label_d = wx.StaticText(self, label='Derivative')
        self.spin_d = wx.SpinCtrlDouble(self, min=0, max=100, initial=10, inc=0.001)
        self.spin_d.Digits = 3

        self.updateBtn = wx.Button(self, id=wx.ID_ANY, label="Update")

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Proportion(0)

        sizer_pid = wx.GridSizer(cols=4, hgap=5, vgap=3)
        sizer_pid.AddMany([
            (self.label_p, flags),
            (self.label_i, flags),
            (self.label_d, flags),
            (self.updateBtn, flags),  # ideally this is centered
            (self.spin_p, flags),
            (self.spin_i, flags),
            (self.spin_d, flags)
        ])
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(sizer_pid, wx.ALL, border=10)
        self.SetSizer(sizer)

        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.updateBtn.Bind(wx.EVT_BUTTON, self.on_update_pid)

    def on_update_pid(self, evt):
        p = self.spin_p.GetValue()
        i = self.spin_i.GetValue()
        d = self.spin_d.GetValue()
        self._pid.tunings = (p, i, d)

    def set_pid(self, pid):
        self._pid = pid
        self.update_controls()

    def update_controls(self):
        if self._pid:
            p, i, d = self._pid.components
            self.spin_p.SetValue(p)
            self.spin_i.SetValue(i)
            self.spin_d.SetValue(d)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelPID(self)
        self.pid = PID()
        self.panel.set_pid(self.pid)


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    app = MyTestApp(0)
    app.MainLoop()
