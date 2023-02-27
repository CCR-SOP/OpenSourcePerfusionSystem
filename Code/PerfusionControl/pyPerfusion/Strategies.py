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
import pyPerfusion.PerfusionConfig as PerfusionConfig


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


def get_strategy(name: str):
    params = PerfusionConfig.read_section('strategies', name)
    strategy_class = get_class(params['strategy'])
    cfg = strategy_class.get_config_type()()
    PerfusionConfig.read_into_dataclass('strategies', 'Stream2File', cfg)
    strategy = strategy_class(cfg.name, cfg.window_len, cfg.buf_len)
    return strategy
