# -*- coding: utf-8 -*-
"""

@author: Allen Luna

Panel class for testing and configuring Dexcom G6 Receiver/Sensor pair, and for initiating glucose controlled insulin/glucagon infusions
"""
import wx
import matplotlib as mpl
import numpy as np

from dexcom_G6_reader.readdata import Dexcom

import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.panel_plotting import PanelPlotting

engaged_COM_list = []
mpl.rcParams.update({'font.size': 6})

class GraphingDexcom(PanelPlotting):
    def __init__(self, parent, with_readout=True):
        super().__init__(parent, with_readout)
        self._valid_range = [80, 110]
        self._CGM = None
        self._time = None
        self.dexcom_receiver = None
        self.__val_display = None

        self.timer_plot.Start(1000, wx.TIMER_CONTINUOUS)
        self.timer_plot.Stop()

    def add_Dexcom(self):
        self.__val_display = self.axes.text(1.06, 0.5, '0', transform=self.axes.transAxes, fontsize=18, ha='center')
        self.axes.text(1.06, 0.4, 'mg/dL', transform=self.axes.transAxes, fontsize=8, ha='center')
        rng = self._valid_range
        self._shaded['normal'] = self.axes.axhspan(rng[0], rng[1], color='g', alpha=0.2)
        self._configure_dexcom_plot()

    def _configure_dexcom_plot(self):
        self.axes.set_title('Glucose Concentration (mg/dL)')
        self.axes.set_ylabel('mg/dL')
        self.axes.set_xlabel('No Sensor Connected')

    def OnTimer(self, event):
        if event.GetId() == self.timer_plot.GetId():
            self._time, latest_read = self.dexcom_receiver.get_latest_CGM()
            if (self._time is None) and (latest_read is None):  # Sensor is dead; end of run
                self._CGM = None
            if (latest_read == 'ABSOLUTE_DEVIATION') or (latest_read == 'POWER_DEVIATION') or (latest_read == 'COUNTS_DEVIATION'):
                self.axes.set_xlabel(latest_read + ' : See Receiver')
                self._CGM = 0
            elif latest_read[0:3] == 'CGM':
                self.axes.set_xlabel('Sensor Active')
                self._CGM = int(latest_read.split('BG:')[1].split(' (')[0])
            else:
                self.axes.set_xlabel('Unknown Error : See Receiver')
                self._CGM = 0

            self.plot()

    def plot(self):
        if self._CGM is None:
            self.EndofRun()
            return
        if self._CGM == 0:
            self.axes.plot_date(self._time, self._CGM, color='white', marker='o', xdate=True)
            self.__val_display.set_text('N/A')
            color = 'black'
        elif self._CGM > self._valid_range[1]:
            self.axes.plot_date(self._time, self._CGM, color='red', marker='o', xdate=True)
            self.__val_display.set_text(f'{self._CGM:.0f}')
            color = 'red'
        elif self._CGM < self._valid_range[0]:
            self.axes.plot_date(self._time, self._CGM, color='orange', marker='o', xdate=True)
            self.__val_display.set_text(f'{self._CGM:.0f}')
            color = 'orange'
        else:
            self.axes.plot_date(self._time, self._CGM, color='black', marker='o', xdate=True)
            self.__val_display.set_text(f'{self._CGM:.0f}')
            color = 'black'

        self.__val_display.set_color(color)

        self.axes.relim()

        labels = self.axes.get_xticklabels()
        if len(labels) >= 12:
            self.axes.set_xlim(left=labels[-12].get_text(), right=self._time)
        self.axes.autoscale_view()
        self.canvas.draw()

    def EndofRun(self):
        self.axes.set_xlabel('End of Sensor Run: Replace Sensor Now!')
        for value in np.linspace(0, self._valid_range[1], 100):
            self.axes.plot_date(self._time, value, color='red', marker='x', xdate=True)
        self.__val_display.set_text('End of Run')
        self.__val_display.set_color('Red')
        self.axes.relim()
        labels = self.axes.get_xticklabels()
        if len(labels) >= 12:
            self.axes.set_xlim(left=labels[-12].get_text(), right=self._time)
        self.axes.autoscale_view()
        self.canvas.draw()

        self.timer_plot.Stop()
        self.dexcom_receiver.Disconnect()
        self.dexcom_receiver = None
        self._time = None
        self._CGM = None
        wx.MessageBox('Sensor Run has Ended; Please Disconnect Receiver and Begin a New Sensor Session', 'Error', wx.OK | wx.ICON_ERROR)

