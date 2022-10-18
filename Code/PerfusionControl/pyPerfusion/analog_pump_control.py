# -*- coding: utf-8 -*-
"""

@author: Allen Luna

Basic code for controlling centrifugal and dialysis pumps via Analog Output
"""
import wx
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyPerfusion.panel_AO import PanelAO

devices = ['Hepatic Artery Centrifugal Pump', 'Portal Vein Centrifugal Pump', 'Dialysis Blood Pump', 'Dialysate Inflow Pump', 'Dialysate Outflow Pump']


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=3)

        self._panel = []
        HA_panel = PanelAO(self, NIDAQ_AO(), devices[0])
        section = PerfusionConfig.read_section('hardware', devices[0])
        dev = section['Device']
        line = section['LineName']
        HA_panel._panel_cfg.choice_dev.SetStringSelection(dev)
        HA_panel._panel_cfg.choice_dev.Enable(False)
        HA_panel._panel_cfg.choice_line.SetStringSelection(line)
        HA_panel._panel_cfg.choice_line.Enable(False)
        sizer.Add(HA_panel, 1, wx.ALL | wx.EXPAND, border=1)
        self._panel.append(HA_panel)

        PV_panel = PanelAO(self, NIDAQ_AO(), devices[1])
        section = PerfusionConfig.read_section('hardware', devices[1])
        dev = section['Device']
        line = section['LineName']
        PV_panel._panel_cfg.choice_dev.SetStringSelection(dev)
        PV_panel._panel_cfg.choice_dev.Enable(False)
        PV_panel._panel_cfg.choice_line.SetStringSelection(line)
        PV_panel._panel_cfg.choice_line.Enable(False)
        sizer.Add(PV_panel, 1, wx.ALL | wx.EXPAND, border=1)
        self._panel.append(PV_panel)

        Perfusate_panel = PanelAO(self, NIDAQ_AO(), devices[2])
        section = PerfusionConfig.read_section('hardware', devices[2])
        dev = section['Device']
        line = section['LineName']
        Perfusate_panel._panel_cfg.choice_dev.SetStringSelection(dev)
        Perfusate_panel._panel_cfg.choice_dev.Enable(False)
        Perfusate_panel._panel_cfg.choice_line.SetStringSelection(line)
        Perfusate_panel._panel_cfg.choice_line.Enable(False)
        sizer.Add(Perfusate_panel, 1, wx.ALL | wx.EXPAND, border=1)
        self._panel.append(Perfusate_panel)

        Dialysate_inflow_panel = PanelAO(self, NIDAQ_AO(), devices[3])
        section = PerfusionConfig.read_section('hardware', devices[3])
        dev = section['Device']
        line = section['LineName']
        Dialysate_inflow_panel._panel_cfg.choice_dev.SetStringSelection(dev)
        Dialysate_inflow_panel._panel_cfg.choice_dev.Enable(False)
        Dialysate_inflow_panel._panel_cfg.choice_line.SetStringSelection(line)
        Dialysate_inflow_panel._panel_cfg.choice_line.Enable(False)
        sizer.Add(Dialysate_inflow_panel, 1, wx.ALL | wx.EXPAND, border=1)
        self._panel.append(Dialysate_inflow_panel)

        Dialysate_outflow_panel = PanelAO(self, NIDAQ_AO(), devices[4])
        section = PerfusionConfig.read_section('hardware', devices[4])
        dev = section['Device']
        line = section['LineName']
        Dialysate_outflow_panel._panel_cfg.choice_dev.SetStringSelection(dev)
        Dialysate_outflow_panel._panel_cfg.choice_dev.Enable(False)
        Dialysate_outflow_panel._panel_cfg.choice_line.SetStringSelection(line)
        Dialysate_outflow_panel._panel_cfg.choice_line.Enable(False)
        sizer.Add(Dialysate_outflow_panel, 1, wx.ALL | wx.EXPAND, border=1)
        self._panel.append(Dialysate_outflow_panel)

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

if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging(filename='panel_gb100_saturation_monitor')
    app = MyTestApp(0)
    app.MainLoop()
