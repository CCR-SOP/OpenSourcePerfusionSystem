# -*- coding: utf-8 -*-
"""

@author: Allen Luna

Basic code for controlling centrifugal and dialysis pumps via Analog Output
"""
import wx

from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyPerfusion.panel_AO import PanelAO

devices = ['Hepatic Artery Centrifugal Pump', 'Portal Vein Centrifugal Pump', 'Perfusate Pump', 'Dialysate Pump']


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=2)

        self._panel = []
        HA_panel = PanelAO(self, NIDAQ_AO(), devices[0])
        HA_panel._panel_cfg.choice_dev.SetStringSelection('Dev3')
        HA_panel._panel_cfg.choice_dev.Enable(False)
        HA_panel._panel_cfg.choice_line.SetStringSelection('1')
        HA_panel._panel_cfg.choice_line.Enable(False)
        sizer.Add(HA_panel, 1, wx.ALL | wx.EXPAND, border=1)
        self._panel.append(HA_panel)

        PV_panel = PanelAO(self, NIDAQ_AO(), devices[1])
        PV_panel._panel_cfg.choice_dev.SetStringSelection('Dev3')
        PV_panel._panel_cfg.choice_dev.Enable(False)
        PV_panel._panel_cfg.choice_line.SetStringSelection('0')
        PV_panel._panel_cfg.choice_line.Enable(False)
        sizer.Add(PV_panel, 1, wx.ALL | wx.EXPAND, border=1)
        self._panel.append(PV_panel)

        Perfusate_panel = PanelAO(self, NIDAQ_AO(), devices[2])
        Perfusate_panel._panel_cfg.choice_dev.SetStringSelection('Dev2')
        Perfusate_panel._panel_cfg.choice_dev.Enable(False)
        Perfusate_panel._panel_cfg.choice_line.SetStringSelection('0')
        Perfusate_panel._panel_cfg.choice_line.Enable(False)
        Perfusate_panel._panel_settings.lbl_offset.SetLabel('Desired Flow (ml/min)')
        Perfusate_panel._panel_settings.spin_offset.SetMax(100)
        sizer.Add(Perfusate_panel, 1, wx.ALL | wx.EXPAND, border=1)
        self._panel.append(Perfusate_panel)

        Dialysate_panel = PanelAO(self, NIDAQ_AO(), devices[3])
        Dialysate_panel._panel_cfg.choice_dev.SetStringSelection('Dev2')
        Dialysate_panel._panel_cfg.choice_dev.Enable(False)
        Dialysate_panel._panel_cfg.choice_line.SetStringSelection('1')
        Dialysate_panel._panel_cfg.choice_line.Enable(False)
        Dialysate_panel._panel_settings.lbl_offset.SetLabel('Desired Flow (ml/min)')
        Dialysate_panel._panel_settings.spin_offset.SetMax(100)
        sizer.Add(Dialysate_panel, 1, wx.ALL | wx.EXPAND, border=1)
        self._panel.append(Dialysate_panel)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for panel in self._panel:
            panel.close()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


app = MyTestApp(0)
app.MainLoop()
