# -*- coding: utf-8 -*-
""" Panels for controlling configuration settings

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import wx


class ConfigGUI(wx.CollapsiblePane):
    def __init__(self, parent, target_object, pane_label:str = None):
        if pane_label is None:
            pane_label = target_object.name
        super().__init__(parent, label=pane_label)
        self._lgr = logging.getLogger(__name__)
        self.target_object = target_object

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_save = wx.Button(self.GetPane(), style=wx.BU_EXACTFIT)
        self.btn_save.SetBitmapLabel(wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_BUTTON))
        self.btn_save.SetToolTip('Save Config to File')
        self.btn_load = wx.Button(self.GetPane(), style=wx.BU_EXACTFIT)
        self.btn_load.SetBitmapLabel(wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_BUTTON))
        self.btn_load.SetToolTip('Load Config From File')
        self.btn_update = wx.Button(self.GetPane(), style=wx.BU_EXACTFIT)
        self.btn_update.SetBitmapLabel(wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_BUTTON))
        self.btn_update.SetToolTip('Update Hardware with Current Displayed Config')

        self.labels = {}
        self.spins = {}

        self.change_detected = False

    def add_var(self, config_name, lbl_name, limits, decimal_places=0):
        self.labels[config_name] = wx.StaticText(self.GetPane(), label=lbl_name)
        self.spins[config_name] = wx.SpinCtrlDouble(self.GetPane(),
                                                    min=limits[0], max=limits[2], inc=limits[1],
                                                    initial=getattr(self.target_object.cfg, config_name))
        self.spins[config_name].SetDigits(decimal_places)

    def add_range(self, config_name, lbl_name, limits, decimal_places=0):
        cfg_name = f'{config_name}_min'
        self.labels[cfg_name] = wx.StaticText(self.GetPane(), label=f'{lbl_name} min')
        self.spins[cfg_name] = wx.SpinCtrlDouble(self.GetPane(),
                                                 min=limits[0], max=limits[2], inc=limits[1],
                                                 initial=getattr(self.target_object.cfg, config_name)[0])
        self.spins[cfg_name].SetDigits(decimal_places)

        cfg_name = f'{config_name}_max'
        self.labels[cfg_name] = wx.StaticText(self.GetPane(), label=f'{lbl_name} max')
        self.spins[cfg_name] = wx.SpinCtrlDouble(self.GetPane(),
                                                 min=limits[0], max=limits[2], inc=limits[1],
                                                 initial=getattr(self.target_object.cfg, config_name)[1])
        self.spins[cfg_name].SetDigits(decimal_places)

    def do_layout(self):
        self.sizer = wx.WrapSizer(wx.HORIZONTAL)

        for label, spin in zip(self.labels.values(), self.spins.values()):
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(label, wx.SizerFlags().CenterHorizontal())
            sizer.Add(spin, wx.SizerFlags().CenterHorizontal())
            self.sizer.Add(sizer, wx.SizerFlags().CenterVertical().Border(wx.RIGHT, 10))

        sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_buttons.Add(self.btn_save, wx.SizerFlags().Expand())
        sizer_buttons.Add(self.btn_load, wx.SizerFlags().Expand())
        sizer_buttons.Add(self.btn_update, wx.SizerFlags().Expand())

        self.sizer.AddSpacer(2)
        self.sizer.Add(sizer_buttons, wx.SizerFlags().Expand())

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
            setattr(self.target_object.cfg, cfg_name, ctrl.GetValue())

    def update_controls_from_config(self):
        try:
            for cfg_name, ctrl in self.spins.items():
                ctrl.SetValue(str(getattr(self.target_object.cfg, cfg_name)))
        except AttributeError:
            # this should only happen if the hardware didn't load
            pass

    def on_save_cfg(self, evt):
        self.update_config_from_controls()
        self.target_object.write_config()
        self.btn_save.Enable(False)
        self.clear_backgrounds()

    def on_load_cfg(self, evt):
        self.target_object.read_config()
        self.update_controls_from_config()
        self.btn_save.Enable(False)
        self.btn_update.Enable(False)
        self.clear_backgrounds()

    def clear_backgrounds(self):
        for spin in self.spins.values():
            spin.SetBackgroundColour(wx.WHITE)
            spin.Refresh()

