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
from gui.panel_syringe import PanelSyringeControlsSimple


class PanelAllSyringes(wx.Panel):
    def __init__(self, parent, automations):
        super().__init__(parent)
        self._lgr = logging.getLogger(__name__)

        self.panels = []
        self.configs = []
        for automation in automations:
            panel = BaseGasMixerPanel(self, automation)
            self.panels.append(panel)
            if automation.name == 'Arterial Gas Mixer Automation':
                panel.config.add_var('pH_min', 'pH (min)', limits=(0, 0.01, 14), decimal_places=2)
                panel.config.add_var('pH_max', 'pH (max)', limits=(0, 0.01, 14), decimal_places=2)
                panel.config.add_var('CO2_min', 'CO2 (min)', limits=(0, 1, 100))
                panel.config.add_var('CO2_max', 'CO2 (max)', limits=(0, 1, 100))
                panel.config.add_var('O2_min', 'O2 (min)', limits=(0, 1, 100))
                panel.config.add_var('O2_max', 'O2 (max)', limits=(0, 1, 100))
                panel.config.do_layout()
                panel.config.set_bindings()
            elif automation.name == 'Venous Gas Mixer Automation':
                panel.config.add_var('pH_min', 'pH (min)', limits=(0, 1, 14), decimal_places=2)
                panel.config.add_var('pH_max', 'pH (max)', limits=(0, 1, 14), decimal_places=2)
                panel.config.add_var('O2_min', 'O2 (min)', limits=(0, 1, 100))
                panel.config.add_var('O2_max', 'O2 (max)', limits=(0, 1, 100))
                panel.config.do_layout()
                panel.config.set_bindings()
        self.static_box = wx.StaticBox(self, wx.ID_ANY, label="Gas Mixers")
        self.wrapper = wx.StaticBoxSizer(self.static_box, wx.VERTICAL)

        # self.text_log_arterial = utils.create_log_display(self, logging.INFO, ['Arterial Gas Mixer'])
        # self.text_log_venous = utils.create_log_display(self, logging.INFO, ['Venous Gas Mixer'])

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()

        self.wrapper.Add(self.panels[0], flags.Proportion(1))
        self.wrapper.Add(self.panels[1], flags.Proportion(1))

        self.wrapper.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.SetSizer(self.wrapper)
        self.Layout()

    def __set_bindings(self):
        self.Bind(wx.EVT_CLOSE, self.OnClose)


    def OnClose(self, evt):
        for panel in self.panels:
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
        self.spin_min_pressure = wx.SpinCtrlDouble(self, min=0, max=14, inc=0.1, initial=7.0)

        self.label_max_pressure = wx.StaticText(self, label='Max Arterial\nmmHg')
        self.spin_max_pressure = wx.SpinCtrlDouble(self, min=0, max=14, inc=0.1, initial=7.0)

        self.label_adjust_minutes = wx.StaticText(self, label='Update Rate\nminute')
        self.spin_adjust_minutes = wx.SpinCtrlDouble(self, min=0, max=60*60*24, inc=1, initial=5)

        self.static_box = wx.StaticBox(self, wx.ID_ANY, label=self.name, style=wx.ALIGN_CENTER_HORIZONTAL)
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

        self.btn_auto = wx.ToggleButton(self, label='Automate')

        self.syringe_collapsible = {}
        self.syringe_collapsible['dilator'] = PanelSyringeControlsSimple(self, self.automation.dilator)
        self.syringe_collapsible['constrictor'] = PanelSyringeControlsSimple(self, self.automation.constrictor)
        self.text_log = utils.create_log_display(self, logging.INFO,
                                                 [self.automation.name, self.automation.dilator.name,
                                                  self.automation.constrictor.name])

        self.timer_gui_update = wx.Timer(self)
        self.timer_gui_update.Start(milliseconds=500, oneShot=wx.TIMER_CONTINUOUS)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):

        sizer_adjustments = wx.BoxSizer(wx.HORIZONTAL)

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

        sizer_adjustments.Add(self.btn_auto, wx.SizerFlags().Expand().Border(wx.RIGHT, 10))

        sizer_manual = wx.BoxSizer(wx.VERTICAL)
        sizer_manual.Add(self.syringe_collapsible['constrictor'])
        sizer_manual.Add(self.syringe_collapsible['dilator'])

        sizer_adjustments.Add(sizer_manual, wx.SizerFlags().Expand())

        self.sizer.Add(sizer_adjustments, wx.SizerFlags().CenterHorizontal())
        self.sizer.Add(self.text_log, wx.SizerFlags().Expand().Proportion(1))

        self.sizer.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.Layout()

        self.update_controls_from_hardware()

    def __set_bindings(self):
        self.Bind(wx.EVT_TIMER, self.update_controls_from_hardware, self.timer_gui_update)
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

    def update_controls_from_hardware(self, evt=None):
        pass

    def OnClose(self, evt):
        self.timer_gui_update.Stop()


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        automation_names = ['Vasoactive Automation']
        self.panels = []
        for name in automation_names:
            automation = SYS_PERFUSION.get_automation(name)
            self.panels.append(PanelVasoactive(self, automation))
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for panel in self.panels:
            panel.Close()
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
