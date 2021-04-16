# -*- coding: utf-8 -*-
"""Utils to manage loggers

@project: Liver Perfusion
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import warnings

from pyPerfusion.PerfusionConfig import LP_PATH


def setup_default_logging(filename=None):
    setup_stream_logger(logging.getLogger(), logging.INFO)
    setup_file_logger(logging.getLogger(), logging.DEBUG, filename)
    configure_matplotlib_logging()


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
    formatter = logging.Formatter('%(asctime) s: %(name) s - %(levelname) s - %(message) s')
    ch.setFormatter(formatter)
    lgr.addHandler(ch)


def filter_legend_messages(record):
    print(record.module)
    if record.module == 'matplotlib.legend':
        return False
    return True

def configure_matplotlib_logging():
    # matplotlib logs to the root logger and can create
    # a lot of debug messages, this will only log warning
    # or higher levels
    lgr = logging.getLogger('matplotlib')
    lgr.setLevel(logging.WARNING)
