# -*- coding: utf-8 -*-
""" Panels for controlling configuration settings

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import wx


class AutomationConfig(wx.CollapsiblePane):
    def __init__(self, parent, automation):
        super().__init__(parent, label=automation.name)
        self._lgr = logging.getLogger(__name__)
        self.automation = automation

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.spin_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_update = wx.Button(self.GetPane(), label='Update Automation')
        self.btn_load = wx.Button(self.GetPane(), label='Load From Config')
        self.btn_save = wx.Button(self.GetPane(), label='Save From Config')
        self.btn_save.Enable(False)
        self.btn_update.Enable(False)

        self.labels = {}
        self.spins = {}

        self.change_detected = False

    def add_var(self, config_name, lbl_name, limits, decimal_places=0):
        self.labels[config_name] = wx.StaticText(self.GetPane(), label=lbl_name)
        self.spins[config_name] = wx.SpinCtrlDouble(self.GetPane(),
                                                    min=limits[0], max=limits[2], inc=limits[1],
                                                    initial=getattr(self.automation.cfg, config_name))
        self.spins[config_name].SetDigits(decimal_places)

    def add_range(self, config_name, lbl_name, limits, decimal_places=0):
        cfg_name = f'{config_name}_min'
        self.labels[cfg_name] = wx.StaticText(self.GetPane(), label=f'{lbl_name} min')
        self.spins[cfg_name] = wx.SpinCtrlDouble(self.GetPane(),
                                                 min=limits[0], max=limits[2], inc=limits[1],
                                                 initial=getattr(self.automation.cfg, config_name)[0])
        self.spins[cfg_name].SetDigits(decimal_places)

        cfg_name = f'{config_name}_max'
        self.labels[cfg_name] = wx.StaticText(self.GetPane(), label=f'{lbl_name} max')
        self.spins[cfg_name] = wx.SpinCtrlDouble(self.GetPane(),
                                                 min=limits[0], max=limits[2], inc=limits[1],
                                                 initial=getattr(self.automation.cfg, config_name)[1])
        self.spins[cfg_name].SetDigits(decimal_places)

    def do_layout(self):
        flags = wx.SizerFlags(1).Expand().Border(wx.ALL, 2)
        for label in self.labels.values():
            self.label_sizer.Add(label, flags)

        for spin in self.spins.values():
            self.spin_sizer.Add(spin, flags)

        self.sizer.Add(self.label_sizer, flags)
        self.sizer.Add(self.spin_sizer, flags)

        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        btnsizer.Add(self.btn_update, flags)
        btnsizer.Add(self.btn_load, flags)
        btnsizer.Add(self.btn_save, flags)
        self.sizer.Add(btnsizer, flags)

        self.sizer.SetSizeHints(self.GetParent())
        self.GetPane().SetSizer(self.sizer)
        self.Fit()
        self.Layout()

    def set_bindings(self):
        self.btn_update.Bind(wx.EVT_BUTTON, self.on_update)
        self.btn_load.Bind(wx.EVT_BUTTON, self.on_load_cfg)
        self.btn_save.Bind(wx.EVT_BUTTON, self.on_save_cfg)
        for spin in self.spins.values():
            spin.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_change)

    def on_change(self, evt):
        evt.GetEventObject().SetBackgroundColour(wx.RED)
        self.btn_update.Enable(True)
        self.btn_save.Enable(True)

    def on_update(self, evt):
        self.update_config_from_controls()
        self.clear_backgrounds()
        self.btn_update.Enable(False)

    def update_config_from_controls(self):
        for cfg_name, ctrl in self.spins.items():
            setattr(self.automation.cfg, cfg_name, ctrl.GetValue())

    def update_controls_from_config(self):
        try:
            for cfg_name, ctrl in self.spins.items():
                ctrl.SetValue(str(getattr(self.automation.cfg, cfg_name)))
        except AttributeError:
            # this should only happen if the hardware didn't load
            pass

    def on_save_cfg(self, evt):
        self.update_config_from_controls()
        self.automation.write_config()
        self.btn_save.Enable(False)
        self.clear_backgrounds()

    def on_load_cfg(self, evt):
        self.automation.read_config()
        self.update_controls_from_config()
        self.btn_save.Enable(False)
        self.btn_update.Enable(False)
        self.clear_backgrounds()

    def clear_backgrounds(self):
        for spin in self.spins.values():
            spin.SetBackgroundColour(wx.WHITE)
            spin.Refresh()

