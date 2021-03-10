# -*- coding: utf-8 -*-
"""

@author: Allen Luna

Panel class for testing and configuring Dexcom G6 Receiver/Sensor pair, and for initiating glucose controlled insulin/glucagon infusions
"""
import wx

from dexcom_G6_reader.readdata import Dexcom

import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.panel_plotting import PanelPlotting, PanelPlotLT
from pyPerfusion.DexcomStream import DexcomStream

engaged_COM_list = []
sensors = []

class PanelDexcom(wx.Panel):
    def __init__(self, parent, receiver_class, name):
        self.parent = parent
        self._receiver_class = receiver_class
        self._name = name
        self._connected_receiver = None

        wx.Panel.__init__(self, parent, -1)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer_main = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_circuit_SN_pair = wx.StaticText(self, label='Dexcom Receiver')
        self.choice_circuit_SN_pair = wx.StaticText(self, label='')

        self.label_connect = wx.StaticText(self, label='')

        self.btn_start = wx.Button(self, label='Start Acquisition')
        self.btn_start.Enable(False)

        self.set_receiver()

        self.sensor = DexcomStream(self._name[14:] + ' Glucose', 'mg/dL', self._connected_receiver, valid_range=[80, 110])
        sensors.append(self.sensor)

        self.sizer_plot = wx.BoxSizer(wx.VERTICAL)
        self._panel_plot = PanelPlotting(self)
        self._panel_plot.add_sensor(self.sensor)
        self.sizer_plot.Add(self._panel_plot, 6, wx.ALL | wx.EXPAND, border=0)
        self._sub_panel = PanelPlotLT(self)
        self._sub_panel.plot_frame_ms = 20000
        self._sub_panel.add_sensor(self.sensor)
        self.sizer_plot.Add(self._sub_panel, 1, wx.ALL | wx.EXPAND, border=0)

        self.__do_layout()
        self.__set_bindings()

        LP_CFG.update_stream_folder()
        self.sensor.open(LP_CFG.LP_PATH['stream'])
        self.sensor.start()

    def set_receiver(self):
        receiver_info = LP_CFG.open_receiver_info()
        for key, val in receiver_info.items():
            if key in self._name.lower():
                self.choice_circuit_SN_pair.SetLabel('%s (SN = %s)' % (key, val))
        receiver_choice = self.choice_circuit_SN_pair.GetLabel()
        SN_choice = receiver_choice[-11:-1]
        COM_ports = self._receiver_class.FindDevices()
        for COM in COM_ports:
            if not (COM in engaged_COM_list):
                potential_receiver = self._receiver_class(COM)
                potential_SN = potential_receiver.ReadManufacturingData().get('SerialNumber')
                if potential_SN == SN_choice:
                    potential_receiver.Disconnect()
                    self._connected_receiver = self._receiver_class(COM)
                    engaged_COM_list.append(COM)
                    self.label_connect.SetLabel('Connected to %s' % COM)
                    self.btn_start.Enable(True)
                    return
                else:
                    potential_receiver.Disconnect()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 2).Center().Proportion(1)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_circuit_SN_pair, flags)
        sizer.Add(self.choice_circuit_SN_pair, flags)
        self.sizer_main.Add(sizer)

        self.sizer_main.AddSpacer(10)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_connect, flags)
        sizer.AddSpacer(30)
        sizer.Add(self.btn_start, flags)
        self.sizer_main.Add(sizer)

        self.sizer_plot_grid = wx.GridSizer(cols=2, hgap=5, vgap=5)
        self.sizer_plot_grid.Add(self.sizer_plot, 1, wx.ALL | wx.EXPAND)
        self.sizer_main.Add(self.sizer_plot_grid, 1, wx.ALL | wx.EXPAND)

        self.SetSizer(self.sizer_main)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_start.Bind(wx.EVT_BUTTON, self.OnStart)

    def OnStart(self, evt):
        state = self.btn_start.GetLabel()
        if state == 'Start Acquisition':
            self.sensor.hw.read_data = True
            self.btn_start.SetLabel('Stop Acquisition')
        else:
            self.sensor.hw.read_data = False
            self.btn_start.SetLabel('Start Acquisition')

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        devices = {'Receiver #1 - Hepatic Artery': Dexcom,
                  # 'Receiver #2 - Portal Vein': Dexcom,
                  # 'Receiver #3 - Inferior Vena Cava': Dexcom
                   }
        sizer = wx.GridSizer(cols=1)
        for key, device in devices.items():
            sizer.Add(PanelDexcom(self, device, name=key), 1, wx.EXPAND, border=2)
        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for sensor in sensors:
            sensor.stop()
        self.Destroy()

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True

if __name__ == "__main__":
    LP_CFG.set_base(basepath='~/Documents/LPTEST')
    LP_CFG.update_stream_folder()
    app = MyTestApp(0)
    app.MainLoop()
