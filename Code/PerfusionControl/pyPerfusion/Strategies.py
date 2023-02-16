# -*- coding: utf-8 -*-
"""Base class for processing stream data


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from dataclasses import dataclass

import pyPerfusion.ProcessingStrategy as ProcessingStrategy
import pyPerfusion.FileStrategy as FileStrategy


def get_class(name: str):
    if name == 'RMSStrategy':
        return ProcessingStrategy.RMSStrategy
    elif name == 'MovingAverageStrategy':
        return ProcessingStrategy.MovingAverageStrategy
    elif name == 'StreamToFile':
        return FileStrategy.StreamToFile
    elif name == 'PointsToFile':
        return FileStrategy.PointsToFile
    else:
        return None

