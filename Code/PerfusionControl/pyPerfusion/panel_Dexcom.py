# -*- coding: utf-8 -*-
"""

@author: Allen Luna

Panel class for testing and configuring Dexcom G6 Receiver/Sensor pair
"""
import wx
import pyPerfusion.PerfusionConfig as LP_CFG
import matplotlib as mpl
from pyPerfusion.panel_plotting import PanelPlotting
from dexcom_G6_reader.readdata import Dexcom

engaged_COM_list = []
mpl.rcParams.update({'font.size': 6})

class GraphingDexcom(PanelPlotting):  # Work
    def __init__(self, parent, with_readout=True):
        super().__init__(parent, with_readout)
        self._valid_range = [80, 110]
        self._CGM = None
        self._time = 0
        self._index = 0  # Delete
        self._dexcom_receiver = None
        self.__val_display = None

        self.timer_plot.Start(1000, wx.TIMER_CONTINUOUS)
        self.timer_plot.Stop()

    def add_Dexcom(self):
        if self._with_readout:
            self.__val_display = self.axes.text(1.06, 0.5, '0', transform=self.axes.transAxes, fontsize=18, ha='center')
            self.axes.text(1.06, 0.4, 'mg/dL', transform=self.axes.transAxes, fontsize=8, ha='center')
        if self._valid_range is not None:
            rng = self._valid_range
            self._shaded['normal'] = self.axes.axhspan(rng[0], rng[1], color='g', alpha=0.2)
            self._valid_range = rng
        self._configure_plot()

    def _configure_plot(self):
        self.axes.set_title('Glucose Concentration (mg/dL)')
        self.axes.set_ylabel('mg/dL')

    def OnTimer(self, event):  # Work
        if event.GetId() == self.timer_plot.GetId():
            glucose, acq_time = PanelDexcom.get_latest_CGM(self)
            if (self._CGM is None) and (self._time is None):
                pass
            else:
                self._CGM = glucose
                self._time = acq_time
                self.plot()

    def plot(self):
        if self._valid_range is not None:
            if self._CGM > self._valid_range[1]:
                self.axes.plot_date(self._time, self._CGM, color='red', marker='o', xdate=True)
            elif self._CGM < self._valid_range[0]:
                self.axes.plot_date(self._time, self._CGM, color='orange', marker='o', xdate=True)
            else:
                self.axes.plot_date(self._time, self._CGM, color='black', marker='o', xdate=True)
        if self._with_readout:
            readout = self._CGM
            if readout < self._valid_range[0]:
                color = 'orange'
            elif readout > self._valid_range[1]:
                color = 'red'
            else:
                color = 'black'
            self.__val_display.set_text(f'{readout:.0f}')
            self.__val_display.set_color(color)

        self.axes.relim()
        x = self.axes.get_xticklabels()
        if len(x) >= 12:
            self.axes.set_xlim(left=x[-12].get_text(), right=self._time)
        self.axes.autoscale_view()
        self.canvas.draw()

