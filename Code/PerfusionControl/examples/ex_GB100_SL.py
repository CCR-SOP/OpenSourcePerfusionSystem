"""Test program to control GB_100 Gas Mixer based on CDI input

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""

from pyPerfusion.pyGB100_SL import GB100_shift
import mcqlib_GB100.mcqlib.main as mcq

sample_CDI_output = [0] * 18

HA_mixer = mcq.Main('Arterial Gas Mixer')
HA_mixer_shift = GB100_shift('HA', HA_mixer)
HA_mixer_shift.check_pH(sample_CDI_output)
HA_mixer_shift.check_CO2(sample_CDI_output)
HA_mixer_shift.check_O2(sample_CDI_output)

PV_mixer = mcq.Main('Venous Gas Mixer')
PV_mixer_shift = GB100_shift('PV', PV_mixer)
PV_mixer_shift.check_pH(sample_CDI_output)
# PV_mixer_shift.check_CO2(sample_CDI_output)
PV_mixer_shift.check_O2(sample_CDI_output)