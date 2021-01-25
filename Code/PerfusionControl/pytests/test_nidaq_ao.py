import time

import PyDAQmx
import numpy as np
import ctypes

top = 2
bottom = 1
write_temp = [top, bottom]
for x in range(0, 4):
    write_temp.append(top)
    write_temp.append(bottom)
write_temp = [float(i) for i in write_temp]
write_temp = np.array(write_temp)
# print(f'{write_temp}')

samples_per_channel_written = ctypes.c_int(0)  # Place holder for a single number that shows samples written
# task = Task()
# task.CreateAOVoltageChan("Dev2/ao0", "", -10.0, 10.0, PyDAQmx.DAQmx_Val_Volts, None)
# task.CfgSampClkTiming(None, 1, PyDAQmx.DAQmx_Val_Rising,
#                                     PyDAQmx.DAQmx_Val_FiniteSamps, 10)

# task.WriteAnalogF64(10, 0, 0, PyDAQmx.DAQmx_Val_GroupByChannel,
#                                   write_temp, PyDAQmx.byref(samples_per_channel_written), None)
# print(f'samples written is {samples_per_channel_written}')
# task.StartTask()

t = np.arange(0, 1.0, step=0.01)
buffer = 1.0 * np.sin(2 * np.pi * 5 * t, dtype=np.float64) + 1.75

task = PyDAQmx.Task()
task.CreateAOVoltageChan("Dev3/ao0", None, -10, 10, PyDAQmx.DAQmx_Val_Volts, None)
task.CfgSampClkTiming("", 100.0, PyDAQmx.DAQmx_Val_Rising, PyDAQmx.DAQmx_Val_FiniteSamps, 10000)
#task.WriteAnalogF64(1000, 1, 10.0, PyDAQmx.DAQmx_Val_GroupByChannel,
#                    buffer, PyDAQmx.byref(samples_per_channel_written), None)
#task.StartTask()
for i in range(1, 10):
    print(f'loop {i}')
    task.WriteAnalogF64(100, 1, 10.0, PyDAQmx.DAQmx_Val_GroupByChannel,
                        buffer, PyDAQmx.byref(samples_per_channel_written), None)
    # time.sleep(0.1)
print(f'samples written is {samples_per_channel_written}')

# Try TaskHandle Method (DOES NOT WORK EITHER)
# task_handle = PyDAQmx.TaskHandle()
# PyDAQmx.DAQmxCreateTask("", PyDAQmx.byref(task_handle))
# PyDAQmx.DAQmxCreateAOVoltageChan(task_handle, "Dev3/ao0", "", -10, 10, DAQmx_Val_Volts, "")
# PyDAQmx.DAQmxCfgSampClkTiming(task_handle, "OnboardClock", 1000.0, DAQmx_Val_Rising, DAQmx_Val_ContSamps, len(buffer))
# PyDAQmx.DAQmxWriteAnalogF64(task_handle, len(buffer), 0, 10.0, DAQmx_Val_GroupByChannel,
#                             buffer, None, None)
# PyDAQmx.DAQmxStartTask(task_handle)