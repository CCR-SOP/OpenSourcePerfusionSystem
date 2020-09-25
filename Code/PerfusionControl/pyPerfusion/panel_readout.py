# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for showing single number readout
"""
import wx


class PanelReadout(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self._sensors = []

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer_value = wx.BoxSizer(wx.HORIZONTAL)
        self.label_name = wx.StaticText(self, label='HA Flow')
        self.label_value = wx.StaticText(self, label='65')
        self.label_units = wx.StaticText(self, label='bpm')

        self.__do_layout()
        # self.__set_bindings()

    def __do_layout(self):

        font = self.label_name.GetFont()
        font.SetPointSize(16)
        self.label_name.SetFont(font)
        font = self.label_value.GetFont()
        font.SetPointSize(20)
        self.label_value.SetFont(font)

        self.sizer.Add(self.label_name, wx.SizerFlags().CenterHorizontal())
        self.sizer_value.Add(self.label_value, wx.SizerFlags().CenterVertical())
        self.sizer_value.AddSpacer(10)
        self.sizer_value.Add(self.label_units, wx.SizerFlags().CenterVertical())
        self.sizer.Add(self.sizer_value, wx.SizerFlags().CenterHorizontal())

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()


    # def __set_bindings(self):
        # add bindings, if needed


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelReadout(self)


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    app = MyTestApp(0)
    app.MainLoop()
