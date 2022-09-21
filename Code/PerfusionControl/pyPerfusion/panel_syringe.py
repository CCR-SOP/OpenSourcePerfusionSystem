# -*- coding: utf-8 -*-
"""Panel class for testing and configuring Pump 11 Elite syringe pump


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.SensorPoint import SensorPoint
import pyPerfusion.utils as utils
from pyPerfusion.FileStrategy import PointsToFile
import pyPerfusion.pyPump11Elite as pyPump11Elite


BAUD_RATES = ['9600', '14400', '19200', '38400', '57600', '115200']


class PanelSyringe(wx.Panel):
    def __init__(self, parent, syringe: pyPump11Elite.Pump11Elite):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self.syringe = syringe

        self._panel_cfg = PanelSyringeConfig(self, syringe)
        self._panel_ctrl = PanelSyringeControls(self, syringe)
        static_box = wx.StaticBox(self, wx.ID_ANY, label=self.syringe.name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()

        self.sizer.Add(self._panel_cfg, flags.Proportion(2))
        self.sizer.Add(self._panel_ctrl, flags.Proportion(2))
        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass


class PanelSyringeConfig(wx.Panel):
    def __init__(self, parent, syringe: pyPump11Elite.Pump11Elite):
        super().__init__(parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self.syringe = syringe

        self._manufacturers = {}

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.label_port = wx.StaticText(self, label='COM Port')
        avail_ports = pyPump11Elite.get_avail_com_ports()
        self.combo_port = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY, choices=avail_ports)

        self.label_baud = wx.StaticText(self, label='Baud')
        self.choice_baud = wx.Choice(self, wx.ID_ANY, choices=BAUD_RATES)
        self.choice_baud.SetSelection(0)

        self.btn_open = wx.ToggleButton(self, label='Open')

        self.label_manufacturer = wx.StaticText(self, label='Manufacturer')
        self.combo_manufacturer = wx.ComboBox(self, wx.ID_ANY, choices=[])
        self.label_sizes = wx.StaticText(self, label='Syringe Sizes')
        self.combo_sizes = wx.ComboBox(self, wx.ID_ANY, choices=[])

        self.btn_save_cfg = wx.Button(self, label='Save')
        self.btn_load_cfg = wx.Button(self, label='Load')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center()

        sizer_cfg = wx.GridSizer(cols=2)
        sizer_cfg.Add(self.label_port, flags)
        sizer_cfg.Add(self.combo_port, flags)

        sizer_cfg.Add(self.label_baud, flags)
        sizer_cfg.Add(self.choice_baud, flags)

        sizer_cfg.Add(self.btn_open, flags)
        sizer_cfg.AddSpacer(2)

        sizer_cfg.Add(self.label_manufacturer, flags)
        sizer_cfg.Add(self.label_sizes, flags)
        sizer_cfg.Add(self.combo_manufacturer, flags)
        sizer_cfg.Add(self.combo_sizes, flags)

        sizer_cfg.Add(self.btn_load_cfg, flags)
        sizer_cfg.Add(self.btn_save_cfg, flags)
        self.sizer.Add(sizer_cfg)

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_open.Bind(wx.EVT_TOGGLEBUTTON, self.OnOpen)
        self.combo_port.Bind(wx.EVT_COMBOBOX_DROPDOWN, self.OnPortDropDown)
        self.combo_manufacturer.Bind(wx.EVT_COMBOBOX, self.OnManufacturer)
        self.btn_save_cfg.Bind(wx.EVT_BUTTON, self.OnSaveCfg)
        self.btn_load_cfg.Bind(wx.EVT_BUTTON, self.OnLoadCfg)

    def OnPortDropDown(self, evt):
        ports = pyPump11Elite.get_avail_com_ports()
        self._lgr.info(f'Available com ports are {ports}')
        self.combo_port.Set(ports)

    def OnManufacturer(self, evt):
        if self.syringe.is_open():
            self.syringe.clear_syringe()
            target = self.combo_manufacturer.GetStringSelection()
            code = [code for code, name in self._manufacturers.items() if name == target]
            if len(code) > 0:
                sizes = self.syringe.get_available_syringes(code[0])
                self.combo_sizes.Set(sizes)

    def OnOpen(self, evt):
        port = self.combo_port.GetStringSelection()
        baud = int(self.choice_baud.GetStringSelection())
        if not self.syringe.is_open():
            self.syringe.open(port, baud)
            self._manufacturers = self.syringe.get_available_manufacturers()
            self.combo_manufacturer.Set(list(self._manufacturers.values()))
            self.btn_open.SetLabel('Close')
        else:
            self._lgr.debug(f'Closing syringe at {port}, {baud}')
            self.syringe.close()
            self.btn_open.SetLabel('Open')


    def OnSaveCfg(self, evt):
        section = LP_CFG.get_hwcfg_section(self.syringe.name)
        section['ComPort'] = self.combo_port.GetStringSelection()
        section['Baud'] = self.choice_baud.GetStringSelection()
        section['Manufacturer'] = self.combo_manufacturer.GetStringSelection()
        section['Size'] = self.combo_sizes.GetStringSelection()
        LP_CFG.update_hwcfg_section(self.syringe.name, section)

    def OnLoadCfg(self, evt):
        section = LP_CFG.get_hwcfg_section(self.syringe.name)
        self.combo_port.SetStringSelection(section['ComPort'])
        self.choice_baud.SetStringSelection(section['Baud'])
        self.combo_manufacturer.SetValue(section['Manufacturer'])
        self.OnManufacturer(None)
        self.combo_sizes.SetValue(section['Size'])


class PanelSyringeControls(wx.Panel):
    def __init__(self, parent, syringe: pyPump11Elite.Pump11Elite):
        super().__init__(parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self.syringe = syringe
        self._inc = 100

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.spin_rate = wx.SpinCtrlDouble(self, min=0, max=100000, inc=self._inc)
        self.spin_rate.SetValue(100)
        self.label_rate = wx.StaticText(self, label='Infusion Rate (ul/min)')
        self.btn_basal = wx.ToggleButton(self, label='Start Basal')

        self.spin_volume = wx.SpinCtrlDouble(self, min=0, max=100000, inc=self._inc)
        self.spin_volume.SetValue(1000)
        self.label_volume = wx.StaticText(self, label='Target Volume (ul)')
        self.btn_bolus = wx.Button(self, label='Bolus')

        self.btn_save_cfg = wx.Button(self, label='Save')
        self.btn_load_cfg = wx.Button(self, label='Load')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center()

        sizer_cfg = wx.GridSizer(cols=3)
        sizer_cfg.Add(self.label_rate, flags)
        sizer_cfg.Add(self.spin_rate, flags)
        sizer_cfg.Add(self.btn_basal, flags)

        sizer_cfg.Add(self.label_volume, flags)
        sizer_cfg.Add(self.spin_volume, flags)
        sizer_cfg.Add(self.btn_bolus, flags)

        sizer_cfg.Add(self.btn_save_cfg, flags)
        sizer_cfg.Add(self.btn_load_cfg, flags)

        self.sizer.Add(sizer_cfg)

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_basal.Bind(wx.EVT_TOGGLEBUTTON, self.OnBasal)
        self.btn_bolus.Bind(wx.EVT_BUTTON, self.OnBolus)
        self.btn_save_cfg.Bind(wx.EVT_BUTTON, self.OnSaveCfg)
        self.btn_load_cfg.Bind(wx.EVT_BUTTON, self.OnLoadCfg)

    def OnBasal(self, evt):
        infusion_rate = self.spin_rate.GetValue()
        if self.syringe.is_infusing:
            self.btn_basal.SetLabel('Start Basal')
            self.btn_basal.SetValue(True)
            self.syringe.stop()
        else:
            self.syringe.set_infusion_rate(infusion_rate)
            self._lgr.debug(f'infusion rate: {infusion_rate}')
            self._lgr.debug(f'target volume: {0}')
            self.syringe.start_constant_infusion()
            self.btn_basal.SetLabel('Stop')
            self.btn_basal.SetValue(False)

    def OnBolus(self, evt):
        infusion_rate = self.spin_rate.GetValue()
        target_vol = self.spin_volume.GetValue()
        self.syringe.set_infusion_rate(infusion_rate)
        self.syringe.set_target_volume(target_vol)
        self.syringe.infuse_to_target_volume()

    def OnSaveCfg(self, evt):
        section = LP_CFG.get_hwcfg_section(self.syringe.name)
        section['InjectionRate'] = str(int(self.spin_rate.GetValue()))
        section['TargetVolume'] = str(int(self.spin_volume.GetValue()))
        LP_CFG.update_hwcfg_section(self.syringe.name, section)

    def OnLoadCfg(self, evt):
        section = LP_CFG.get_hwcfg_section(self.syringe.name)
        self.spin_rate.SetValue(section['InjectionRate'])
        self.spin_volume.SetValue(section['TargetVolume'])

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        # see if there are any available com ports, if not
        # use a mock for testing.
        ports = pyPump11Elite.get_avail_com_ports()
        if len(ports) > 0:
            self.syringe = pyPump11Elite.Pump11Elite('Example Syringe')
        else:
            self.syringe = pyPump11Elite.MockPump11Elite('MOCK Syringe')

        self.panel = PanelSyringe(self, self.syringe)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.syringe.close()
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
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()
    app = MyTestApp(0)
    app.MainLoop()
