"""Test program to control GB_100 Gas Mixer based on CDI input

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""

from pyPerfusion.pyGB100_SL import GB100_shift
import mcqlib_GB100.mcqlib.main as mcq
import pyPerfusion.PerfusionConfig as PerfusionConfig

PerfusionConfig.set_test_config()

sample_CDI_output = [1] * 18

HA_mixer = mcq.Main('Arterial Gas Mixer')
HA_mixer_shift = GB100_shift('HA', HA_mixer)
HA_mixer_shift.check_pH(sample_CDI_output)
HA_mixer_shift.check_CO2(sample_CDI_output)
HA_mixer_shift.check_O2(sample_CDI_output)
working_status = HA_mixer.get_working_status()
if working_status == 1:  # 1 is off
    HA_mixer.set_working_status_ON()

PV_mixer = mcq.Main('Venous Gas Mixer')
PV_mixer_shift = GB100_shift('PV', PV_mixer)
PV_mixer_shift.check_pH(sample_CDI_output)
PV_mixer_shift.check_CO2(sample_CDI_output)
PV_mixer_shift.check_O2(sample_CDI_output)
working_status = PV_mixer.get_working_status()
if working_status == 1:  # 1 is off
    PV_mixer.set_working_status_ON()
