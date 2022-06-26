import os
from pathlib import Path
from matplotlib import pyplot as plt
import numpy as np
from pyHardware.PHDserial import PHDserial
from pyHardware.pySaturationMonitor import TSMSerial
from pyHardware.pyGB100 import GB100
from pyHardware.pyDialysatePumps import DialysatePumps

class ReadBinaryData:
    def __init__(self, filename):
        self.path = Path(os.path.expanduser('~')) / 'Documents/LPTEST/LiverPerfusion/data'
        self.filename = Path(f'{filename}')

    def read_pressure_flow_data(self, sampling_period_ms, title, y_axis):  # Data Version 1
        _fid = open(self.path / self.filename.with_suffix('.dat'), 'rb')
        data_type = np.dtype(np.float32)
        try:
            data = np.memmap(_fid, dtype=data_type, mode='r')
        except ValueError:
            data = []
        times = []
        for value in range(len(data)):
            times.append(value * sampling_period_ms / 1000)
        plt.figure()
        plt.plot(times, data)
        plt.title(title)
        plt.xlabel('Time (s)')
        plt.ylabel(y_axis)
        return data

    def read_syringe_data(self):  # Data Version 3
        x = PHDserial('PHDserial')
        x._full_path = self.path
        x._filename = self.filename
        timestamp_matrix, data_matrix = x.get_data()
    #    syringe_datapoints = []
    #    time_datapoints = []
   #     for value in range(len(timestamp_matrix)):
   #         if data_matrix[value][0] > 0:
   #             syringe_datapoints.append()
   #         elif data_matrix[value][0] < 0:
   #             if data_matrix[value][0] == -2:
   #                 syringe_datapoints.append(data_matrix[value][1])
   #                 time_datapoints.append(timestamp_matrix[value])
   #             elif data_matrix[value][0] == -1:
   #                 syringe_datapoints.append(data_matrix[value][1])
   #                 time_datapoints.append(0)
        return timestamp_matrix, data_matrix

    def read_cdi_data(self):  # Data Version 4
        x = TSMSerial('CDI')
        x._full_path = self.path
        x._filename = self.filename
        timestamp_matrix, data_matrix = x.get_data()
        pH_datapoints = []
        ph_time = []
        pCO2_datapoints = []
        pCO2_time = []
        pO2_datapoints = []
        pO2_time = []
        temp_datapoints = []
        temp_time = []
        bicarb_datapoints = []
        bicarb_time = []
        BE_datapoints = []
        BE_time = []
        K_datapoints = []
        K_time = []
        o2sat_datapoints = []
        o2sat_time = []
        hct_datapoints = []
        hct_time = []
        hb_datapoints = []
        hb_time = []
        for value in range(len(data_matrix)):
            try:
                float(data_matrix[value][9:13])
                pH_datapoints.append(float(data_matrix[value][9:13]))
                ph_time.append(timestamp_matrix[value])
            except ValueError:
                pass
            try:
                float(data_matrix[value][15:18])
                pCO2_datapoints.append(float(data_matrix[value][15:18]))
                pCO2_time.append(timestamp_matrix[value])
            except ValueError:
                pass
            try:
                float(data_matrix[value][20:23])
                pO2_datapoints.append(float(data_matrix[value][20:23]))
                pO2_time.append(timestamp_matrix[value])
            except ValueError:
                pass
            try:
                float(data_matrix[value][24:28])
                temp_datapoints.append(float(data_matrix[value][24:28]))
                temp_time.append(timestamp_matrix[value])
            except ValueError:
                pass
            try:
                float(data_matrix[value][30:32])
                bicarb_datapoints.append(float(data_matrix[value][30:32]))
                bicarb_time.append(timestamp_matrix[value])
            except ValueError:
                pass
            try:
                float(data_matrix[value][35:37])
                BE_datapoints.append(float(data_matrix[value][35:37]))
                BE_time.append(timestamp_matrix[value])
            except ValueError:
                pass
            try:
                float(data_matrix[value][45:48])
                K_datapoints.append(float(data_matrix[value][45:48]))
                K_time.append(timestamp_matrix[value])
            except ValueError:
                pass
            try:
                float(data_matrix[value][84:87])
                o2sat_datapoints.append(float(data_matrix[value][84:87]))
                o2sat_time.append(timestamp_matrix[value])
            except ValueError:
                pass
            try:
                float(data_matrix[value][90:92])
                hct_datapoints.append(float(data_matrix[value][90:92]))
                hct_time.append(timestamp_matrix[value])
            except ValueError:
                pass
            try:
                float(data_matrix[value][95:99])
                hb_datapoints.append(float(data_matrix[value][95:99]))
                hb_time.append(timestamp_matrix[value])
            except ValueError:
                pass
        plt.figure()
        plt.scatter(ph_time, pH_datapoints)
        plt.legend(['pH'])
        plt.title('pH')
        plt.xlabel('Time (ms)')
        plt.ylabel('pH')
        plt.figure()
        plt.scatter(pCO2_time, pCO2_datapoints)
        plt.legend(['pCO2'])
        plt.title('pCO2')
        plt.xlabel('Time (ms)')
        plt.ylabel('pCO2 (mmHg)')
        plt.figure()
        plt.scatter(pO2_time, pO2_datapoints)
        plt.legend(['pO2'])
        plt.title('pO2')
        plt.xlabel('Time (ms)')
        plt.ylabel('pO2 (mmHg)')
        plt.figure()
        plt.scatter(temp_time, temp_datapoints)
        plt.legend(['Temperature'])
        plt.title('Temperature')
        plt.xlabel('Time (ms)')
        plt.ylabel('Temperature (C)')
        plt.figure()
        plt.scatter(bicarb_time, bicarb_datapoints)
        plt.legend(['Bicarbonate'])
        plt.title('Bicarbonate')
        plt.xlabel('Time (ms)')
        plt.ylabel('Bicarbonate (mEq/L)')
        plt.figure()
        plt.scatter(BE_time, BE_datapoints)
        plt.legend(['Base Excess'])
        plt.title('Base Excess')
        plt.xlabel('Time (ms)')
        plt.ylabel('BE (mEq/L)')
        plt.figure()
        plt.scatter(K_time, K_datapoints)
        plt.legend(['Potassium'])
        plt.title('Potassium')
        plt.xlabel('Time (ms)')
        plt.ylabel('Potassium (mmol/L)')
        plt.figure()
        plt.scatter(o2sat_time, o2sat_datapoints)
        plt.legend(['Oxygen Saturation'])
        plt.title('Oxygen Saturation')
        plt.xlabel('Time (ms)')
        plt.ylabel('Oxygen Saturation (%)')
        plt.figure()
        plt.scatter(hct_time, hct_datapoints)
        plt.legend(['Hematocrit'])
        plt.title('Hematocrit')
        plt.xlabel('Time (ms)')
        plt.ylabel('Hct (%)')
        plt.figure()
        plt.scatter(hb_time, hb_datapoints)
        plt.legend(['Hemoglobin'])
        plt.title('Hemoglobin')
        plt.xlabel('Time (ms)')
        plt.ylabel('Hb (g/dL)')
        return timestamp_matrix, data_matrix

    def read_gb100_data(self):  # Data Version 5
        x = GB100('GB100')
        x._full_path = self.path
        x._filename = self.filename
        timestamp_matrix, data_matrix = x.get_data()
        GAS_TYPES = {1: 'Air', 2: 'Nitrogen', 3: 'Oxygen', 4: 'Carbon Dioxide'}
        gas_1 = GAS_TYPES[data_matrix[0][0]]
        gas_2 = GAS_TYPES[data_matrix[0][1]]
        flow_datapoints = []
        gas_1_percentage_datapoints = []
        gas_2_percentage_datapoints = []
        for value in range(len(timestamp_matrix)):
            if data_matrix[value][5] == 1:
                flow_datapoints.append(data_matrix[value][4])
                gas_1_percentage_datapoints.append(data_matrix[value][2])
                gas_2_percentage_datapoints.append(data_matrix[value][3])
            elif data_matrix[value][5] == 0:
                flow_datapoints.append(0)
                gas_1_percentage_datapoints.append(0)
                gas_2_percentage_datapoints.append(0)
        plt.figure()
        plt.scatter(timestamp_matrix, flow_datapoints)
        plt.legend(['Gas Flow'])
        plt.title('Total Gas Flow')
        plt.xlabel('Time (ms)')
        plt.ylabel('Flow (ml/min)')
        plt.figure()
        plt.scatter(timestamp_matrix, gas_1_percentage_datapoints)
        plt.scatter(timestamp_matrix, gas_2_percentage_datapoints)
        plt.legend([gas_1 + ' %', gas_2 + ' %'])
        plt.title('Gas Percentages')
        plt.xlabel('Time (ms)')
        plt.ylabel('%')
        return timestamp_matrix, data_matrix

    def read_dexcom_data(self):  # Data Version 6
        pass

    def read_dialysis_flow_rate_data(self):  # Data Version 7
        x = DialysatePumps('Dialysate Pumps')
        x._full_path = self.path
        x._filename = self.filename
        timestamp_matrix, data_matrix = x.get_data()
        inflow_datapoints = []
        outflow_datapoints = []
        for value in range(len(timestamp_matrix)):
            if data_matrix[value][2] == 1:
                inflow_datapoints.append(data_matrix[value][0])
                outflow_datapoints.append(data_matrix[value][1])
            else:
                inflow_datapoints.append(0)
                outflow_datapoints.append(0)
        plt.figure()
        plt.scatter(timestamp_matrix, inflow_datapoints)
        plt.scatter(timestamp_matrix, outflow_datapoints)
        plt.legend(['Dialysate Inflow', 'Dialysate Outflow'])
        plt.title('Dialysate Flow Rates')
        plt.xlabel('Time (ms)')
        plt.ylabel('Flow Rate (ml/min)')
        return timestamp_matrix, data_matrix
