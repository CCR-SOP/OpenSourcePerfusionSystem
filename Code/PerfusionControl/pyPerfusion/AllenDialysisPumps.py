"""Adjusts MasterFlex pumps based on CDI output

@project: LiverPerfusion NIH
@author: Allen Luna, Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""

from enum import Enum
import wx
import logging
import pyPerfusion.utils as utils
from pyPerfusion.pyDialysatePumps import DialysatePumps

dialysis_limits = {'flow_rate_lower': 3, 'flow_rate_upper': 20, 'flow_difference': 3,
                   'K_lower': 3, 'K_upper': 6,
                   'hct_lower': 17, 'hct_upper': 38}

# Allen's ONDialysis method
def OnDialysis(self, event):  # Logging dialysis rates? New file?
    label = self.btn_automated_dialysis.GetLabel()
    if label == 'Start Automated Dialysis':
        inflow = self.spin_inflow_pump_rate.GetValue()
        outflow = self.spin_outflow_pump_rate.GetValue()
        self._pump_streaming.start_stream()
        self._pump_streaming.record(inflow, outflow, 1)
        self._inflow_pump.start()
        self._inflow_pump.set_dc(
            inflow / 10.9)  # With the 3.17mm BWB peristaltic pump tubing that we use, 1 V = 10.9 ml/min of flow
        self._inflow_pump.set_dc(inflow / 10.9)
        self._outflow_pump.start()
        self._outflow_pump.set_dc(outflow / 10.9)
        self._outflow_pump.set_dc(outflow / 10.9)  # For some reason this only works if I give two commands...
        self.spin_inflow_pump_rate.Enable(False)
        self.spin_outflow_pump_rate.Enable(False)
        self.timer_update_dialysis.Start(300000, wx.TIMER_CONTINUOUS)
        self.btn_automated_dialysis.SetLabel('Stop Automated Dialysis')
    elif label == 'Stop Automated Dialysis':
        self.timer_update_dialysis.Stop()
        self._inflow_pump.set_dc(0)
        self._inflow_pump.close()
        self._outflow_pump.set_dc(0)
        self._outflow_pump.close()
        self._pump_streaming.record(self.spin_inflow_pump_rate.GetValue(), self.spin_outflow_pump_rate.GetValue(), 0)
        self._pump_streaming.stop_stream()
        self.spin_inflow_pump_rate.Enable(True)
        self.spin_outflow_pump_rate.Enable(True)
        self.btn_automated_dialysis.SetLabel('Start Automated Dialysis')

# Allen had a dialysis timer? I think gas mixer, CDI, dialysis all being checked every 5 mintues if sufficient to start
def OnDialysisTimer(self, event):
    if event.GetId() == self.timer_update_dialysis.GetId():
        self.update_dialysis()

# checks K and hct and updates rates accordingly, try to make more succinct
    def update_dialysis(self):
        change_inflow = False
        change_outflow = False
        current_inflow = self.spin_inflow_pump_rate.GetValue()
        new_inflow = current_inflow
        if self._monitor._TSMSerial__thread_streaming:
            K = self.readouts['K'].label_value.GetLabel()
            try:
                k_value = float(K)
            except ValueError:
                k_value = []
            if k_value and k_value >= self.upper_k_limit:  # Want to run harder dialysis
                new_inflow = current_inflow + 0.5
            elif k_value and k_value <= self.lower_k_limit:  # Back off on dialysis
                new_inflow = current_inflow - 0.5
            else:
                pass
        if new_inflow > self.upper_dialysis_limit:
            new_inflow = self.upper_dialysis_limit
        elif new_inflow < self.lower_dialysis_limit:
            new_inflow = self.lower_dialysis_limit
        if new_inflow == current_inflow:
            print('no change in dialysate inflow rate required')
            adjusted_outflow = self.spin_outflow_pump_rate.GetValue()
        else:
            print('changing dialysate inflow rate')
            self._inflow_pump.set_dc(new_inflow/10.9)
            self.spin_inflow_pump_rate.SetValue(new_inflow)
            adjusted_outflow = self.spin_outflow_pump_rate.GetValue() + (new_inflow - current_inflow)
            change_inflow = True
        current_inflow = self.spin_inflow_pump_rate.GetValue()
        current_outflow = self.spin_outflow_pump_rate.GetValue()
        new_outflow = adjusted_outflow
        if self._monitor._TSMSerial__thread_streaming:
            Hct = self.readouts['Hct'].label_value.GetLabel()
            try:
                hct_value = float(Hct)
            except ValueError:
                hct_value = []
            if hct_value and hct_value >= self.upper_hct_limit:  # Want to dilute
                new_outflow -= 0.5
            elif hct_value and hct_value <= self.lower_hct_limit:  # Want to concentrate
                new_outflow += 0.5
            else:
                pass
        if new_outflow > (current_inflow + 1.5):  # Don't want flow rates to be massively divergent or else we will get significant concentration/dilution in a short period
            new_outflow = current_inflow + 1.5
        elif new_outflow < (current_inflow - 1.5):
            new_outflow = current_inflow - 1.5
        if new_outflow == current_outflow:
            print('no change in dialysate outflow rate required')
        else:
            print('changing dialysate outflow rate')
            self._outflow_pump.set_dc(new_outflow/10.9)
            self.spin_outflow_pump_rate.SetValue(new_outflow)
            change_outflow = True
        if change_inflow or change_outflow:
            self._pump_streaming.record(self.spin_inflow_pump_rate.GetValue(), self.spin_outflow_pump_rate.GetValue(), 1)

# hardware interfacing - need to keep this probably? check comports
self.ao_inflow = NIDAQ_AO('Dialysate Inflow Pump')
        self.ao_outflow = NIDAQ_AO('Dialysate Outflow Pump')
        self.ao_streaming = DialysatePumps('Automated Dialysate Pumps')
        self.ao_streaming.open()
        self.ao_streaming.open_stream(LP_CFG.LP_PATH['stream'])

# end of timer
self.panel_GB100_CDI_Presens.timer_update_dialysis.Stop()

