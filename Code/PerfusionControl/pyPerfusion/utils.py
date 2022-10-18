# -*- coding: utf-8 -*-
"""Utils to manage loggers, performance measures, etc.

@project: Liver Perfusion
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from time import time
from functools import wraps

import pyPerfusion.PerfusionConfig as PerfusionConfig


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
    ch = logging.FileHandler(PerfusionConfig.get_folder('logs')/ f'{filename}.log')
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime) s: %(name) s - %(levelname) s - %(message) s')
    ch.setFormatter(formatter)
    lgr.addHandler(ch)


def filter_legend_messages(record):
    # print(record.module)
    if record.module == 'matplotlib.legend':
        return False
    return True

def configure_matplotlib_logging():
    # matplotlib logs to the root logger and can create
    # a lot of debug messages, this will only log warning
    # or higher levels
    lgr = logging.getLogger('matplotlib')
    lgr.setLevel(logging.WARNING)


def simple_time_tracker(log_fun):
    """ wrapper function to measure the execution time of a function
    Taken from https://medium.com/sicara/profile-surgical-time-tracking-python-db1e0a5c06b6
    """
    def _simple_time_tracker(fn):
        @wraps(fn)
        def wrapped_fn(*args, **kwargs):
            start_time = time()

            try:
                result = fn(*args, **kwargs)
            finally:
                elapsed_time = time() - start_time

                # log the result
                log_fun({
                    'function_name': fn.__name__,
                    'total_time': elapsed_time,
                })

            return result

        return wrapped_fn

    return _simple_time_tracker


def log(message):
    """for use with simple_time_tracker"""
    print('[SimpleTimeTracker] {function_name} {total_time:.3f}'.format(**message))
