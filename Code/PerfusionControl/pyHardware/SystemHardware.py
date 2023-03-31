# -*- coding: utf-8 -*-
""" SystemHardware provides a unified location to handle all system hardware

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import time

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyHardware.pyAI as pyAI
import serial.serialutil
from pyHardware.pyAI_NIDAQ import NIDAQAIDevice, AINIDAQDeviceConfig
import pyPerfusion.pyCDI as pyCDI
import pyPerfusion.pyPump11Elite as pyPump11Elite
from pyHardware.pyGB100 import GasDevice
from pyHardware.pyDC_NIDAQ import NIDAQDCDevice
import pyHardware.pyDC as pyDC
import pyPerfusion.pyDexcom as pyDexcom


class SystemHardware:
    def __init__(self):
        self._lgr = logging.getLogger(__name__)
        self.mocks_enabled = False

        self.ni_dev1 = NIDAQAIDevice()
        self.ni_dev2 = NIDAQAIDevice()

        self.syringes = []

        self.ha_mixer = None
        self.pv_mixer = None

        self.dialysate_outflow = None
        self.glucose_circuit = None
        self.dialysate_inflow = None
        self.dialysis_blood = None

        self.cdi = None
        self.dexcoms = []

        self.mock_device = None
        self.mock_cdi = None
        self.mock_syringe = None


    def load_hardware_from_config(self):
        try:
            self.ni_dev1.cfg = AINIDAQDeviceConfig(name='Dev1')
            self.ni_dev1.read_config()
            self.ni_dev2.cfg = AINIDAQDeviceConfig(name='Dev2')
            self.ni_dev2.read_config()
        except pyAI.AIDeviceException as e:
            self._lgr.error(e)

        try:
            self.ha_mixer = GasDevice(name='Arterial Gas Mixer')
            self.ha_mixer.read_config()
        except Exception as e:
            self._lgr.error(f'Error trying to create {self.ha_mixer.name}')
            self._lgr.error(f'GasDevice exception: {e}')

        try:
            self.pv_mixer = GasDevice(name='Venous Gas Mixer')
            self.pv_mixer.read_config()
        except Exception as e:
            self._lgr.error(f'Error trying to create {self.pv_mixer.name}')
            self._lgr.error(f'GasDevice exception: {e}')

        try:
            self.cdi = pyCDI.CDIStreaming(name='CDI')
            self.cdi.read_config()
        except Exception as e:
            self._lgr.error('Error trying to create CDI')
            self._lgr.error(f'CDI exception: {e}')

        try:
            self.dialysate_inflow = NIDAQDCDevice()
            self.dialysate_inflow.cfg = pyDC.DCChannelConfig(name='Dialysate Inflow Pump')
            self.dialysate_inflow.read_config()

            self.dialysate_outflow = NIDAQDCDevice()
            self.dialysate_outflow.cfg = pyDC.DCChannelConfig(name='Dialysate Outflow Pump')
            self.dialysate_outflow.read_config()

            self.dialysis_blood = NIDAQDCDevice()
            self.dialysis_blood.cfg = pyDC.DCChannelConfig(name='Dialysis Blood Pump')
            self.dialysis_blood.read_config()

            self.glucose_circuit = NIDAQDCDevice()
            self.glucose_circuit.cfg = pyDC.DCChannelConfig(name='Glucose Circuit Pump')
            self.glucose_circuit.read_config()
        except pyDC.DCDeviceException as e:
            self._lgr.error(e)

        all_syringe_names = PerfusionConfig.get_section_names('syringes')
        real_syringe_names = all_syringe_names[1:]
        # self._lgr.debug(f' Excluding mock: {real_syringe_names}')
        for name in real_syringe_names:
            syringe = pyPump11Elite.Pump11Elite(name=name)
            syringe.read_config()
            self._lgr.debug(f'read syringe {name}: {syringe}')
            self.syringes.append(syringe)

        # all_dexcom_names = PerfusionConfig.get_section_names('dexcom')
        # for name in all_dexcom_names:
            # dexcom = pyDexcom.DexcomReceiver(name=name)
            # try:
                # dexcom.read_config()
                # self._lgr.debug(f'read dexcom {name}: {dexcom}')
                # self.dexcoms.append(dexcom)
            # except serial.serialutil.SerialException as e:
                # self._lgr.error(f"Could not open dexcom {name} at port {dexcom.cfg.com_port}")


    def load_mocks(self):
        self.mocks_enabled = True
        self.mock_device = pyAI.AIDevice()
        self.mock_cdi = pyCDI.MockCDI('mock_cdi')
        self.mock_syringe = pyPump11Elite.MockPump11Elite(name='mock_syringe')

        self.mock_device.cfg = pyAI.AIDeviceConfig(name='FakeEvents')
        self.mock_device.read_config()
        self.mock_cdi.cfg = pyCDI.CDIConfig(name='mock_cdi')
        self.mock_cdi.read_config()
        self.mock_syringe.cfg = pyPump11Elite.SyringeConfig(name='mock_syringe')
        self.mock_syringe.read_config()

    def start(self):
        try:
            self.ni_dev1.start()
            self.ni_dev2.start()
        except pyAI.AIDeviceException as e:
            self._lgr.error(e)
        for syringe in self.syringes:
            syringe.start()

        for dexcom in self.dexcoms:
            dexcom.start()

        if self.cdi:
            self.cdi.start()

        if self.ha_mixer:
            self.ha_mixer.start()
        if self.pv_mixer:
            self.pv_mixer.start()

        if self.mocks_enabled:
            self.mock_device.start()
            self.mock_cdi.start()
            self.mock_syringe.start()

    def stop(self):
        try:
            self.ni_dev1.stop()
            self.ni_dev2.stop()
        except pyAI.AIDeviceException as e:
            self._lgr.error(e)

        try:
            self.glucose_circuit.stop()
            self.dialysate_inflow.stop()
            self.dialysate_outflow.stop()
            self.dialysis_blood.stop()

        except pyDC.DCDeviceException as e:
            self._lgr.error(e)

        for syringe in self.syringes:
            syringe.stop()

        for dexcom in self.dexcoms:
            dexcom.stop()

        if self.cdi:
            self.cdi.stop()

        if self.ha_mixer:
            self.ha_mixer.stop()
        if self.pv_mixer:
            self.pv_mixer.stop()
            
        if self.mocks_enabled:
            self.mock_device.stop()
            self.mock_cdi.stop()
            self.mock_syringe.stop()

    def get_hw(self, name: str = None):
        self._lgr.debug(f'Getting hardware named: {name}')
        hw = None
        if hw is None:
            if name == 'Glucose Circuit Pump':
                hw = self.glucose_circuit
            elif name == 'Dialysate Inflow Pump':
                hw = self.dialysate_inflow
            elif name == 'Dialysate Outflow Pump':
                hw = self.dialysate_outflow
            elif name == 'Dialysis Blood Pump':
                hw = self.dialysis_blood
            elif name == 'Arterial Gas Mixer':
                hw = self.ha_mixer
            elif name == 'Venous Gas Mixer':
                hw = self.pv_mixer
            elif name == 'CDI':
                hw = self.cdi
        if hw is None:
            hw = self.ni_dev1.ai_channels.get(name, None)
        if hw is None:
            hw = self.ni_dev2.ai_channels.get(name, None)
        if hw is None:
            hw = next((syringe for syringe in self.syringes if syringe.name == name), None)
        if hw is None:
            hw = next((dexcom for dexcom in self.dexcoms if dexcom.name == name), None)

        if self.mocks_enabled:
            if hw is None and self.mock_device is not None:
                hw = self.mock_device.ai_channels.get(name, None)
            if hw is None:
                if name == "mock_cdi":
                    hw = self.mock_cdi
                elif name == "mock_syringe":
                    hw = self.mock_syringe
        self._lgr.debug(f'Found {hw}')
        return hw


SYS_HW = SystemHardware()
