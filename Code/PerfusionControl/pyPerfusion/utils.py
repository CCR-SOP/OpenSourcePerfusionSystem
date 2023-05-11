# -*- coding: utf-8 -*-
"""Utils to manage loggers, performance measures, etc.

@project: Liver Perfusion
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from logging.handlers import RotatingFileHandler
from time import time_ns
import sys
import colorlog

import wx
import serial
import serial.tools.list_ports
import numpy as np

import pyPerfusion.PerfusionConfig as PerfusionConfig


def get_epoch_ms():
    return np.uint64(time_ns() / 1_000_000.0)


# utility function to return all available comports in a list
# typically used in a GUI to provide a selection of com ports
def get_avail_com_ports() -> list:
    ports = [comport.device for comport in serial.tools.list_ports.comports()]
    return ports


def get_standard_log_format():
    return '%(asctime) s: %(name)s | %(levelname)s | ' \
           '%(filename)s:%(lineno)s | %(message) s'


def get_color_standard_log_format():
    return '%(asctime) s: %(blue)s%(name)s%(reset)s | %(log_color)s%(levelname)s%(reset)s | ' \
           '%(yellow)s%(filename)s:%(lineno)s%(reset)s | %(message) s'


def get_gui_log_format():
    return '%(asctime)s--%(last_name)s--%(message)s'


class MyGuiFormatter(logging.Formatter):
    def format(self, record):
        orig_format = self._style._fmt

        if record.levelno > logging.INFO:
            self._style._fmt = f'++%(levelname)s++\n{orig_format}\n++END %(levelname)s++'

        result = logging.Formatter.format(self, record)

        self._style._fmt = orig_format

        return result


def setup_stream_logger(lgr, level):
    lgr.setLevel(level)
    stdout = colorlog.StreamHandler(stream=sys.stdout)
    stdout.setLevel(level)
    fmt = colorlog.ColoredFormatter(get_color_standard_log_format())

    stdout.setFormatter(fmt)
    lgr.addHandler(stdout)


def setup_file_logger(lgr, level, filename=None):
    if not filename:
        filename = lgr.name
    lgr.setLevel(level)
    handler = RotatingFileHandler(PerfusionConfig.ACTIVE_CONFIG.get_folder('logs') / f'{filename}.log',
                                  backupCount=3)
    handler.doRollover()

    handler.setLevel(level)
    formatter = logging.Formatter(get_standard_log_format())
    handler.setFormatter(formatter)
    lgr.addHandler(handler)


def disable_matplotlib_logging():
    # matplotlib logs to the root logger and can create
    # a lot of debug messages, this will only log warning
    # or higher levels
    lgr = logging.getLogger('matplotlib')
    lgr.setLevel(logging.WARNING)


# helper function to create a logger with consistent naming
# Use module_name.object_name to allow filtering by entire class (e.g. pyPump)
# as well as a specific instance (e.g., Pump1)
def get_object_logger(module_name: str, object_name: str):
    return logging.getLogger(f'{module_name}.{object_name}')


class Whitelist(logging.Filter):
    def __init__(self, whitelist):
        super().__init__()
        self.whitelist = whitelist

    def filter(self, record):
        matches = [name in record.name for name in self.whitelist]
        return any(matches)


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
        if bool(self.ctrl):
            wx.CallAfter(self.ctrl.WriteText, s)
        else:
            logging.getLogger().error(f'Attempt to log to deleted TextCtrl {self.ctrl} with'
                                      f'message {self.format(record)}')


def create_log_display(parent, logging_level, names_to_log, use_last_name=False):
    log_display = wx.TextCtrl(parent, wx.ID_ANY, size=(300, 100),
                              style=wx.TE_MULTILINE | wx.TE_READONLY)
    create_wx_handler(log_display, logging_level, names_to_log, use_last_name)
    return log_display


class LastPartFilter(logging.Filter):
    def filter(self, record):
        record.last_name = record.name.rsplit('.', 1)[-1]
        return True


def create_wx_handler(wx_control, logging_level, names_to_log, use_last_name=False):
    handler = WxTextCtrlHandler(wx_control)
    handler.setLevel(logging_level)
    handler.addFilter(Whitelist(names_to_log))
    handler.addFilter(LastPartFilter())
    handler.setFormatter(MyGuiFormatter(get_gui_log_format(), '%a %I:%M:%S %p'))
    logging.getLogger().addHandler(handler)


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.critical('Uncaught exception, ', exc_info=(exc_type, exc_value, exc_traceback))
    # raise exc_type


def catch_unhandled_exceptions():
    sys.excepthook = handle_exception


def setup_default_logging(app_name, stream_level):
    catch_unhandled_exceptions()

    lgr = logging.getLogger()
    lgr.setLevel(logging.DEBUG)
    disable_matplotlib_logging()
    setup_stream_logger(lgr, stream_level)
    setup_file_logger(lgr, logging.DEBUG, app_name)
