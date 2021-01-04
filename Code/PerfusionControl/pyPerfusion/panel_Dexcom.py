# -*- coding: utf-8 -*-
"""

@author: Allen Luna

Panel class for testing and configuring Dexcom G6 Receiver/Sensor pair
"""
import wx
import pyPerfusion.PerfusionConfig as LP_CFG
from dexcom_G6_reader import readdata

CIRCUIT_LIST = [f'Hepatic Artery', f'Portal Vein', f'Inferior Vena Cava']

class PanelDexcom(wx.Panel):
    def __init__(self, parent, receiver, name='Receiver'):
        self.parent = parent
        self._receiver = receiver
        self._name = name
        wx.Panel.__init__(self, parent, -1)

        LP_CFG.set_base()
        self._avail_circuit = CIRCUIT_LIST

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_circuit = wx.StaticText(self, label='Perfusion Circuit')
        self.choice_circuit = wx.Choice(self, wx.ID_ANY, choices=self._avail_circuit)
        self.choice_circuit.SetSelection(0)

        self.label_serial = wx.StaticText(self, label='Receiver Serial Number')
        self.choice_serial = wx.Choice(self, choices=[])  # Choices = list of receiver SN from database
        # Tie in serial number display with line selection and vise versa; if one updates, so does the other

        self.btn_dl_info = wx.Button(self, label='Download Receiver Info')
        self.btn_dl_info.Enable(True)
        # Make this download serial number/line pairs for the three Dexcom receivers; should be first thing you do

        self.btn_connect = wx.Button(self, label='Connect to Receiver')
        self.btn_connect.Enable(False)
        # Once pairs are downloaded and line is choosen,enable; then, connect to the correct receiver of the three possible

        self.btn_start = wx.ToggleButton(self, label='Start Data Acquisition')

        self.btn_latest = wx.Button(self, label='Display Latest Glucose Value')

        self.btn_save = wx.Button(self, label='Save Config')
        self.btn_load = wx.Button(self, label='Load Config')

       # self.load_info()

        self.__do_layout()
       # self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 2).Center().Proportion(1)

        self.sizer_circuit = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_circuit.Add(self.label_circuit, flags)
        self.sizer_circuit.Add(self.choice_circuit, flags)

        self.sizer_serial = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_serial.Add(self.label_serial, flags)
        self.sizer_serial.Add(self.choice_serial, flags)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sizer_circuit)
        sizer.AddSpacer(10)
        sizer.Add(self.sizer_serial)
        sizer.AddSpacer(20)
        sizer.Add(self.btn_dl_info, flags)
        self.sizer.Add(sizer)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_connect)
        sizer.Add(self.btn_start)
        sizer.Add(self.btn_latest)
        self.sizer.AddSpacer(5)
        self.sizer.Add(sizer)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        receivers = {'Receiver #1': readdata,
                     'Receiver #2': readdata,
                     'Receiver #3': readdata
                     }
        sizer = wx.GridSizer(cols=1)
        for key, receiver in receivers.items():
            sizer.Add(PanelDexcom(self, receiver, name=key), 1, wx.EXPAND, border=2)
        self.SetSizer(sizer)
        self.Fit()
        self.Layout()

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    app = MyTestApp(0)
    app.MainLoop()
