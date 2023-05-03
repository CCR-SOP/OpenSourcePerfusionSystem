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
        self._lgr = logging.getLogger(__name__)
        wx.Panel.__init__(self, parent)
        self.automations = automations

        font = wx.Font()
        font.SetPointSize(int(16))
        static_box = wx.StaticBox(self, wx.ID_ANY, label="Roller Pumps")
        static_box.SetFont(font)
        self.wrapper = wx.StaticBoxSizer(static_box, wx.VERTICAL)
        self.sizer = wx.GridSizer(cols=2)

        self.panels = []
        for automation in automations:
            panel = PanelDC(self, automation.pump)
            self.panels.append(panel)

        # Add auto start button as 5th panel
        self.btn_auto_dialysis = wx.Button(self, label='Start Auto Dialysis')
        self.btn_auto_dialysis.SetFont(font)
        self.btn_auto_dialysis.SetBackgroundColour(wx.Colour(0, 240, 0))

        log_names = []
        for automation in self.automations:
            log_names.append(automation.pump.name)
        log_names.append('AutoDialysis')
        self.text_log_roller_pumps = utils.create_log_display(self, logging.INFO, log_names, use_last_name=True)
        self.panels.append(self.text_log_roller_pumps)

        self.__do_layout()
        self.__set_bindings()

    def close(self):
        counter = 0
        for panel in self.panels:
            if counter == 3:  # to close text box
                panel.Close()
            else:
                panel.close()
            counter += 1
        super().Close()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()

        for panel in self.panels:
            self.sizer.Add(panel, flags)

        self.sizer.SetSizeHints(self.GetParent())
        self.wrapper.Add(self.sizer, flags.Proportion(1))
        self.wrapper.Add(self.btn_auto_dialysis, wx.SizerFlags().Border())
        self.SetAutoLayout(True)
        self.SetSizer(self.wrapper)
        self.Layout()

    def __set_bindings(self):
        self.btn_auto_dialysis.Bind(wx.EVT_BUTTON, self.on_auto)

    def on_auto(self, evt):
        if self.btn_auto_dialysis.GetLabel() == "Start Auto Dialysis":
            self.btn_auto_dialysis.SetLabel("Stop Auto Dialysis")
            self.btn_auto_dialysis.SetBackgroundColour(wx.Colour(240, 0, 0))
            for automation in self.automations:
                automation.start()
            counter = 0
            for panel in self.panels:
                if counter == 3:
                    pass
                else:
                    panel.panel_dc.entered_offset.Enable(False)
                counter += 1
        else:
            self.btn_auto_dialysis.SetLabel("Start Auto Dialysis")
            self.btn_auto_dialysis.SetBackgroundColour(wx.Colour(0, 240, 0))
            for automation in self.automations:
                automation.stop()
            counter = 0
            for panel in self.panels:
                if counter == 3:
                    pass
                else:
                    panel.panel_dc.entered_offset.Enable(True)
                counter += 1


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)

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
    lgr = logging.getLogger()
    PerfusionConfig.set_test_config()
    # utils.setup_stream_logger(lgr, logging.DEBUG)
    utils.setup_file_logger(lgr, logging.DEBUG, 'panel_DialysisPumps')

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