class PanelDexcom(wx.Panel):
    def __init__(self, parent, receiver, name):
        self.parent = parent
        self._receiver = receiver
        self._name = name
        self._circuit_SN_pairs = []

        wx.Panel.__init__(self, parent, -1)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_circuit_SN_pair = wx.StaticText(self, label='Dexcom Receiver')
        self.choice_circuit_SN_pair = wx.Choice(self, wx.ID_ANY, choices=[])

        self.btn_dl_info = wx.Button(self, label='Download Receiver Info')

        self.btn_connect = wx.Button(self, label='Connect to Receiver xxxxxxxxxx / COMX')
        self.btn_connect.Enable(False)

        self.btn_start = wx.Button(self, label='Start Acquisition')
        self.btn_start.Enable(False)

        self._panel_plot = GraphingDexcom(self)
        self._panel_plot.add_Dexcom()

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
            pairs = ['Perfusion Circuit (SN = 0123456789)']
        self.choice_circuit_SN_pair.Append(pairs)

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 2).Center().Proportion(1)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_circuit_SN_pair, flags)
        sizer.Add(self.choice_circuit_SN_pair, flags)
        self.sizer.Add(sizer)

        self.sizer.AddSpacer(10)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_dl_info, flags)
        sizer.AddSpacer(10)
        sizer.Add(self.btn_connect, flags)
        self.sizer.Add(sizer)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_start, flags)
        self.sizer.Add(sizer)

        self.sizer.Add(self._panel_plot, 1, wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.choice_circuit_SN_pair.Bind(wx.EVT_CHOICE, self.OnCircuitSN)
        self.btn_dl_info.Bind(wx.EVT_BUTTON, self.OnDLInfo)
        self.btn_connect.Bind(wx.EVT_BUTTON, self.OnConnect)
        self.btn_start.Bind(wx.EVT_BUTTON, self.OnStart)

    def OnCircuitSN(self, evt):
        receiver_choice = self.choice_circuit_SN_pair.GetStringSelection()
        self.btn_connect.SetLabel('Connect to Receiver %s / COMX' % receiver_choice[-11:-1])
        self.btn_connect.Enable(True)
        self.btn_dl_info.Enable(False)

    def OnDLInfo(self, evt):
        self.load_info()

    def OnConnect(self, evt):
        if 'Connect' in self.btn_connect.GetLabel():
            receiver_choice = self.choice_circuit_SN_pair.GetStringSelection()
            SN_choice = receiver_choice[-11:-1]
            COM_ports = self._receiver.FindDevices()
            for COM in COM_ports:  # When multiple receivers are connected, make sure you connect/extract data from the receiver of interest
                if not (COM in engaged_COM_list):
                    potential_receiver = self._receiver(COM)
                    potential_SN = potential_receiver.ReadManufacturingData().get('SerialNumber')
                    if potential_SN == SN_choice:
                        potential_receiver.Disconnect()
                        self._panel_plot.dexcom_receiver = self._receiver(COM)
                        engaged_COM_list.append(COM)
                        self.btn_connect.SetLabel('Disconnect Receiver %s / %s' % (SN_choice, COM))
                        self.btn_start.Enable(True)
                        self.choice_circuit_SN_pair.Enable(False)
                        return
                    else:
                        potential_receiver.Disconnect()
            wx.MessageBox('Receiver is Already Connected to a Different Panel; Choose a Different One', 'Error', wx.OK | wx.ICON_ERROR)  # Executes only if the receiver that is trying to be accessed is already accessed by a different subpanel
        else:
            self._panel_plot.timer_plot.Stop()
            self._panel_plot.dexcom_receiver.Disconnect()
            self._panel_plot.dexcom_receiver = None
            self._panel_plot._time = None
            self._panel_plot._CGM = None
            connected_COM = (self.btn_connect.GetLabel().split('/ '))[1]
            engaged_COM_list.remove(connected_COM)
            self.btn_start.Enable(False)
            self.btn_start.SetLabel('Start Acquisition')
            self.btn_connect.SetLabel('Connect to Receiver %s / COMX' % self.choice_circuit_SN_pair.GetStringSelection()[-11:-1])
            self.choice_circuit_SN_pair.Enable(True)

    def OnStart(self, evt):
        state = self.btn_start.GetLabel()
        if state == 'Start Acquisition':
            self._panel_plot.timer_plot.Start(1000, wx.TIMER_CONTINUOUS )
            self.btn_start.SetLabel('Stop Acquisition')
        else:
            self._panel_plot.timer_plot.Stop()
            self.btn_start.SetLabel('Start Acquisition')

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        devices = {'Receiver #1': Dexcom,
                     'Receiver #2': Dexcom,
                     'Receiver #3': Dexcom
                   }
        sizer = wx.GridSizer(cols=3)
        for key, device in devices.items():
            sizer.Add(PanelDexcom(self, device, name=key), 1, wx.EXPAND, border=2)
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
    LP_CFG.set_base(basepath='~/Documents/LPTEST')
    LP_CFG.update_stream_folder()
    app = MyTestApp(0)
    app.MainLoop()
