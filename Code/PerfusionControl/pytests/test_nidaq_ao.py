import PyDAQmx
from PyDAQmx import Task
from PyDAQmx.DAQmxConstants import *
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

t = np.arange(0, 3.0, step=0.001)
buffer = 1.0 * np.sin(2 * np.pi * 1 * t, dtype=np.float64) + 1.75
task = Task()
task.CreateAOVoltageChan("Dev2/ao0", None, -10, 10, DAQmx_Val_Volts, None)
task.CfgSampClkTiming(None, 100, PyDAQmx.DAQmx_Val_Rising,
                      PyDAQmx.DAQmx_Val_FiniteSamps, len(buffer))
task.WriteAnalogF64(len(buffer), 1, 5.0, PyDAQmx.DAQmx_Val_GroupByChannel,
                    buffer, PyDAQmx.byref(samples_per_channel_written), None)
print(f'samples written is {samples_per_channel_written}')
