# -*- coding: utf-8 -*-
"""

@author: Allen Luna

Panel class for testing and configuring Dexcom G6 Receiver/Sensor pair
"""
import wx
import pyPerfusion.PerfusionConfig as LP_CFG
from dexcom_G6_reader import readdata

class PanelDexcom(wx.Panel):
    def __init__(self, parent, receiver, name='Receiver'):
        self.parent = parent
        self._receiver = receiver
        self._name = name
        self._circuit_SN_pairs = []
        wx.Panel.__init__(self, parent, -1)

        LP_CFG.set_base()

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_circuit_SN_pair = wx.StaticText(self, label='Dexcom Receiver')
        self.choice_circuit_SN_pair = wx.Choice(self, wx.ID_ANY, choices=[])

        self.btn_dl_info = wx.Button(self, label='Download Receiver Info')

        self.btn_save = wx.Button(self, label='Save Config')
        self.btn_load = wx.Button(self, label='Load Config')

        self.btn_connect = wx.Button(self, label='Connect to Receiver')
        self.btn_connect.Enable(False)

        self.btn_start = wx.ToggleButton(self, label='Start Acquisition')
        self.btn_start.Enable(False)

        self.label_latest = wx.StaticText(self, label='Latest Glucose Value')
        self.display_latest = wx.TextCtrl(self)

        self.load_info()
        self.__do_layout()
        self.__set_bindings()

    def load_info(self):
        receiver_info = LP_CFG.open_receiver_info()
        self._circuit_SN_pairs.clear()
        for key, val in receiver_info.items():
            self._circuit_SN_pairs.append('%s (SN = %s)' % (key, val))
        self.update_receiver_choices()

    def update_receiver_choices(self):
        self.choice_circuit_SN_pair.Clear()
        pairs = self._circuit_SN_pairs
        if not pairs:
            pairs = ['Perfusion Circuit (SN = 123456789)']
        self.choice_circuit_SN_pair.Append(pairs)

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 2).Center().Proportion(1)

        self.sizer_circuit_SN_pair = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_circuit_SN_pair.Add(self.label_circuit_SN_pair, flags)
        self.sizer_circuit_SN_pair.Add(self.choice_circuit_SN_pair, flags)

        self.sizer_latest = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_latest.Add(self.label_latest, flags)
        self.sizer_latest.Add(self.display_latest, flags)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sizer_circuit_SN_pair)
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
        self.choice_circuit_SN_pair.Bind(wx.EVT_CHOICE, self.OnCircuitSN)
        self.btn_dl_info.Bind(wx.EVT_BUTTON, self.OnDLInfo)
        #self.btn_save.Bind(wx.EVT_BUTTON, self.OnSaveConfig)
        #self.btn_load.Bind(wx.EVT_BUTTON, self.OnLoadConfig)
        #self.btn_connect.Bind(wx.EVT_BUTTON, self.OnConnect)
        #self.btn_start.Bind(wx.EVT_TOGGLEBUTTON, self.OnStart)

    def OnCircuitSN(self, evt):
        self.btn_connect.Enable(True)
    #    circuit = self.choice_circuit.GetString(self.choice_circuit.GetSelection())

    def OnDLInfo(self, evt):
        self.load_info()


  #  def OnConnect(self, evt):
   #     circuit = self.choice_circuit.GetString(self.choice_circuit.GetSelection())

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
