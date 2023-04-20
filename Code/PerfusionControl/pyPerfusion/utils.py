# -*- coding: utf-8 -*-
"""Utils to manage loggers, performance measures, etc.

@project: Liver Perfusion
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from time import time_ns

import wx
import serial
import serial.tools.list_ports
import numpy as np

import pyPerfusion.PerfusionConfig as PerfusionConfig


def get_standard_log_format():
    return '%(asctime) s: %(name) s - %(levelname) s - %(message) s'


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
    ch = logging.FileHandler(PerfusionConfig.ACTIVE_CONFIG.get_folder('logs') / f'{filename}.log')

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


# utility function to return all available comports in a list
# typically used in a GUI to provide a selection of com ports
def get_avail_com_ports() -> list:
    ports = [comport.device for comport in serial.tools.list_ports.comports()]
    return ports


def get_epoch_ms():
    return np.uint64(time_ns() / 1_000_000.0)


# helper function to create a logger with consistent naming
# Use module_name.object_name to allow filtering by entire class (e.g. pyPump)
# as well as a specific instance (e.g., Pump1)
def get_object_logger(module_name: str, object_name: str):
    return logging.getLogger(f'{module_name}.{object_name}')


# borrowed from https://stackoverflow.com/questions/17275334/what-is-a-correct-way-to-filter-different-loggers-using-python-logging
class Whitelist(logging.Filter):
    def __init__(self, whitelist):
        super().__init__()
        self.whitelist = [logging.Filter(name) for name in whitelist]

    def filter(self, record):
        return any(f.filter(record) for f in self.whitelist)


class Blacklist(Whitelist):
    def filter(self, record):
        return not Whitelist.filter(self, record)


def only_show_logs_from(names_to_show):
    for handler in logging.root.handlers:
        handler.addFilter(Whitelist(names_to_show))


def never_show_logs_from(names_to_hide):
    for handler in logging.root.handlers:
        handler.addFilter(Blacklist(names_to_hide))


class WxTextCtrlHandler(logging.Handler):
    def __init__(self, ctrl):
        logging.Handler.__init__(self)
        self.ctrl = ctrl

    def emit(self, record):
        s = self.format(record) + '\n'
        wx.CallAfter(self.ctrl.WriteText, s)


def create_log_display(parent, logging_level, names_to_log):
    log_display = wx.TextCtrl(parent, wx.ID_ANY, size=(300, 100),
                              style=wx.TE_MULTILINE | wx.TE_READONLY)
    create_wx_handler(log_display, logging_level, names_to_log)
    return log_display


def create_wx_handler(wx_control, logging_level, names_to_log):
    handler = WxTextCtrlHandler(wx_control)
    handler.setLevel(logging_level)
    formatter = logging.Formatter('%(asctime) s - %(levelname) s - %(message) s',
                                  '%H:%M:%S')
    handler.setFormatter(formatter)
    loggers = logging.root.manager.loggerDict
    for log_name in names_to_log:
        logs_with_name = [logging.getLogger(lgr_name) for lgr_name in loggers.keys() if log_name in lgr_name]
        for lgr in logs_with_name:
            lgr.addHandler(handler)
