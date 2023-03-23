# -*- coding: utf-8 -*-
""" Panel class for controlling analog output

@project: LiverPerfusion NIH
@author: Stephie Lux NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from time import sleep
import wx

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyHardware.SystemHardware import SYS_HW
from pyPerfusion.Sensor import Sensor

physio_ranges = {'hgb_lower': 7, 'hgb_upper': 12,
                 'K_lower': 2, 'K_upper': 6}

class PanelDC(wx.Panel):
    def __init__(self, parent, name, sensor):
        wx.Panel.__init__(self, parent, -1)
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self.name = name
        self.sensor = sensor

        self.panel_dc = PanelDCControl(self, self.name, self.sensor)

        font = wx.Font()
        font.SetPointSize(int(16))

        static_box = wx.StaticBox(self, wx.ID_ANY, label=self.name + " Pump")
        static_box.SetFont(font)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.__do_layout()
        self.__set_bindings()

    def close(self):
        self.sensor.hw.stop()

    def __do_layout(self):

        self.sizer.Add(self.panel_dc, wx.SizerFlags(1).Expand())

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass


class PanelDCControl(wx.Panel):
    def __init__(self, parent, name, sensor):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self.name = name
        self.sensor = sensor
        self.reader = self.sensor.get_reader()
        self.sensor.hw.start()

        font = wx.Font()
        font.SetPointSize(int(18))
        font_btn = wx.Font()
        font_btn.SetPointSize(int(16))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.label_offset = wx.StaticText(self, label='Pump Speed (mL/min)')
        self.entered_offset = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=50, inc=.5)
        self.label_offset.SetFont(font)
        self.entered_offset.SetFont(font)

        self.btn_change_rate = wx.Button(self, label='Update Rate')
        self.btn_change_rate.SetFont(font_btn)

        self.btn_stop = wx.Button(self, label='Stop')
        self.btn_stop.SetFont(font_btn)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_offset, wx.SizerFlags().CenterHorizontal())
        sizer.Add(self.entered_offset, wx.SizerFlags(1).Expand())
        self.sizer.Add(sizer, wx.SizerFlags(0).Expand())

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_change_rate)
        sizer.Add(self.btn_stop)
        self.sizer.Add(sizer, wx.SizerFlags(0).CenterHorizontal().Top())

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_change_rate.Bind(wx.EVT_BUTTON, self.on_update)
        self.btn_stop.Bind(wx.EVT_BUTTON, self.on_stop)

    def on_update(self, evt):
        self._lgr.debug('on_update called')
        new_flow = self.entered_offset.GetValue() / 10
        self.sensor.hw.set_output(new_flow)

        sleep(2)
        ts, last_samples = self.reader.retrieve_buffer(5000, 5)
        for ts, samples in zip(ts, last_samples):
            self._lgr.debug(f' At time {ts}, {self.name} Pump was changed to {samples*10} mL/min')

    def update_dialysis_rates(self, cdi_input):
        self._lgr.debug(f'{cdi_input.K} is K and {cdi_input.hgb} is hgb. Name is {self.name}')

        if self.name == "Dialysate Outflow" or self.name == "Dialysate Inflow":

            if cdi_input.hgb == -1:
                self._lgr.warning(f'Hemoglobin is out of range. Cannot be adjusted automatically')
            elif 0 < cdi_input.hgb < physio_ranges['hgb_lower'] and self.name == "Dialysate Outflow":
                self._lgr.info(f'Hemoglobin is low at {cdi_input.hgb}. Increasing dialysate outflow')
                self.increase_dc_pump_speed()
            elif cdi_input.hgb > physio_ranges['hgb_upper'] and self.name == "Dialysate Inflow":
                self._lgr.info(f'Hemoglobin is high at {cdi_input.hgb}. Increasing dialysate inflow')
                self.increase_dc_pump_speed()
            else:
                self._lgr.info(f'No need to increase or decrease relative inflow/outflow rates')

            if cdi_input.K == -1:
                self._lgr.warning(f'K is out of range. Cannot be adjusted automatically')
            elif cdi_input.K > physio_ranges['K_upper']:
                self._lgr.info(f'K is high at {cdi_input.K}. Increasing rates of dialysis')
                self.increase_dc_pump_speed()
            elif 0 < cdi_input.K < physio_ranges['K_lower']:
                self._lgr.info(f'K is stable at {cdi_input.K}. Decreasing rates of dialysis to conserve dialysate')
                self.decrease_dc_pump_speed()
            else:
                self._lgr.info(f'Dialysis can continue at a stable rate')
    
    def increase_dc_pump_speed(self):
        sleep(1)
        ts, last_samples = self.reader.get_last_acq()
        current_flow_rate = last_samples * 10
        self._lgr.info(f'{current_flow_rate} mL/min')
        if current_flow_rate <= 9.5:
            new_voltage = (current_flow_rate + 0.5) / 10
            self._lgr.info(f'{new_voltage} V')
            self.sensor.hw.set_output(new_voltage)
        else:
            self._lgr.warning(f'Current flow rate is {current_flow_rate}. '
                              f'At ceiling - cannot be automatically exceeded')
        
    def decrease_dc_pump_speed(self):
        sleep(1)
        ts, last_samples = self.reader.get_last_acq()
        current_flow_rate = last_samples * 10
        self._lgr.info(f'{current_flow_rate} mL/min')
        if current_flow_rate >= 0.5:
            new_voltage = (current_flow_rate - 0.5) / 10
            self._lgr.info(f'{new_voltage} V')
            self.sensor.hw.set_output(new_voltage)
        else:
            self._lgr.warning(f'Current flow rate is {current_flow_rate}. Cannot go negative')

    def on_stop(self, evt):
        self.sensor.hw.set_output(int(0))


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelDC(self, pump_name, trial_sensor)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        SYS_HW.stop()
        trial_sensor.stop()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()

    SYS_HW.load_hardware_from_config()

    pump_name = 'Dialysate Inflow'
    try:
        trial_sensor = Sensor(name=pump_name)
        trial_sensor.read_config()
    except PerfusionConfig.MissingConfigSection:
        print(f'Could not find sensor called {pump_name} in sensors.ini')
        SYS_HW.stop()
        raise SystemExit(1)
    trial_sensor.start()

    app = MyTestApp(0)
    app.MainLoop()
