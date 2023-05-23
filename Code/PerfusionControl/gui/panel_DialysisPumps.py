# -*- coding: utf-8 -*-
""" Application to display dialysis pump controls

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from gui.panel_DC import PanelDC
from pyPerfusion.PerfusionSystem import PerfusionSystem


class DialysisPumpPanel(wx.Panel):
    def __init__(self, parent, automations):
        super().__init__(parent)
        self._lgr = logging.getLogger(__name__)
        self.automations = automations

        font = wx.Font()
        font.SetPointSize(int(16))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.static_box = wx.StaticBox(self, wx.ID_ANY, label="Roller Pumps")
        self.static_box.SetFont(font)

        # self.wrapper = wx.StaticBoxSizer(self.static_box, wx.HORIZONTAL)
        self.gridsizer = wx.GridSizer(rows=2, cols=2, vgap=5, hgap=5)

        self.panels = []
        self.configs = []
        for automation in automations:
            panel = PanelDC(self, automation.pump)
            self.panels.append(panel)
            if automation.name == 'Dialysate Inflow Automation':
                self.configs.append(DialysateInflowConfig(self, automation))
            elif automation.name == 'Dialysate Outflow Automation':
                self.configs.append(DialysateOutflowConfig(self, automation))
            elif automation.name == 'Dialysis Blood Automation':
                self.configs.append(DialysisBloodConfig(self, automation))

        # Add log
        log_names = []
        for automation in self.automations:
            log_names.append(automation.pump.name)
        log_names.append('AutoDialysis')
        self.text_log_roller_pumps = utils.create_log_display(self, logging.INFO, log_names, use_last_name=True)

        # Add auto start button
        self.btn_auto_dialysis = wx.Button(self, label='Start Auto Dialysis')
        self.btn_auto_dialysis.SetFont(font)
        self.btn_auto_dialysis.SetBackgroundColour(wx.Colour(0, 240, 0))

        self.__do_layout()
        self.__set_bindings()

    def close(self):
        for panel in self.panels:
            panel.close()
        super().Close()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border(wx.ALL, 1)

        configsizer = wx.BoxSizer(wx.HORIZONTAL)
        for config in self.configs:
            configsizer.Add(config, flags)

        for idx, panel in enumerate(self.panels):
            self.gridsizer.Add(panel, flags=flags)
        self.gridsizer.Add(self.btn_auto_dialysis, flags)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(configsizer, flags=flags.Proportion(0))
        sizer.Add(self.text_log_roller_pumps, flags=flags.Proportion(2))

        self.sizer.Add(self.gridsizer, flags=flags.Proportion(1))
        self.sizer.Add(sizer, flags=flags)

        self.sizer.SetSizeHints(self.GetParent())
        self.SetSizer(self.sizer)
        self.Fit()
        self.Layout()

    def __set_bindings(self):
        self.btn_auto_dialysis.Bind(wx.EVT_BUTTON, self.on_auto)
        for pane in self.configs:
            pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_pane_changed)

    def on_auto(self, evt):
        if self.btn_auto_dialysis.GetLabel() == "Start Auto Dialysis":
            self.btn_auto_dialysis.SetLabel("Stop Auto Dialysis")
            self.btn_auto_dialysis.SetBackgroundColour(wx.Colour(240, 0, 0))
            for automation in self.automations:
                automation.start()
            for panel in self.panels:
                panel.panel_dc.entered_offset.Enable(False)
        else:
            self.btn_auto_dialysis.SetLabel("Start Auto Dialysis")
            self.btn_auto_dialysis.SetBackgroundColour(wx.Colour(0, 240, 0))
            for automation in self.automations:
                automation.stop()
            for panel in self.panels:
                panel.panel_dc.entered_offset.Enable(True)

    def on_pane_changed(self, evt):
        self.sizer.Layout()
        self.Layout()


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

        self.add_var('adjust_rate_ms', 'Adjust Rate (ms)', (0, 60*1_000, 60*60*1_000))
        self.add_var('adjust_percent', 'Flow Adjust (ml/min)', (0, 1, 100))

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


class DialysateInflowConfig(AutomationConfig):
    def __init__(self, parent, automation):
        super().__init__(parent, automation)

        self.add_var('K_min', 'K (min)', limits=(0, 1, 10))
        self.add_var('K_max', 'K (max)', limits=(0, 1, 10))

        self.do_layout()
        self.set_bindings()


class DialysateOutflowConfig(AutomationConfig):
    def __init__(self, parent, automation):
        super().__init__(parent, automation)

        self.add_var('K_min', 'K (min)', limits=(0, 1, 10))
        self.add_var('K_max', 'K (max)', limits=(0, 1, 10))
        self.add_var('hct_min', 'hct (min)', limits=(0, 1, 10))
        self.add_var('hct_max', 'hct (max)', limits=(0, 1, 10))

        self.do_layout()
        self.set_bindings()


class DialysisBloodConfig(AutomationConfig):
    def __init__(self, parent, automation):
        super().__init__(parent, automation)
        self.do_layout()


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        automation_names = ['Dialysate Inflow Automation',
                            'Dialysate Outflow Automation',
                            'Dialysis Blood Automation']
        automations = []
        for name in automation_names:
            automations.append(SYS_PERFUSION.get_automation(name))
        self.panel = DialysisPumpPanel(self, automations)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel.close()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None)
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('panel_DialysisPumps', logging.DEBUG)

    SYS_PERFUSION = PerfusionSystem()
    try:
        SYS_PERFUSION.open()
        SYS_PERFUSION.load_all()
        SYS_PERFUSION.load_automations()
    except Exception as e:
        # if anything goes wrong loading the perfusion system
        # close the hardware and exit the program
        SYS_PERFUSION.close()
        raise e

    app = MyTestApp(0)
    app.MainLoop()
    SYS_PERFUSION.close()
