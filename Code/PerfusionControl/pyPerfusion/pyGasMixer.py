"""Panel class for controlling gas mix in GB100 gas mixers

@project: Liver Perfusion, NIH
@author: Stephie Lux, NIH

"""
from enum import Enum
import wx
import logging
import pyPerfusion.utils as utils
from pyPerfusion.plotting import PanelPlotting, TSMDexPanelPlotting, TSMDexPanelPlotLT, TSMDexSensorPlot, SensorPlot
from pyHardware.pyGB100 import GB100
import pyPerfusion.PerfusionConfig as LP_CFG
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyHardware.pyAI import AIDeviceException
from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.FileStrategy import StreamToFile
from pyHardware.pyAO_NIDAQ import NIDAQ_AO



class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True

if __name__ == "__main__":
    LP_CFG.set_base(basepath='~/Documents/LPTEST')
    LP_CFG.update_stream_folder()
    utils.setup_default_logging(filename='panel_gb100_saturation_monitor')
    app = MyTestApp(0)
    app.MainLoop()