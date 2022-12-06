"""Panel class for configuring CDI saturation monitor

@project: Liver Perfusion, NIH
@author: Stephie Lux, NIH

JUST COPIED FROM OLD pyCDI FILE - NOT UPDATED

"""
from enum import Enum
import wx
import logging

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.pyCDI as pyCDI

from pyPerfusion.FileStrategy import MultiVarToFile, MultiVarFromFile
from pyPerfusion.SensorPoint import SensorPoint, ReadOnlySensorPoint

utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
utils.configure_matplotlib_logging()


class PanelCDI(wx.Panel):
    def __init__(self, parent, cdi_obj: pyCDI.CDIStreaming):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self.cdi = cdi

        self._panel_cfg = PanelCDIConfig(self, self.cdi)
        # self._panel_display = PanelCDIDisplay(self, self.cdi)
        static_box = wx.StaticBox(self, wx.ID_ANY, label=self.cdi.name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()

        self.sizer.Add(self._panel_cfg, flags.Proportion(2))
        # self.sizer.Add(self._panel_display, flags.Proportion(2))
        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass


class PanelCDIConfig(wx.Panel):
    def __init__(self, parent, cdi_obj: pyCDI.CDIStreaming):
        super().__init__(parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self.cdi = cdi_obj

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.label_port = wx.StaticText(self, label='COM Port')
        avail_ports = utils.get_avail_com_ports()
        self.combo_port = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY, choices=avail_ports)

        # self.label_interval = wx.StaticText(self, label='Output Interval As Entered by CDI Front Panel')
        # self.combo_interval = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY, choices=[0, 6, 30, 1, 2, 5, 10])

        self.btn_open = wx.ToggleButton(self, label='Open')

        self.btn_save_cfg = wx.Button(self, label='Save')
        self.btn_load_cfg = wx.Button(self, label='Load')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center()

        sizer_cfg = wx.GridSizer(cols=2)
        sizer_cfg.Add(self.label_port, flags)
        sizer_cfg.Add(self.combo_port, flags)

        # sizer_cfg.Add(self.label_interval, flags)
        # sizer_cfg.Add(self.choice_interval, flags)

        sizer_cfg.Add(self.btn_open, flags)
        sizer_cfg.AddSpacer(2)

        sizer_cfg.Add(self.btn_load_cfg, flags)
        sizer_cfg.Add(self.btn_save_cfg, flags)
        self.sizer.Add(sizer_cfg)

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_open.Bind(wx.EVT_TOGGLEBUTTON, self.OnOpen)
        self.btn_save_cfg.Bind(wx.EVT_BUTTON, self.on_save_cfg)
        self.btn_load_cfg.Bind(wx.EVT_BUTTON, self.on_load_cfg)

    def OnOpen(self, evt):
        port = self.combo_port.GetStringSelection()
        # interval = self.combo_interval.GetStringSelection()
        if not self.cdi.is_open():
            self.cdi.cfg.com_port = port
            self.cdi.open()

            self.btn_open.SetLabel('Close')
        else:
            self._lgr.debug(f'Closing cdi at {port}')
            self.cdi.close()
            self.btn_open.SetLabel('Open')

    def update_config_from_controls(self):
        self.cdi.cfg.com_port = self.combo_port.GetStringSelection()

    def update_controls_from_config(self):
        self.combo_port.SetStringSelection(self.cdi.cfg.port)

    def on_save_cfg(self, evt):
        self.update_config_from_controls()
        self.cdi.write_config()

    def on_load_cfg(self, evt):
        self.cdi.read_config()
        self.update_controls_from_config()


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.cdi = pyCDI.CDIStreaming('CDI')
        self.panel = PanelCDI(self, self.cdi)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, evt):
        self.cdi.close()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()

    cdi = pyCDI.CDIStreaming('CDI')
    cdi.read_config()
    sensorpt = SensorPoint(cdi, 'na')
    sensorpt.add_strategy(strategy=MultiVarToFile('write', 1, 17))
    ro_sensorpt = ReadOnlySensorPoint(cdi, 'na')
    read_strategy = MultiVarFromFile('multi_var', 1, 17, 1)
    ro_sensorpt.add_strategy(strategy=read_strategy)
    sensorpt.start()
    cdi.start()

    app = MyTestApp(0)
    app.MainLoop()