class PanelDexcom(wx.Panel):
    def __init__(self, parent, receiver, name='Receiver'):
        self.parent = parent
        self._receiver = receiver
        self._dexcom_receiver = None
        self._name = name
        self._index = 0  # Delete
        self._circuit_SN_pairs = []
        wx.Panel.__init__(self, parent, -1)

        LP_CFG.set_base()

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_circuit_SN_pair = wx.StaticText(self, label='Dexcom Receiver')
        self.choice_circuit_SN_pair = wx.Choice(self, wx.ID_ANY, choices=[])

        self.btn_dl_info = wx.Button(self, label='Download Receiver Info')

        self.btn_connect = wx.Button(self, label='Connect to Receiver')
        self.btn_connect.Enable(False)

        self.btn_disconnect = wx.Button(self, label='Disconnect Receiver S/N: xxxxxxxxx')
        self.btn_disconnect.Enable(False)

        self.btn_start = wx.Button(self, label='Start Acquisition')
        self.btn_start.Enable(False)

        self.btn_stop = wx.Button(self, label='Stop Acquisition')
        self.btn_stop.Enable(False)

        self.label_error = wx.StaticText(self, label='No Sensor Errors Detected')

        self.panel_plot = GraphingDexcom(self)
        self.panel_plot.add_Dexcom()

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

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sizer_circuit_SN_pair)
        self.sizer.Add(sizer)

        self.sizer.AddSpacer(10)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_dl_info, flags)
        self.sizer.Add(sizer)

        self.sizer.AddSpacer(10)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_connect)
        sizer.AddSpacer(10)
        sizer.Add(self.btn_disconnect)
        self.sizer.Add(sizer)

        self.sizer.AddSpacer(10)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_start)
        sizer.AddSpacer(10)
        sizer.Add(self.btn_stop)
        self.sizer.Add(sizer)

        self.sizer.AddSpacer(10)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_error)
        self.sizer.Add(sizer)

        self.sizer.Add(self.panel_plot, 1, wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.choice_circuit_SN_pair.Bind(wx.EVT_CHOICE, self.OnCircuitSN)
        self.btn_dl_info.Bind(wx.EVT_BUTTON, self.OnDLInfo)
        self.btn_connect.Bind(wx.EVT_BUTTON, self.OnConnect)
        self.btn_disconnect.Bind(wx.EVT_BUTTON, self.OnDisconnect)
        self.btn_start.Bind(wx.EVT_BUTTON, self.OnStart)
        self.btn_stop.Bind(wx.EVT_BUTTON, self.OnStop)

    def OnCircuitSN(self, evt):
        state = self.btn_connect.GetLabel()
        if state == 'Connect to Receiver':
            self.btn_connect.Enable(True)

    def OnDLInfo(self, evt):
        self.load_info()

    def OnConnect(self, evt):
        receiver_choice = self.choice_circuit_SN_pair.GetStringSelection()
        if not receiver_choice:
            wx.MessageBox('Please Choose a Dexcom Receiver to Connect to', 'Error', wx.OK | wx.ICON_ERROR)
            return
        SN_choice = receiver_choice[-11:-1]
        COM_ports = self._receiver.FindDevices()
        for COM in COM_ports:
            if not (COM in engaged_COM_list):
                potential_receiver = self._receiver(COM)
                potential_SN = potential_receiver.ReadManufacturingData().get('SerialNumber')
                if potential_SN == SN_choice:
                    potential_receiver.Disconnect()
                    self._dexcom_receiver = self._receiver(COM)
                    self.panel_plot._dexcom_receiver = self._dexcom_receiver

                    SN_info = '%s S/N: %s;  ' % (self._dexcom_receiver.GetFirmwareHeader().get('ProductName'), self._dexcom_receiver.ReadManufacturingData().get('SerialNumber'))
                    Transmitter_info = 'Transmitter: %s;  ' % self._dexcom_receiver.ReadTransmitterId().decode('utf-8')
                    CGM_info = 'CGM records: %d' % (len(self._dexcom_receiver.ReadRecords('EGV_DATA')))
                    Aggregate_info = SN_info + Transmitter_info + CGM_info
                    wx.MessageBox(Aggregate_info, 'Receiver Connected!', wx.OK | wx.ICON_NONE)

                    engaged_COM_list.append(COM)
                    self.btn_connect.SetLabel('Connected to %s' % COM)
                    self.btn_connect.Enable(False)
                    self.btn_start.Enable(True)
                    self.btn_disconnect.SetLabel('Disconnect Receiver S/N: %s' % self._dexcom_receiver.ReadManufacturingData().get('SerialNumber'))
                    self.btn_disconnect.Enable(True)
                    return
                else:
                    potential_receiver.Disconnect()
        wx.MessageBox('Receiver is Already Connected to a Different Panel; Choose a Different One', 'Error', wx.OK | wx.ICON_ERROR)  # Executes if the receiver that is trying to be accessed is already accessed by a different subpanel

    def OnDisconnect(self, evt):  # Work
        connected_COM = self.btn_connect.GetLabel()[-4:]
        engaged_COM_list.remove(connected_COM)
        self._dexcom_receiver.Disconnect()
        self.btn_start.Enable(False)
        self.btn_stop.Enable(False)
        self.btn_connect.SetLabel('Connect to Receiver')
        self.btn_connect.Enable(True)
        self.btn_disconnect.SetLabel('Disconnect Receiver S/N: xxxxxxxxx')
        self.btn_disconnect.Enable(False)
        self.panel_plot.timer_plot.Stop()
        self.panel_plot._dexcom_receiver = None

    def OnStart(self, evt):  # Work
        self.btn_start.Enable(False)
        self.btn_stop.Enable(True)
        self.panel_plot.timer_plot.Start()

    def OnStop(self, evt):  # Work
        self.btn_start.Enable(True)
        self.btn_stop.Enable(False)
        self.panel_plot.timer_plot.Stop()
        # Reset plot, save off previous plot

    def get_latest_CGM(self):  # Work
        CGM_records = self._dexcom_receiver.ReadRecords('EGV_DATA')
        CGM_records = CGM_records[25:-25]  # Delete
        latest_read_split = str(CGM_records[self._index]).split(': ')
        self._index += 1  # Delete
        latest_read_time = latest_read_split[0][11:16]
        latest_read_value = latest_read_split[1]
        if (latest_read_value == 'ABSOLUTE_DEVIATION') or (latest_read_value == 'POWER_DEVIATION') or (latest_read_value == 'COUNTS_DEVIATION'):
            self.label_error.SetLabel(latest_read_value + ' Error' + '- See Receiver for More Info')
            return None, latest_read_time
        elif latest_read_value == 'SENSOR_NOT_ACTIVE':
            self.label_error.SetLabel('Sensor Not Active: Replace Sensor Now!')
            return None, None
        elif latest_read_value[0:3] == 'CGM':
            latest_CGM_value = int(latest_read_value.split('BG:')[1].split(' (')[0])
            return latest_CGM_value, latest_read_time
        else:
            self.label_error.SetLabel('Unknown Error - See Receiver for More Info')
            return None, latest_read_time

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
    app = MyTestApp(0)
    app.MainLoop()
