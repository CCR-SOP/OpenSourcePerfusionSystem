# -*- coding: utf-8 -*-
"""Provides concrete class for controlling AO through NIDAQmx

Each channel is created and run separately to ensure full periods of a sine
wave are created. For DC tasks, the task end quickly as the DAQ will maintain
the DC output. Sine tasks keep updating from the buffer, however, this can
cause errors if multiple channels use a sine wave.

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import ctypes
import logging

import PyDAQmx
import PyDAQmx.DAQmxConstants

import pyHardware.pyAO as pyAO


class NIDAQAODevice(pyAO.AODevice):
    def __init__(self):
        super().__init__()
        self._lgr = logging.getLogger(__name__)
        self.__timeout = 1.0
        self.__hw_clk = False
        self.cfg = None

    @property
    def devname(self):
        # recreate from scratch so base naming convention does not need
        # to be consistent with actual hardware naming convention
        lines = [cfg.line for cfg in self.cfg.ch_info.values()]
        if len(lines) == 0:
            dev_str = f'{self.cfg.device_name}/ai'
        else:
            dev_str = f','.join([f'{self.cfg.device_name}/ao{line}' for line in lines])
        return dev_str

    def devname4line(self, line=None):
        # recreate from scratch so base naming convention does not need
        # to be consistent with actual hardware naming convention
        lines = [line]
        dev_str = f','.join([f'{self.cfg.device_name}/ao{line}' for line in lines])
        return dev_str

    def _output_samples(self):
        # super()._output_samples()
        pass

    def is_open(self):
        return any(self.__tasks)

    def open(self, cfg: pyAO.AODeviceConfig):
        self.cfg = cfg

    def close(self):
        self.stop()

    def add_channel(self, cfg):
        if cfg.name in self.ao_channels.keys():
            self._lgr.warning(f'Channel {cfg.name} already exists. Overwriting with new config')
        self.stop()
        self.cfg.ch_info[cfg.name] = cfg
        self.ao_channels[cfg.name] = NIDAQAOChannel(cfg=cfg, device=self)

    # def __check_hw_clk_support(self):
    #     task = PyDAQmx.Task()
    #     try:
    #         self._open_task(task)
    #     except pyAO.AODeviceException as e:
    #         self.__hw_clk = False
    #         raise
    #     else:
    #         try:
    #             task.CfgSampClkTiming("", 1.0, PyDAQmx.DAQmxConstants.DAQmx_Val_Rising,
    #                                   PyDAQmx.DAQmxConstants.DAQmx_Val_ContSamps, 10)
    #             self.__hw_clk = True
    #         except PyDAQmx.DAQmxFunctions.InvalidAttributeValueError:
    #             self.__hw_clk = False
    #
    #         task.StopTask()
    #         task.ClearTask()
    #         phrase = 'is' if self.__hw_clk else 'is not'
    #         self._lgr.info(f'Hardware clock {phrase} supported for {self.devname}')

    def start(self):
        for ch in self.ao_channels.values():
            ch.set_output(ch.cfg.output_type)

    def stop(self):
        for ch in self.ao_channels.values():
            # set output to 0 to stop all motors
            ch.set_output(pyAO.DCOutput(offset_volts=0.0))


class NIDAQAOChannel(pyAO.AOChannel):
    def __init__(self, cfg: pyAO.AOChannelConfig, device: pyAO.AODevice):
        super().__init__(cfg, device)
        self._task = PyDAQmx.Task()
        self.__timeout = 1.0
        self._open_task()

    def _open_task(self):
        self._task.StopTask()
        self._task.WaitUntilTaskDone(10.0)
        self._task.ClearTask()
        self._task = PyDAQmx.Task()
        try:
            devname = self.device.devname4line(line=self.cfg.line)
            self._task.CreateAOVoltageChan(devname, None, 0, 5,
                                           PyDAQmx.DAQmxConstants.DAQmx_Val_Volts, None)
        except PyDAQmx.DevCannotBeAccessedError as e:
            msg = f'Could not access device "{self.device.cfg.device_name}". Please ensure device is '\
                  f'plugged in and assigned the correct device name'
            self._lgr.error(msg)
            raise(pyAO.AODeviceException(msg))
        except PyDAQmx.DAQmxFunctions.PhysicalChanDoesNotExistError:
            msg = f'Channel "{self.cfg.line}" does not exist on device {self.device.cfg.device_name}'
            self._lgr.error(msg)
            raise(pyAO.AODeviceException(msg))
        except PyDAQmx.DAQmxFunctions.InvalidDeviceIDError:
            msg = f'Device "{self.device.cfg.device_name}" is not a valid device ID'
            self._lgr.error(msg)
            raise(pyAO.AODeviceException(msg))

    def set_output(self, output: pyAO.OutputType):
        super().set_output(output)
        self._open_task()

        hz = 1.0 / (self.device.cfg.sampling_period_ms / 1000.0)
        try:
            if len(self._buffer) > 1:
                self._task.CfgSampClkTiming("", hz, PyDAQmx.DAQmx_Val_Rising,
                                            PyDAQmx.DAQmx_Val_ContSamps,
                                            len(self._buffer))
        except PyDAQmx.DAQmxFunctions.InvalidAttributeValueError as e:
            msg = f'{self.device.cfg.device_name} does not support hardware sampling required for sine output'
            self._lgr.error(msg)
        try:
            written = ctypes.c_int32(0)
            self._task.WriteAnalogF64(len(self._buffer), True, self.__timeout * 5,
                                      PyDAQmx.DAQmx_Val_GroupByChannel,
                                      self._buffer, PyDAQmx.byref(written), None)
        except PyDAQmx.DAQmxFunctions.PALResourceReservedError as e:
            msg = f'{self.device.cfg.device_name} is reserved. Check for an invalid config or output type'
            self._lgr.error(msg)
            self._lgr.error(e)
