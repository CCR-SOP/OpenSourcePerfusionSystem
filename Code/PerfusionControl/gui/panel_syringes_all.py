# -*- coding: utf-8 -*-
""" Panel for showing syringes and controlling automations related to syringes

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx
import wx.lib.colourdb
import numpy as np

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.PerfusionSystem import PerfusionSystem
from gui.panel_syringe import PanelSyringeControlsSimple, PanelSyringeControls


class PanelAllSyringes(wx.Panel):
    def __init__(self, parent, vaso, glucose, manual_syringes):
        super().__init__(parent)
        self._lgr = logging.getLogger(__name__)

        self.sizer = None

        self.auto = []
        self.auto.append(PanelVasoactive(self, vaso))
        self.auto.append(PanelGlucose(self, glucose))

        self.manual = []
        for manual in manual_syringes:
            self.manual.append(PanelSyringeControls(self, manual))

        manual_names = [manual.device.name for manual in manual_syringes]

        names = [vaso.name, vaso.dilator.name, vaso.constrictor.name,
                 glucose.name, glucose.increase.name, glucose.decrease.name]
        names.extend(manual_names)
        self._lgr.debug(f'logging to {names}')
        self.text_log = utils.create_log_display(self, logging.INFO, names)
        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        sizer_controls = wx.BoxSizer(wx.HORIZONTAL)
        sizer_auto = wx.BoxSizer(wx.VERTICAL)
        for panel in self.auto:
            sizer_auto.Add(panel, wx.SizerFlags().Proportion(1).Expand())

        sizer_manual = wx.BoxSizer(wx.VERTICAL)
        for panel in self.manual:
            sizer_manual.Add(panel, wx.SizerFlags().Proportion(1).Expand())

        sizer_controls.Add(sizer_auto, wx.SizerFlags().Proportion(3).Expand())
        sizer_controls.Add(sizer_manual, wx.SizerFlags().Proportion(1).Expand())

        self.sizer.Add(sizer_controls, wx.SizerFlags().Proportion(2).Expand())
        self.sizer.Add(self.text_log, wx.SizerFlags().Proportion(1).Expand())
        self.sizer.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.Layout()

    def __set_bindings(self):
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for panel in self.auto:
            panel.Close()


class PanelVasoactive(wx.Panel):
    def __init__(self, parent, automation):
        super().__init__(parent)
        self.automation = automation
        self.name = self.automation.name
        self._lgr = utils.get_object_logger(__name__, self.automation.name)

        wx.lib.colourdb.updateColourDB()
        self.normal_color = self.GetBackgroundColour()
        self.warning_color = wx.Colour('orange')

        font = wx.Font()
        font.SetPointSize(12)

        self.label_min_pressure = wx.StaticText(self, label='Min Arterial\nmmHg')
        self.spin_min_pressure = wx.SpinCtrlDouble(self, min=0, max=300, inc=1, initial=0)

        self.label_max_pressure = wx.StaticText(self, label='Max Arterial\nmmHg')
        self.spin_max_pressure = wx.SpinCtrlDouble(self, min=0, max=300, inc=1, initial=0)

        self.label_adjust_minutes = wx.StaticText(self, label='Update Rate\nminute')
        self.spin_adjust_minutes = wx.SpinCtrlDouble(self, min=0, max=60*60*24, inc=1, initial=5)

        self.static_box = wx.StaticBox(self, wx.ID_ANY, label=self.name, style=wx.ALIGN_CENTER_HORIZONTAL)
        self.static_box.SetFont(utils.get_header_font())
        self.sizer = wx.StaticBoxSizer(self.static_box, wx.VERTICAL)

        self.btn_save = wx.Button(self, style=wx.BU_EXACTFIT)
        self.btn_save.SetBitmapLabel(wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_BUTTON))
        self.btn_save.SetToolTip('Save Config to File')
        self.btn_load = wx.Button(self, style=wx.BU_EXACTFIT)
        self.btn_load.SetBitmapLabel(wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_BUTTON))
        self.btn_load.SetToolTip('Load Config From File')
        self.btn_update = wx.Button(self, style=wx.BU_EXACTFIT)
        self.btn_update.SetBitmapLabel(wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_BUTTON))
        self.btn_update.SetToolTip('Update Hardware with Current Displayed Config')

        self.btn_auto = wx.ToggleButton(self, label='Automate', style=wx.TE_MULTILINE)

        self.syringe_collapsible = {}
        self.syringe_collapsible['dilator'] = PanelSyringeControlsSimple(self, self.automation.dilator)
        self.syringe_collapsible['constrictor'] = PanelSyringeControlsSimple(self, self.automation.constrictor)


        self.timer_gui_update = wx.Timer(self)
        self.timer_gui_update.Start(milliseconds=500, oneShot=wx.TIMER_CONTINUOUS)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):

        sizer_adjustments = wx.BoxSizer(wx.HORIZONTAL)

        sizer_adjustments.Add(self.syringe_collapsible['constrictor'])
        sizer_adjustments.AddStretchSpacer(6)

        sizer_min = wx.BoxSizer(wx.VERTICAL)
        sizer_min.Add(self.label_min_pressure)
        sizer_min.Add(self.spin_min_pressure)

        sizer_max = wx.BoxSizer(wx.VERTICAL)
        sizer_max.Add(self.label_max_pressure)
        sizer_max.Add(self.spin_max_pressure)

        sizer_minute = wx.BoxSizer(wx.VERTICAL)
        sizer_minute.Add(self.label_adjust_minutes)
        sizer_minute.Add(self.spin_adjust_minutes)

        sizer_adjustments.Add(sizer_min, wx.SizerFlags().CenterVertical().Border(wx.RIGHT, 10))
        sizer_adjustments.Add(sizer_max, wx.SizerFlags().CenterVertical().Border(wx.RIGHT, 10))
        sizer_adjustments.Add(sizer_minute, wx.SizerFlags().CenterVertical().Border(wx.RIGHT, 10))

        sizer_buttons = wx.BoxSizer(wx.VERTICAL)
        sizer_buttons.Add(self.btn_save)
        sizer_buttons.Add(self.btn_load)
        sizer_buttons.Add(self.btn_update)
        sizer_adjustments.Add(sizer_buttons, wx.SizerFlags().CenterVertical().Border(wx.RIGHT, 10))

        sizer_adjustments.Add(self.btn_auto, wx.SizerFlags().Expand().Proportion(1).Border(wx.RIGHT, 10))

        sizer_adjustments.AddStretchSpacer(3)
        sizer_adjustments.Add(self.syringe_collapsible['dilator'])

        self.sizer.Add(sizer_adjustments, wx.SizerFlags().CenterHorizontal())

        self.sizer.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.Layout()

        self.btn_auto.SetBackgroundColour(wx.Colour(126, 202, 22))

    def __set_bindings(self):
        self.btn_auto.Bind(wx.EVT_TOGGLEBUTTON, self.on_auto)
        self.btn_save.Bind(wx.EVT_BUTTON, self.on_save)
        self.btn_load.Bind(wx.EVT_BUTTON, self.on_load)
        self.btn_update.Bind(wx.EVT_BUTTON, self.on_update)
        for pane in self.syringe_collapsible.values():
            pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_pane_changed)

    def on_pane_changed(self, evt):
        self.sizer.Layout()
        self.Layout()

    def update_controls(self):
        pass

    def warn_on_difference(self, ctrl, actual, set_value):
        old_color = ctrl.GetBackgroundColour()
        tooltip_msg = ''

        if not np.isclose(actual, set_value):
            color = self.warning_color
            tooltip_msg = f'Expected {set_value:02f}'
        else:
            color = self.normal_color

        # this prevents "blinking" text by only refreshing when somthing changes
        if old_color != color:
            ctrl.SetBackgroundColour(color)
            ctrl.Refresh()
        ctrl.SetToolTip(tooltip_msg)

    def on_auto(self, evt):
        if not self.btn_auto.GetValue():
            self.automation.stop()
            self.btn_auto.SetLabel('Automate')
            self.btn_auto.SetBackgroundColour(wx.Colour(126, 202, 22))
        else:
            self.automation.start()
            self.btn_auto.SetLabel('Switch to\nManual\nControl')
            self.btn_auto.SetBackgroundColour(wx.Colour(113, 182, 20))
        self.Refresh()
        for pane in self.syringe_collapsible.values():
            pane.Enable(not self.btn_auto.GetValue())

    def update_config_from_controls(self):
        self.automation.cfg.pressure_mmHg_min = self.spin_min_pressure.GetValue()
        self.automation.cfg.pressure_mmHg_max = self.spin_max_pressure.GetValue()
        self.automation.cfg.update_rate_minute = self.spin_adjust_minutes.GetValue()

    def update_controls_from_config(self):
        self._lgr.debug(f'min pressure is {self.automation.cfg.pressure_mmHg_min}')
        self.spin_min_pressure.SetValue(self.automation.cfg.pressure_mmHg_min)
        self.spin_max_pressure.SetValue(self.automation.cfg.pressure_mmHg_max)
        self.spin_adjust_minutes.SetValue(self.automation.cfg.update_rate_minute)

    def on_save(self, evt):
        self.update_config_from_controls()
        self.automation.write_config()

    def on_load(self, evt):
        self.automation.read_config()
        self.update_controls_from_config()

    def on_update(self, evt):
        self.update_controls_from_config()

    def OnClose(self, evt):
        self.timer_gui_update.Stop()


class PanelGlucose(wx.Panel):
    def __init__(self, parent, automation):
        super().__init__(parent)
        self.automation = automation
        self.name = self.automation.name
        self._lgr = utils.get_object_logger(__name__, self.automation.name)

        wx.lib.colourdb.updateColourDB()
        self.normal_color = self.GetBackgroundColour()
        self.warning_color = wx.Colour('orange')

        font = wx.Font()
        font.SetPointSize(12)

        self.label_min_glucose = wx.StaticText(self, label='Min Glucose\n')
        self.spin_min_glucose = wx.SpinCtrlDouble(self, min=0, max=1000, inc=1, initial=0)

        self.label_max_glucose = wx.StaticText(self, label='Max Glucose\n')
        self.spin_max_glucose = wx.SpinCtrlDouble(self, min=0, max=1000, inc=1, initial=0)

        self.label_adjust_minutes = wx.StaticText(self, label='Update Rate\nminute')
        self.spin_adjust_minutes = wx.SpinCtrlDouble(self, min=0, max=60*60*24, inc=1, initial=5)

        self.static_box = wx.StaticBox(self, wx.ID_ANY, label=self.name, style=wx.ALIGN_CENTER_HORIZONTAL)
        self.static_box.SetFont(utils.get_header_font())
        self.sizer = wx.StaticBoxSizer(self.static_box, wx.VERTICAL)

        self.btn_save = wx.Button(self, style=wx.BU_EXACTFIT)
        self.btn_save.SetBitmapLabel(wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_BUTTON))
        self.btn_save.SetToolTip('Save Config to File')
        self.btn_load = wx.Button(self, style=wx.BU_EXACTFIT)
        self.btn_load.SetBitmapLabel(wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_BUTTON))
        self.btn_load.SetToolTip('Load Config From File')
        self.btn_update = wx.Button(self, style=wx.BU_EXACTFIT)
        self.btn_update.SetBitmapLabel(wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_BUTTON))
        self.btn_update.SetToolTip('Update Hardware with Current Displayed Config')

        self.btn_auto = wx.ToggleButton(self, label='Automate\n')

        self.syringe_collapsible = {}
        self.syringe_collapsible['increase'] = PanelSyringeControlsSimple(self, self.automation.increase)
        self.syringe_collapsible['decrease'] = PanelSyringeControlsSimple(self, self.automation.decrease)

        self.timer_gui_update = wx.Timer(self)
        self.timer_gui_update.Start(milliseconds=500, oneShot=wx.TIMER_CONTINUOUS)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):

        sizer_adjustments = wx.BoxSizer(wx.HORIZONTAL)

        sizer_adjustments.Add(self.syringe_collapsible['decrease'])
        sizer_adjustments.AddStretchSpacer(7)

        sizer_min = wx.BoxSizer(wx.VERTICAL)
        sizer_min.Add(self.label_min_glucose)
        sizer_min.Add(self.spin_min_glucose)

        sizer_max = wx.BoxSizer(wx.VERTICAL)
        sizer_max.Add(self.label_max_glucose)
        sizer_max.Add(self.spin_max_glucose)

        sizer_minute = wx.BoxSizer(wx.VERTICAL)
        sizer_minute.Add(self.label_adjust_minutes)
        sizer_minute.Add(self.spin_adjust_minutes)

        sizer_adjustments.Add(sizer_min, wx.SizerFlags().CenterVertical().Border(wx.RIGHT, 10))
        sizer_adjustments.Add(sizer_max, wx.SizerFlags().CenterVertical().Border(wx.RIGHT, 10))
        sizer_adjustments.Add(sizer_minute, wx.SizerFlags().CenterVertical().Border(wx.RIGHT, 10))

        sizer_buttons = wx.BoxSizer(wx.VERTICAL)
        sizer_buttons.Add(self.btn_save)
        sizer_buttons.Add(self.btn_load)
        sizer_buttons.Add(self.btn_update)
        sizer_adjustments.Add(sizer_buttons, wx.SizerFlags().CenterVertical().Border(wx.RIGHT, 10))

        sizer_adjustments.Add(self.btn_auto, wx.SizerFlags().Expand().Proportion(1).Border(wx.RIGHT, 10))

        sizer_adjustments.AddStretchSpacer(3)
        sizer_adjustments.Add(self.syringe_collapsible['increase'])

        self.sizer.Add(sizer_adjustments, wx.SizerFlags().CenterHorizontal())

        self.sizer.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.Layout()

        self.btn_auto.SetBackgroundColour(wx.Colour(126, 202, 22))

    def __set_bindings(self):
        self.btn_auto.Bind(wx.EVT_TOGGLEBUTTON, self.on_auto)
        self.btn_save.Bind(wx.EVT_BUTTON, self.on_save)
        self.btn_load.Bind(wx.EVT_BUTTON, self.on_load)
        self.btn_update.Bind(wx.EVT_BUTTON, self.on_update)
        for pane in self.syringe_collapsible.values():
            pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_pane_changed)

    def on_pane_changed(self, evt):
        self.sizer.Layout()
        self.Layout()

    def on_auto(self, evt):
        if not self.btn_auto.GetValue():
            self.automation.stop()
            self.btn_auto.SetLabel('Automate')
            self.btn_auto.SetBackgroundColour(wx.Colour(126, 202, 22))
        else:
            self.automation.start()
            self.btn_auto.SetLabel('Switch to\nManual\nControl')
            self.btn_auto.SetBackgroundColour(wx.Colour(113, 182, 20))

        self.Refresh()
        for pane in self.syringe_collapsible.values():
            pane.Enable(not self.btn_auto.GetValue())

    def update_controls(self):
        pass

    def warn_on_difference(self, ctrl, actual, set_value):
        old_color = ctrl.GetBackgroundColour()
        tooltip_msg = ''

        if not np.isclose(actual, set_value):
            color = self.warning_color
            tooltip_msg = f'Expected {set_value:02f}'
        else:
            color = self.normal_color

        # this prevents "blinking" text by only refreshing when somthing changes
        if old_color != color:
            ctrl.SetBackgroundColour(color)
            ctrl.Refresh()
        ctrl.SetToolTip(tooltip_msg)

    def update_config_from_controls(self):
        self.automation.cfg.glucose_min = self.spin_min_glucose.GetValue()
        self.automation.cfg.glucose_max = self.spin_max_glucose.GetValue()
        self.automation.cfg.update_rate_minute = self.spin_adjust_minutes.GetValue()

    def update_controls_from_config(self):
        self.spin_min_glucose.SetValue(self.automation.cfg.glucose_min)
        self.spin_max_glucose.SetValue(self.automation.cfg.glucose_max)
        self.spin_adjust_minutes.SetValue(self.automation.cfg.update_rate_minute)

    def on_save(self, evt):
        self.update_config_from_controls()
        self.automation.write_config()

    def on_load(self, evt):
        self.automation.read_config()
        self.update_controls_from_config()

    def on_update(self, evt):
        self.update_controls_from_config()

    def OnClose(self, evt):
        self.timer_gui_update.Stop()


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        vaso = SYS_PERFUSION.get_automation('Vasoactive Automation')
        glucose = SYS_PERFUSION.get_automation('Glucose Automation')
        manual = [SYS_PERFUSION.get_automation('Solumed Manual'),
                  SYS_PERFUSION.get_automation('TPN + Bile Salts Manual'),
                  SYS_PERFUSION.get_automation('Zosyn Manual')]

        self.panel_syringes = PanelAllSyringes(self, vaso, glucose, manual)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel_syringes.Close()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None)
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('panel_syringes_all', logging.DEBUG)

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
