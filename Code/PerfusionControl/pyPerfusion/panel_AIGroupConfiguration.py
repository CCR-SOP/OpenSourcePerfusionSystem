# -*- coding: utf-8 -*-
""" Panel class for assinging sensor names to analog input hardware


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyHardware.SystemHardware import SYS_HW
import pyHardware.pyAI as pyAI


DEV_LIST = ['Dev1', 'Dev2', 'Dev3', 'Dev4', 'Dev5']
LINE_LIST = [f'{line}' for line in range(0, 9)]


class PanelAIGroup(wx.Panel):
    def __init__(self, parent, ai_device: pyAI.AIDevice):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self.device = ai_device

        self._rows = {}
        self._avail_dev = DEV_LIST
        self._avail_lines = LINE_LIST

        static_box = wx.StaticBox(self, wx.ID_ANY, label=f'{self.device.cfg.name} Configuration')
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_dev = wx.StaticText(self, label='NI Device Name')
        self.choice_dev = wx.Choice(self, wx.ID_ANY, choices=self._avail_dev)

        self.btn_save_cfg = wx.Button(self, label='Save')
        self.btn_load_cfg = wx.Button(self, label='Load')

        self.sizer_assignments = wx.FlexGridSizer(cols=2)
        self.sizer_assignments.AddGrowableCol(idx=1, proportion=1)
        self.btn_add_channel = wx.Button(self, label='Add Channel')

        self.rows = []

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()

        sizer_cfg = wx.GridSizer(cols=2)
        sizer_cfg.Add(self.label_dev, flags)
        sizer_cfg.Add(self.choice_dev, flags)

        sizer_cfg.Add(self.btn_load_cfg, flags)
        sizer_cfg.Add(self.btn_save_cfg, flags)

        sizer_cfg.Add(self.btn_add_channel, flags)
        self.sizer.Add(sizer_cfg)

        self.sizer.Add(self.sizer_assignments)
        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_save_cfg.Bind(wx.EVT_BUTTON, self.on_save_cfg)
        self.btn_load_cfg.Bind(wx.EVT_BUTTON, self.on_load_cfg)
        self.btn_add_channel.Bind(wx.EVT_BUTTON, self.on_add_channel)

    def on_save_cfg(self, evt):
        self.update_config_from_controls()
        self.device.write_config()

    def on_load_cfg(self, evt):
        self.device.read_config()
        self.choice_dev.SetStringSelection(self.device.cfg.device_name)
        for ch_name in self.device.cfg.ch_names:
            self.add_channel_controls(ch_name)

        self.Layout()
        self.Fit()
        self.parent.Fit()

    def add_channel_controls(self, ch_name: str):
        assignment = PanelAIAssignment(self, ai_channel=self.device.ai_channels[ch_name])
        btn_remove = wx.Button(self, label='Remove')

        self.sizer_assignments.Add(assignment, wx.SizerFlags().CenterVertical())
        self.sizer_assignments.Add(btn_remove, wx.SizerFlags().CenterHorizontal().CenterVertical())

        # create a lambda function to pass the btn and panel objects to the
        # on_remove callback. This makes it easy to delete both
        row = (assignment, btn_remove)
        self.rows.append(row)
        btn_remove.Bind(wx.EVT_BUTTON, lambda event, temp=row: self.on_remove(wx.CommandEvent(), temp))

    def on_add_channel(self, evt):
        dlg = wx.TextEntryDialog(self, 'Enter Channel Name (e.g. HA Flow)', '')
        if dlg.ShowModal() == wx.ID_OK:
            ch_name = dlg.GetValue()
            cfg = pyAI.AIChannelConfig(name=ch_name)
            self.device.add_channel(cfg)
            self.add_channel_controls(ch_name)

            self.Layout()
            self.Fit()
            self.parent.Fit()

    def on_remove(self, evt, temp=None):
        temp[0].Destroy()
        temp[1].Destroy()

        self.Layout()
        self.Fit()
        self.parent.Fit()

    def remove_all_channels(self):
        for row in self.rows:
            row[0].Destroy()
            row[1].Destroy()
        self.Layout()
        self.Fit()
        self.parent.Fit()

    def update_config_from_controls(self):
        self.device.cfg.device_name = self.choice_dev.GetStringSelection()
        for assignment in self.sizer_assignments.GetChildren():
            obj = assignment.GetWindow()
            if isinstance(obj, PanelAIAssignment):
                obj.update_config_from_controls()

    def update_controls_from_config(self):
        self.choice_dev.SetStringSelection(self.device.cfg.device_name)
        for assignment in self.sizer_assignments.GetChildren():
            obj = assignment.GetWindow()
            if isinstance(obj, PanelAIAssignment):
                obj.update_config_from_controls()


class PanelAIAssignment(wx.Panel):
    def __init__(self, parent, ai_channel: pyAI.AIChannel):
        super().__init__(parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self.ai_channel = ai_channel

        static_box = wx.StaticBox(self, wx.ID_ANY, label=f'{self.ai_channel.cfg.name}')
        self.sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

        self.label_line = wx.StaticText(self, label="AI Line")
        self.spin_line = wx.SpinCtrl(self, min=0, max=16)
        self.spin_line.SetValue(ai_channel.cfg.line)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 2).Center()

        self.sizer.Add(self.label_line, flags)
        self.sizer.Add(self.spin_line, flags)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass

    def update_config_from_controls(self):
        self.ai_channel.cfg.line = int(self.spin_line.GetValue())

    def update_controls_from_config(self):
        self.spin_line.SetValue(self.ai_channel.cfg.line)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.SetTitle(f'{device.cfg.name}')
        self.frame_sizer = wx.BoxSizer(wx.VERTICAL)

        self.panel = PanelAIGroup(self, ai_device=device)
        self.frame_sizer.Add(self.panel, 1, wx.EXPAND)
        self.Fit()
        self.Show()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        SYS_HW.stop()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
    PerfusionConfig.set_test_config()

    SYS_HW.load_hardware_from_config()
    SYS_HW.start()
    device = SYS_HW.ni_dev1

    app = MyTestApp(0)
    app.MainLoop()
