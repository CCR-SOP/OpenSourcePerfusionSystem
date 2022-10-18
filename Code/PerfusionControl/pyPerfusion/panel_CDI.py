"""Panel class for configuring CDI saturation monitor

@project: Liver Perfusion, NIH
@author: Stephie Lux, NIH

JUST COPIED FROM OLD pyCDI FILE - NOT UPDATED

"""
from enum import Enum
import wx
import logging
import time
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as LP_CFG
import serial
import serial.tools.list_ports

from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.FileStrategy import StreamToFile

utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
utils.configure_matplotlib_logging()

# how to set up pathway?

class CDIPanel(wx.Panel):
    # make new panel or access panel DIO? Started making new one below
    def __init__(self, parent, label, unit):
        super().__init__(parent, -1)
        self._parent = parent
        self._label = label
        self._unit = unit

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer_value = wx.BoxSizer(wx.HORIZONTAL)
        self.label_name = wx.StaticText(self, label=label)
        self.label_value = wx.StaticText(self, label='000')
        self.label_units = wx.StaticText(self, label=unit)
        self.__do_layout()

    def __do_layout(self):
        font = self.label_name.GetFont()
        font.SetPointSize(10)
        self.label_name.SetFont(font)
        font = self.label_value.GetFont()
        font.SetPointSize(15)
        self.label_value.SetFont(font)

        self.sizer.Add(self.label_name, wx.SizerFlags().CenterHorizontal())
        self.sizer_value.Add(self.label_value, wx.SizerFlags().CenterVertical())
        self.sizer_value.AddSpacer(10)
        self.sizer_value.Add(self.label_units, wx.SizerFlags().CenterVertical())
        self.sizer.Add(self.sizer_value, wx.SizerFlags().CenterHorizontal())

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    section = LP_CFG.get_hwcfg_section('CDI Monitor') # what's the real argument that needs to be passed here?
    com = section['commport']
    baud = section['baudrate']
    bytesize = section['bytesize']
    parity = section['parity']
    stopbits = section['stopbits']
    CDI = PHDserial('CDI500')
    CDI.open(com, baud)
    CDI.open_stream(LP_CFG.LP_PATH['stream'])
    CDI.start_stream()

    # stream all data and then parse

    # plot arterial pO2 and pCO2, venous pO2 and pCO2, pH, hemoglobin

    # set physio limits in graphs

    # make sure data is accessible

    # add buttons, sizing, titles, etc.

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
         kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
         wx.Frame.__init__(self, *args, **kwds)
         sizer = wx.GridSizer(cols=3)
         ArtShunt_sizer = wx.FlexGridSizer(cols=1)
         ArtShunt_sizer.AddGrowableRow(0, 2)
         ArtShunt_sizer.AddGrowableRow(1, 2)
         VenShunt_sizer = wx.FlexGridSizer(cols=1)
         VenShunt_sizer.AddGrowableRow(0, 2)
         VenShunt_sizer.AddGrowableRow(1, 2)
         HSCuvette_sizer = wx.FlexGridSizer(cols=1)
         HSCuvette_sizer.AddGrowableRow(0, 1)
         HSCuvette_sizer.AddGrowableRow(1, 1)

        # CONTINUE - call panel class

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True

if __name__ == "__main__":
    LP_CFG.set_base(basepath='~/Documents/LPTEST')
    LP_CFG.update_stream_folder()
    utils.setup_default_logging(filename='panel_saturation_monitor_data')
    app = MyTestApp(0)
    app.MainLoop()