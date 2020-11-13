# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for testing and configuring Elite 11 Syringe Pump
"""
import wx
from pyHardware.PHDserial import PHDserial

COMM_LIST = [f'COM{num}' for num in range(1,10)]
BAUD_LIST = ['9600', '115200']


class PanelSyringe(wx.Panel):
    def __init__(self, parent, syringe):
        self.parent = parent
        self._syringe = syringe
        wx.Panel.__init__(self, parent, -1)

        self._avail_comm = COMM_LIST
        self._avail_baud = BAUD_LIST

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.label_comm = wx.StaticText(self, label='USB COMM')
        self.choice_comm = wx.Choice(self, wx.ID_ANY, choices=self._avail_comm)

        self.label_baud = wx.StaticText(self, label='Baud Rate')
        self.choice_baud = wx.Choice(self, wx.ID_ANY, choices=self._avail_baud)
        self.choice_baud.SetSelection(2)

        self.btn_open = wx.ToggleButton(self, label='Open')

        self.label_manu = wx.StaticText(self, label='Manufacturer')
        self.choice_manu = wx.Choice(self, choices=self._manufacturers)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center().Proportion(0)

        self.sizer_comm = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_comm.Add(self.label_comm, flags)
        self.sizer_comm.Add(self.choice_comm, flags)

        self.sizer_baud = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_baud.Add(self.label_baud, flags)
        self.sizer_baud.Add(self.choice_baud, flags)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sizer_comm)
        sizer.AddSpacer(10)
        sizer.Add(self.sizer_baud)
        sizer.AddSpacer(20)
        sizer.Add(self.btn_open, flags)

        self.sizer.Add(sizer)
        self.sizer.AddSpacer(10)


        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_open.Bind(wx.EVT_TOGGLEBUTTON, self.OnOpen)

    def OnOpen(self, evt):
        state = self.btn_open.GetValue()
        if state:
            comm = self.choice_comm.GetStringSelection()
            baud = self.choice_baud.GetStringSelection()
            self._syringe.open(comm, int(baud))
            self.btn_open.SetLabel('Close',)
        else:
            self._syringe.close()
            self.btn_open.SetLabel('Open')


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.syringe = PHDserial()
        self.panel = PanelSyringe(self, self.syringe)


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    app = MyTestApp(0)
    app.MainLoop()
