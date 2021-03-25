# -*- coding: utf-8 -*-
"""Utils to manage loggers

@project: Liver Perfusion
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from pyPerfusion.PerfusionConfig import LP_PATH


def setup_default_logging():
    setup_stream_logger(logging.getLogger(), logging.INFO)
    setup_file_logger(logging.getLogger(), logging.DEBUG)
    disable_matplotlib_debug()


def setup_stream_logger(lgr, level):
    lgr.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('%(name) s - %(levelname) s - %(message) s')
    ch.setFormatter(formatter)
    lgr.addHandler(ch)


def setup_file_logger(lgr, level, filename=None):
    if not filename:
        filename = lgr.name
    lgr.setLevel(level)
    ch = logging.FileHandler(LP_PATH['logs'] / f'{filename}.log')
    ch.setLevel(level)
    formatter = logging.Formatter('%(name) s - %(levelname) s - %(message) s')
    ch.setFormatter(formatter)
    lgr.addHandler(ch)


def disable_matplotlib_debug():
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
