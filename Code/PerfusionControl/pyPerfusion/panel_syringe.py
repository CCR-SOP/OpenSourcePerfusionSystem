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
from pyPerfusion.pyPump11Elite import Pump11Elite, get_avail_com_ports


BAUD_RATES = ['9600', '14400', '19200', '38400', '57600', '115200']


class PanelSyringe(wx.Panel):
    def __init__(self, parent, syringe: Pump11Elite):
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
    def __init__(self, parent, syringe: Pump11Elite):
        super().__init__(parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self.syringe = syringe

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.label_port = wx.StaticText(self, label='COM Port')
        avail_ports = get_avail_com_ports()
        self.combo_port = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY, choices=avail_ports)

        self.label_baud = wx.StaticText(self, label='Baud')
        self.choice_baud = wx.Choice(self, wx.ID_ANY, choices=BAUD_RATES)
        self.choice_baud.SetSelection(0)

        self.btn_open = wx.ToggleButton(self, label='Open')

        self.label_manufacturer = wx.StaticText(self, label='Manufacturer')
        self.combo_manufacturer = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY, choices=[])
        self.label_sizes = wx.StaticText(self, label='Syringe Sizes')
        self.combo_sizes = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY, choices=[])

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
        self.btn_open.Bind(wx.EVT_UPDATE_UI, self.OnUpdateOpen)
        self.combo_port.Bind(wx.EVT_COMBOBOX_DROPDOWN, self.OnPortDropDown)
        self.combo_manufacturer.Bind(wx.EVT_COMBOBOX, self.OnManufacturer)
        self.btn_save_cfg.Bind(wx.EVT_BUTTON, self.OnSaveCfg)
        self.btn_load_cfg.Bind(wx.EVT_BUTTON, self.OnLoadCfg)

    def OnUpdateOpen(self, evt):
        if self.syringe.is_open():
            lbl = 'Close'
            opened = True
            manufacturers = self.syringe.get_available_manufacturers()
            self.combo_manufacturer.Set(manufacturers)
        else:
            lbl = 'Open'
            opened = False
        self.btn_open.SetLabel(lbl)
        self.btn_open.SetValue(opened)

    def OnPortDropDown(self, evt):
        ports = get_avail_com_ports()
        self._lgr.info(f'Available com ports are {ports}')
        self.combo_port.Set(ports)

    def OnManufacturer(self, evt):
        if self.syringe.is_open():
            self.combo_sizes.clear()
            sizes = self.syringe.get_available_syringes(evt.GetSelection())
            self.combo_sizes.Set(sizes)

    def OnOpen(self, evt):
        opened = self.syringe.is_open()
        port = self.combo_port.GetStringSelection()
        baud = int(self.choice_baud.GetStringSelection())
        if not opened:
            self._lgr.debug(f'Opening syringe at {port}, {baud}')
            self.syringe.open(port, baud)
        if self.syringe.is_open():
            self.btn_open.SetLabel('Close')
        else:
            self._lgr.debug(f'Closing syringe at {port}, {baud}')
            self.btn_open.SetLabel('Open')

    def OnSaveCfg(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        section['ComPort'] = self.choice_dev.GetStringSelection()
        section['Baud'] = self.choice_line.GetStringSelection()
        LP_CFG.update_hwcfg_section(self._name, section)

    def OnLoadCfg(self, evt):
        section = LP_CFG.get_hwcfg_section(self._name)
        self.choice_dev.SetStringSelection(section['ComPort'])
        self.choice_line.SetStringSelection(section['Baud'])

class PanelSyringeControls(wx.Panel):
    def __init__(self, parent, syringe: Pump11Elite):
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
        self.btn_bolus = wx.ToggleButton(self, label='Bolus')

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

        self.sizer.Add(sizer_cfg)

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_basal.Bind(wx.EVT_BUTTON, self.OnBasal)
        self.btn_bolus.Bind(wx.EVT_BUTTON, self.OnBolus)
        self.btn_basal.Bind(wx.EVT_UPDATE_UI, self.OnUpdateBasal)
        self.btn_bolus.Bind(wx.EVT_UPDATE_UI, self.OnUpdateBolus)


    def OnUpdateBasal(self, evt):
        if not self.syringe.is_open():
            enabled = False
            label = 'Start Basal'
        else:
            if self.syringe.is_infusing:
                label = 'Stop'
                enabled = True
            else:
                label = 'Start Basal'
                enabled = False
        self.btn_basal.SetLabel(label)
        self.btn_basal.Enable(enabled)

    def OnUpdateBolus(self, evt):
        enable = self.syringe.is_open() and not self.syringe.is_infusing
        self.btn_bolus.Enable(enable)

    def OnBasal(self, evt):
        infusion_rate = self.spin_rate.GetValue()
        if self.syringe.is_infusing:
            self.syringe.stop()
        else:
            self.syringe.set_infusion_rate(infusion_rate)
            self.syringe.set_target_volume(0)
            self.syringe.start_constant_infusion()

    def OnBolus(self, evt):
        infusion_rate = self.spin_rate.GetValue()
        target_vol = self.spin_volume.GetValue()
        self.syringe.set_infusion_rate(infusion_rate)
        self.syringe.set_target_volume(target_vol)
        self.syringe.infuse_to_target_volume()


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.syringe = Pump11Elite('Example Syringe')
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
