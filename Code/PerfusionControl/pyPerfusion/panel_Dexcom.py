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
        self._circuits = None
        self._serials = None
        wx.Panel.__init__(self, parent, -1)

        LP_CFG.set_base()
        self._avail_circuit = CIRCUIT_LIST

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_circuit = wx.StaticText(self, label='Circuit')
        self.choice_circuit = wx.Choice(self, wx.ID_ANY, choices=self._avail_circuit)
        self.choice_circuit.SetSelection(0)

        self.label_serial = wx.StaticText(self, label='Receiver SN')
        self.choice_serial = wx.Choice(self, choices=[])

        self.btn_dl_info = wx.Button(self, label='Download Receiver Info')

        self.btn_save = wx.Button(self, label='Save Config')
        self.btn_load = wx.Button(self, label='Load Config')

        self.btn_connect = wx.Button(self, label='Connect to Receiver')
        self.btn_connect.Enable(False)

        self.btn_start = wx.ToggleButton(self, label='Start Acquisition')

        self.label_latest = wx.StaticText(self, label='Latest Glucose Value')
        self.display_latest = wx.TextCtrl(self)

        self.load_info()

        self.__do_layout()
        self.__set_bindings()

    def load_info(self):
        circuits, serials = LP_CFG.open_receiver_info()
        self._circuits = circuits
        self._serials = serials
        self.update_available_receivers()

    def update_available_receivers(self):
        self.choice_circuit.Clear()
        self.choice_serial.Clear()
        circuit_str = [f'({code}) {desc}' for code, desc in manu.items()]
        serial_str = [f'({code}) {desc}' for code, desc in manu.items()]

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 2).Center().Proportion(1)

        self.sizer_circuit = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_circuit.Add(self.label_circuit, flags)
        self.sizer_circuit.Add(self.choice_circuit, flags)

        self.sizer_serial = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_serial.Add(self.label_serial, flags)
        self.sizer_serial.Add(self.choice_serial, flags)

        self.sizer_latest = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_latest.Add(self.label_latest, flags)
        self.sizer_latest.Add(self.display_latest, flags)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sizer_circuit)
        sizer.AddSpacer(10)
        sizer.Add(self.sizer_serial)
        self.sizer.Add(sizer)

        self.sizer.AddSpacer(10)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_dl_info, flags)
        sizer.AddSpacer(10)
        sizer.Add(self.btn_save)
        sizer.AddSpacer(10)
        sizer.Add(self.btn_load)
        self.sizer.Add(sizer)

        self.sizer.AddSpacer(10)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_connect)
        sizer.AddSpacer(10)
        sizer.Add(self.btn_start)
        self.sizer.Add(sizer)

        self.sizer.AddSpacer(10)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sizer_latest)
        self.sizer.Add(sizer)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.choice_circuit.Bind(wx.EVT_CHOICE, self.OnCircuit)
        self.choice_serial.Bind(wx.EVT_CHOICE, self.OnSerial)
        self.btn_dl_info.Bind(wx.EVT_BUTTON, self.OnDLInfo)
        self.btn_save.Bind(wx.EVT_BUTTON, self.OnSaveConfig)
        self.btn_load.Bind(wx.EVT_BUTTON, self.OnLoadConfig)
        self.btn_connect.Bind(wx.EVT_BUTTON, self.OnConnect)
        self.btn_start.Bind(wx.EVT_TOGGLEBUTTON, self.OnStart)

    def OnCircuit(self, evt):
        circuit = self.choice_circuit.GetString(self.choice_circuit.GetSelection())


    def OnConnect(self, evt):
        serial_number = self.

# Choices = list of receiver SN from database
# Tie in serial number display with line selection and vise versa; if one updates, so does the
# Once pairs are downloaded and line is choosen, enable "connect"; then, connect to the correct receiver of the three possible
# Make this download serial number/line pairs for the three Dexcom receivers; should be first thing you do
# Add graph that plots RT data from sensor once data acquisition is activated
# Fix way that the latest glucose value is displayed
# Add "open_receiver_info" method to PerfusionConfig

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        receivers = {'Receiver #1': readdata,
                     'Receiver #2': readdata,
                     'Receiver #3': readdata
                     }
        sizer = wx.GridSizer(cols=3)
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
