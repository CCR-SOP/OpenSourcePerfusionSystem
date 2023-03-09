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
from pyPerfusion.panel_DC import PanelDC
from pyHardware.pyDC_NIDAQ import NIDAQDCDevice
import pyHardware.pyDC as pyDC
from pyPerfusion.FileStrategy import StreamToFile
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.pyCDI as pyCDI
from pyPerfusion.SensorPoint import SensorPoint, ReadOnlySensorPoint
from pyPerfusion.FileStrategy import MultiVarToFile, MultiVarFromFile


class DialysisPumpPanel(wx.Panel):
    def __init__(self, parent, roller_pumps, cdi_data, **kwds):
        self._lgr = logging.getLogger(__name__)
        wx.Panel.__init__(self, parent, -1)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        self.parent = parent
        self.cdi_data = cdi_data
        self.roller_pumps = roller_pumps

        self._panel_outflow = PanelDC(self, self.roller_pumps['Dialysate Outflow Pump'])
        self._panel_glucose = PanelDC(self, self.roller_pumps['Glucose Circuit Pump'])
        self._panel_inflow = PanelDC(self, self.roller_pumps['Dialysate Inflow Pump'])
        self._panel_bloodflow = PanelDC(self, self.roller_pumps['Dialysis Blood Pump'], self.cdi_data)

        static_box = wx.StaticBox(self, wx.ID_ANY, label="Roller Pumps")
        self.sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

        self.__do_layout()
        self.__set_bindings()

    def close(self):
        self._panel_outflow.close()
        self._panel_inflow.close()
        self._panel_glucose.close()
        self._panel_bloodflow.close()

    def __do_layout(self):
        flagsExpand = wx.SizerFlags(1)
        flagsExpand.Expand().Border(wx.ALL, 10)
        self.sizer = wx.GridSizer(cols=2)

        self.sizer.Add(self._panel_inflow, flagsExpand)
        self.sizer.Add(self._panel_outflow, flagsExpand)
        self.sizer.Add(self._panel_bloodflow, flagsExpand)
        self.sizer.Add(self._panel_glucose, flagsExpand)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass

class CheckHGB(DialysisPumpPanel):  # TODO: THIS DOES NOT WORK - MOVE TO MORE LOGICAL LOCATION
    def __init__(self, parent, cdi_input, cdi_data=None, **kwds):
        super().__init__(parent, cdi_data, **kwds)
        self.cdi_input = cdi_input
        self._lgr = logging.getLogger(__name__)
        self.update_dialysis()

    def update_dialysis(self):
        # TODO: Add ceilings and error cases
        if self.cdi_input.hgb < 7:
            self._lgr.debug('Hemoglobin is low. Increasing dialysate outflow')
            # current_flow_rate = 10  # TODO: GET CURRENT FLOW RATE
            # new_flow_rate = current_flow_rate + 1
            # self._panel_outflow.sensor.hw.set_output(int(new_flow_rate))
        elif self.cdi_input.hgb > 12:
            self._lgr.debug(f'Hemoglobin is high. Increasing dialysate inflow')
            # TODO: add real method for _panel_inflow
        elif self.cdi_input.K > 6:
            self._lgr.debug(f'K is high. Increasing rates of dialysis')
            # TODO: add real method
        else:
            self._lgr.debug(f'Dialysis can continue at a stable rate')

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = DialysisPumpPanel(self, roller_pumps=r_pumps, cdi_data=cdi_object)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.Destroy()
        self.panel.close()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    logger = logging.getLogger()
    utils.setup_stream_logger(logger, logging.DEBUG)
    utils.configure_matplotlib_logging()

    # Initialize pumps
    r_pumps = {}
    rPumpNames = ["Dialysate Outflow Pump", "Dialysate Inflow Pump",
                       "Dialysis Blood Pump", "Glucose Circuit Pump"]
    for pumpName in rPumpNames:
        hw = NIDAQDCDevice()
        hw.cfg = pyDC.DCChannelConfig(name=pumpName)
        hw.read_config()
        sensor = SensorStream(hw, "ml/min")
        sensor.add_strategy(strategy=StreamToFile('Raw', 1, 10))
        r_pumps[pumpName] = sensor

    # Initialize CDI
    cdi_object = pyCDI.CDIStreaming('CDI')
    cdi_object.read_config()
    stream_cdi_to_file = SensorPoint(cdi_object, 'NA')
    stream_cdi_to_file.add_strategy(strategy=MultiVarToFile('write', 1, 17))
    ro_sensor = ReadOnlySensorPoint(cdi_object, 'na')
    read_from_cdi = MultiVarFromFile('multi_var', 1, 17, 1)
    ro_sensor.add_strategy(strategy=read_from_cdi)
    stream_cdi_to_file.start()
    cdi_object.start()

    app = MyTestApp(0)
    app.MainLoop()
