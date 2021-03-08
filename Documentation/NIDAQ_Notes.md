Basic information on the NI DAQ devices in use and limitations on NIDAQmx software.
Last updated: 2021-02-10

USB-6211 required for analog output waveforms (other than DC) as the USB-6009 does not support hardware-timed analog outputs. 

# Task Limitations 
NIDAQ-mx software has certain limitations on the number of tasks allowed. See NI Support [https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z0000019KWYSA2&l=en-US](Article: Running DAQmx Tasks Simultaneously). 

For Hardware-timed tasks, there can be only 1 task per device each for Analog Input, Analog Output, Digital Input, and Digital Output. Counters can have a task per counter.

For Software-timed task, there is 1 task per device for Analog Input, 1 task per AO channel, 1 task per Digital Input channel, and 1 task per Digital Output channel.  Counters have a task per counter.

# Digital Outputs
Only the VCS uses digital outputs. While they can be combined into single port task, they can be software-timed so there is no need to change the existing code.

# Analog Outputs
There are 5 devices (pumps) that require analog output. Currently, only 1 (HA pump) will definitely require hardware-timed output. The others are most likely DC output only. As of 2021-02-09, ramp waveforms (to control accel/decel) use hardware-timing (if available). Ramps should be always done with software-timing as they are non-critical.

# Analog Inputs
There are 10 analog inputs. The gas sensors (O2, CO2, pH) and temp sensor do not need hardware-timing has they are taken intermittently. The remaining 6 (pressure and flow) are assumed to require hardware-timing.

