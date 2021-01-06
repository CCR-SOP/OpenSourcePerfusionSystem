# -*- coding: utf-8 -*-
"""

@author: Allen Luna

Panel class for testing and configuring Dexcom G6 Receiver/Sensor pair
"""
import wx
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.panel_plotting import PanelPlotting
from dexcom_G6_reader.readdata import Dexcom

engaged_COM_list = []

class GraphingDexcom(PanelPlotting):
    def __init__(self, parent, with_readout=True):
        super().__init__(parent, with_readout)
        self.__plot_len = 50
        self._valid_range = [60, 120]
        self._plot_frame_ms = 60_000

        self.timer_plot = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer_plot.Start(1000, wx.TIMER_CONTINUOUS)  # Time between graphing each value

    def OnTimer(self, event):
        if event.GetId() == self.timer_plot.GetId():
            self.get_CGM_data()
            self.plot()

    def plot(self):  # Called every 1000 milliseconds)

        self.axes.relim()
        self.axes.autoscale_view()
        self.canvas.draw()

    def get_CGM_data(self):
        print('x')

    def add_Dexcom(self, color='r'):
        self.axes.plot([0] * self.__plot_len)
        self.axes.fill_between([0, 1], [0, 0], [0, 0])
        if self._with_readout:
            self.axes.text(1.06, 0.5, '0', transform=self.axes.transAxes,fontsize=18, ha='center')
            self.axes.text(1.06, 0.4, 'mg/dL', transform=self.axes.transAxes, fontsize=8,ha='center')
        if self._valid_range is not None:
            rng = self._valid_range
            self._shaded['normal'] = self.axes.axhspan(rng[0], rng[1], color='g',alpha=0.2)
            self._valid_range = rng
            self._configure_plot()
        #elif type(sensor) is SensorPoint:
         #   self.__line[sensor.name] = self.axes.vlines(0, ymin=0, ymax=100, color=color,
          #                                              label=sensor.name)  # Plotting a vertical line @ x = 0 between ymin and ymax
           # self.__colors[sensor.name] = color

    def _configure_plot(self):
        self.axes.set_title('Dexcom')
        self.axes.set_ylabel('mg/dL')
        self.show_legend()

    def show_legend(self):
        self.axes.legend(loc='lower left', bbox_to_anchor=(0.0, 1.01, 1.0, .102), ncol=2, mode="expand",
                         borderaxespad=0, framealpha=0.0, fontsize='x-small')


















class PanelDexcom(wx.Panel):
    def __init__(self, parent, receiver, name='Receiver'):
        self.parent = parent
        self._receiver = receiver
        self._name = name
        self._circuit_SN_pairs = []
        wx.Panel.__init__(self, parent, -1)

        LP_CFG.set_base()
        LP_CFG.update_stream_folder()

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_circuit_SN_pair = wx.StaticText(self, label='Dexcom Receiver')
        self.choice_circuit_SN_pair = wx.Choice(self, wx.ID_ANY, choices=[])

        self.btn_dl_info = wx.Button(self, label='Download Receiver Info')

        self.btn_connect = wx.Button(self, label='Connect to Receiver')
        self.btn_connect.Enable(False)

        self.btn_disconnect = wx.Button(self, label='Disconnect Receiver S/N: xxxxxxxxx')
        self.btn_disconnect.Enable(False)

        self.btn_start = wx.ToggleButton(self, label='Start Acquisition')
        self.btn_start.Enable(False)

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
        self.btn_start.Bind(wx.EVT_TOGGLEBUTTON, self.OnStart)

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
                    dexcom_receiver = self._receiver(COM)

                    SN_info = '%s S/N: %s;  ' % (dexcom_receiver.GetFirmwareHeader().get('ProductName'), dexcom_receiver.ReadManufacturingData().get('SerialNumber'))
                    Transmitter_info = 'Transmitter: %s;  ' % dexcom_receiver.ReadTransmitterId().decode('utf-8')
                    CGM_info = 'CGM records: %d' % (len(dexcom_receiver.ReadRecords('EGV_DATA')))
                    Aggregate_info = SN_info + Transmitter_info + CGM_info
                    wx.MessageBox(Aggregate_info, 'Receiver Connected!', wx.OK | wx.ICON_NONE)

                    engaged_COM_list.append(COM)
                    self.btn_connect.SetLabel('Connected to %s' % COM)
                    self.btn_connect.Enable(False)
                    self.btn_start.Enable(True)
                    self.btn_disconnect.SetLabel('Disconnect Receiver S/N: %s' % dexcom_receiver.ReadManufacturingData().get('SerialNumber'))
                    self.btn_disconnect.Enable(True)
                    return
                else:
                    potential_receiver.Disconnect()
        wx.MessageBox('Receiver is Already Connected to a Different Panel; Choose a Different One', 'Error', wx.OK | wx.ICON_ERROR)  # Executes if the receiver that is trying to be accessed is already accessed by a different subpanel


    def OnDisconnect(self, evt):
        connected_COM = self.btn_connect.GetLabel()[-4:]
        engaged_COM_list.remove(connected_COM)
        print(engaged_COM_list)
        self.btn_start.Enable(False)
        self.btn_connect.SetLabel('Connect to Receiver')
        self.btn_connect.Enable(True)
        self.btn_disconnect.SetLabel('Disconnect Receiver S/N: xxxxxxxxx')
        self.btn_disconnect.Enable(False)

    def OnStart(self, evt):
        print('y')


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
