# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for testing and configuring Elite 11 Syringe Pump
"""
import wx
import time
from serial import SerialException
from pyHardware.PHDserial import PHDserial
import pyPerfusion.PerfusionConfig as LP_CFG

class PanelSyringe(wx.Panel):
    def __init__(self, parent, syringe, name):
        self.parent = parent
        self._syringe = syringe
        self._name = name
        wx.Panel.__init__(self, parent, -1)

        LP_CFG.set_base()
        self._comm, self._baud = self.get_hardware_info()

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_comm = wx.StaticText(self, label='USB COMM:')
        self.choice_comm = wx.StaticText(self, label=self._comm)

        self.label_baud = wx.StaticText(self, label='Baud Rate:')
        self.choice_baud = wx.StaticText(self, label=self._baud)

        self.btn_open = wx.ToggleButton(self, label='Open')

        self.label_manu = wx.StaticText(self, label='Manufacturer')
        self.choice_manu = wx.Choice(self, choices=[])

        self.label_types = wx.StaticText(self, label='Syringe Type')
        self.choice_types = wx.Choice(self, choices=[])

        self.btn_dl_info = wx.Button(self, label='Download Syringe Info')
        self.btn_dl_info.Enable(False)

        self.label_rate = wx.StaticText(self, label='Infusion Rate')
        self.spin_rate = wx.SpinCtrl(self, min=1, max=100000)
        self.spin_rate.SetValue(1)
        self.choice_rate = wx.Choice(self, choices=['ul/min', 'ml/min'])
        self.choice_rate.SetSelection(1)
        self.btn_update = wx.Button(self, label='Update')

        self.btn_infuse = wx.Button(self, label='Infuse')
        self.btn_stop = wx.Button(self, label='Stop')

        self.label_volume_infuse = wx.StaticText(self, label='Volume Infusion (ml)')
        self.spin_volume_infuse = wx.SpinCtrl(self, min=0, max=10)
        self.spin_volume_infuse.SetValue(1)
        self.btn_volume_infuse = wx.Button(self, label='Initiate Set Volume Infusion')

        self.btn_save = wx.Button(self, label='Save Config')
        self.btn_load = wx.Button(self, label='Load Config')

        self.load_info()

        self.__do_layout()
        self.__set_bindings()

    def get_hardware_info(self):
        COMs_bauds = LP_CFG.get_COMs_bauds()
        for syringe, info in COMs_bauds.items():
            if self._name.lower() == syringe:
                comm = info[0]
                baud = info[1]
                return comm, baud

    def load_info(self):
        codes, volumes = LP_CFG.open_syringe_info()
        self._syringe.manufacturers = codes
        self._syringe.syringes = volumes
        self.update_syringe_choices()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 2).Expand().Proportion(1)

        self.sizer_comm = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_comm.Add(self.label_comm, flags)
        self.sizer_comm.Add(self.choice_comm, flags)

        self.sizer_baud = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_baud.Add(self.label_baud, flags)
        self.sizer_baud.Add(self.choice_baud, flags)

        self.sizer_manu = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_manu.Add(self.label_manu, flags)
        self.sizer_manu.Add(self.choice_manu, flags)

        self.sizer_types = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_types.Add(self.label_types, flags)
        self.sizer_types.Add(self.choice_types, flags)

        self.sizer_rate = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_rate.Add(self.label_rate, flags)
        self.sizer_rate.Add(self.spin_rate, flags)
        self.sizer_rate.Add(self.choice_rate, flags)
        self.sizer_rate.AddSpacer(20)
        self.sizer_rate.Add(self.btn_update)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sizer_comm, flags)
        sizer.AddSpacer(10)
        sizer.Add(self.sizer_baud, flags)
        self.sizer.Add(sizer, flags)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_open, flags)
        sizer.AddSpacer(10)
        sizer.Add(self.btn_dl_info, flags)
        self.sizer.Add(sizer, flags)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_save, flags)
        sizer.AddSpacer(10)
        sizer.Add(self.btn_load, flags)
        self.sizer.Add(sizer, flags)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer_manu, flags)
        sizer.Add(self.sizer_types, flags)
        self.sizer.Add(sizer, flags)

        self.sizer.AddSpacer(10)
        self.sizer.Add(self.sizer_rate, flags)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_infuse, flags)
        sizer.Add(self.btn_stop, flags)
        self.sizer.AddSpacer(5)
        self.sizer.Add(sizer, flags)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_volume_infuse, flags)
        sizer.Add(self.spin_volume_infuse, flags)
        sizer.Add(self.btn_volume_infuse, flags)
        self.sizer.AddSpacer(5)
        self.sizer.Add(sizer, flags)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_open.Bind(wx.EVT_TOGGLEBUTTON, self.OnOpen)
        self.choice_manu.Bind(wx.EVT_CHOICE, self.OnManu)
        self.choice_types.Bind(wx.EVT_CHOICE, self.OnTypes)
        self.btn_update.Bind(wx.EVT_BUTTON, self.OnUpdate)
        self.btn_infuse.Bind(wx.EVT_BUTTON, self.OnInfuse)
        self.btn_stop.Bind(wx.EVT_BUTTON, self.OnStop)
        self.btn_dl_info.Bind(wx.EVT_BUTTON, self.OnDLInfo)
        self.btn_save.Bind(wx.EVT_BUTTON, self.OnSaveConfig)
        self.btn_load.Bind(wx.EVT_BUTTON, self.OnLoadConfig)
        self.btn_volume_infuse.Bind(wx.EVT_BUTTON, self.OnSetInfusion)

    def OnOpen(self, evt):
        state = self.btn_open.GetValue()
        if state:
            comm = self.choice_comm.GetLabel()
            baud = self.choice_baud.GetLabel()
            try:
                self._syringe.open(comm, int(baud))
                self._syringe.ResetSyringe()
                self._syringe.syringe_configuration()
                self._syringe.open_stream(LP_CFG.LP_PATH['stream'])
                self._syringe.start_stream()
                self.btn_open.SetLabel('Close', )
                self.btn_dl_info.Enable(True)
            except SerialException:
                wx.MessageBox('Port Could Not be Opened; it is Already in Use by Another Syringe', 'Error',
                           wx.OK | wx.ICON_ERROR)
                return
        else:
            self._syringe.close()
            self.btn_open.SetLabel('Open')
            self.btn_dl_info.Enable(False)

    def update_syringe_choices(self):
        self.choice_manu.Clear()
        manu = self._syringe.manufacturers
        if not manu:
            # create dummy map for testing
            manu = {'ABC': 'Test 1', 'DEF': 'Test 2'}

        manu_str = [f'({code}) {desc}' for code, desc in manu.items()]
        self.choice_manu.Append(manu_str)

    def update_syringe_types(self):
        code = self.get_selected_code()
        self.choice_types.Clear()
        syringes = self._syringe.syringes
        if not syringes:
            # create dummy map for testing
            syringes = {'ABC': ['1 ml', '2 ml', '3 ml'], 'DEF': ['4 ul', '5 ul', '6 ul']}

        types = syringes[code]
        self.choice_types.Append(types)

    def get_selected_code(self):
        sel = self.choice_manu.GetString(self.choice_manu.GetSelection())
        code = sel[1:4]
        return code

    def OnManu(self, evt):
        code = self.get_selected_code()
        self.update_syringe_types()

    def OnTypes(self, evt):
        code = self.get_selected_code()
        syr_size = self.choice_types.GetString(self.choice_types.GetSelection())
        self._syringe.set_syringe_manufacturer_size(code, syr_size)

    def OnUpdate(self, evt):
        rate = self.spin_rate.GetValue()
        unit = self.choice_rate.GetString(self.choice_rate.GetSelection())
        self._syringe.set_infusion_rate(rate, unit)

    def OnInfuse(self, evt):
        self._syringe.infuse()

    def OnStop(self, evt):
        self._syringe.stop()

    def OnSetInfusion(self, evt):
        self._syringe.reset_infusion_volume()
        self._syringe.reset_target_volume()
        target_volume = self.spin_volume_infuse.GetValue()
        self._syringe.set_target_volume(target_volume, 'ml')
        infusion_rate = int(self._syringe.get_infusion_rate().split(' ')[0])
        wait_time = ((target_volume/infusion_rate) * 60) + 0.5
        self._syringe.target_infuse(target_volume, infusion_rate)
        time.sleep(wait_time)
        self._syringe.reset_infusion_volume()
        self._syringe.reset_target_volume()

    def OnDLInfo(self, evt):
        self._syringe.update_syringe_manufacturers()
        self._syringe.update_syringe_types()
        self.update_syringe_choices()
        LP_CFG.save_syringe_info(self._syringe.manufacturers, self._syringe.syringes)

    def OnSaveConfig(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        section['CommPort'] = self.choice_comm.GetLabel()
        section['BaudRate'] = self.choice_baud.GetLabel()
        section['ManuCode'] = self.choice_manu.GetStringSelection()
        section['Volume'] = self.choice_types.GetStringSelection()
        section['Rate'] = str(self.spin_rate.GetValue())
        section['Unit'] = self.choice_rate.GetStringSelection()
        LP_CFG.update_hwcfg_section(self._name, section)

    def OnLoadConfig(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        state = self.btn_open.GetValue()
        if state:
            self._syringe.close()
            self.btn_open.SetLabel('Open')
            self.btn_dl_info.Enable(False)
        self.choice_comm.SetLabel(section['CommPort'])
        self.choice_baud.SetLabel(section['BaudRate'])
        comm = self.choice_comm.GetLabel()
        baud = self.choice_baud.GetLabel()
        try:
            self._syringe.open(comm, int(baud))
            self._syringe.ResetSyringe()
            self._syringe.syringe_configuration()
            self._syringe.open_stream(LP_CFG.LP_PATH['stream'])
            self._syringe.start_stream()
            self.btn_open.SetLabel('Close', )
            self.btn_dl_info.Enable(True)

            self.choice_manu.SetStringSelection(section['ManuCode'])
            self.update_syringe_types()
            self.choice_types.SetStringSelection(section['Volume'])
            manu = self.get_selected_code()
            syr_size = self.choice_types.GetString(self.choice_types.GetSelection())
            self._syringe.set_syringe_manufacturer_size(manu, syr_size)

            self.spin_rate.SetValue(int(section['Rate']))
            self.choice_rate.SetStringSelection(section['Unit'])
            rate = self.spin_rate.GetValue()
            unit = self.choice_rate.GetString(self.choice_rate.GetSelection())
            self._syringe.set_infusion_rate(rate, unit)

        except SerialException:
            wx.MessageBox('Port Could Not be Opened; it is Already in Use by Another Syringe', 'Error',
                          wx.OK | wx.ICON_ERROR)
            return

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        syringes = {'Insulin (PV)': PHDserial('Insulin'),
                    'Glucagon (PV)': PHDserial('Glucagon'),
                    'Phenylephrine (HA)': PHDserial('Phenylephrine'),
                    'Epoprostenol (HA)': PHDserial('Epoprostenol'),
                    'TPN/Bile Salts (PV)': PHDserial('TPN/Bile Salts'),
                    'Heparin/Methylprednisolone/Ampicillin-Sulbactam (PV)': PHDserial('Heparin/Methylprednisolone/Ampicillin-Sulbactam')
                    }
        sizer = wx.GridSizer(cols=3)
        for key, syringe in syringes.items():
            sizer.Add(PanelSyringe(self, syringe, name=key), 1, wx.EXPAND, border=2)
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
