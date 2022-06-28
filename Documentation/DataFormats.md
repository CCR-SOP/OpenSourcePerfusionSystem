# Data Formats

## Version 1:
Text-based header followed by a stream of samples stored in binary format
Header Lines:
File Format: 1
Sensor: {string containing sensor name (e.g. "HA Flow")}
Unit: {string containing units of data (e.g. "ml/min")}
Data Format: {string representing sample format (e.g. "float32")}
Sampling Period (ms): {number represeting the sampling period in milliseconds}
Start of Acquisition: {timestamp of acquisition in "YYYY-MM-DD_HH:SS" format}

After header, data is immediately stored in described format.
The assumption is each sample is acquired at the specified sampling period with no data losses
{Sample[1]}{Sample[2]}{Sample[3]} etc

## Version 2:
Text-based header followed by a stream of timestamp/sample pairs in binary format
The timestamp is stored as the number of milliseconds from the start of the acquisition
Header Lines:
File Format: 2
Sensor: {string containing sensor name (e.g. "HA Flow")}
Unit: {string containing units of data (e.g. "ml/min")}
Data Format: {string representing sample format (e.g. "float32")}
Samples Per Timestamp: {number of samples stored per timestamp}
Bytes per Timestamp: {number of bytes used to store the timestamp}
Sampling Period (ms): {number represeting the sampling period in milliseconds}
Start of Acquisition: {timestamp of acquisition in "YYYY-MM-DD_HH:SS" format}

After the header, data is immediately stored in described format.
If "Samples Per Timestamp" is one, data is stored as:
{Timestamp[1]}{Sample[1]}{Timestamp[2]}{Sample[2]} etc
The "Sampling Period (ms)" will represent the expected time difference between timestamps

If "Samples Per Timestamp" is greater than one, data is stored as:
{Timestamp[1]}{Sample[1]}...{Sample[n]}{Timestamp[2]}{Sample[1]}...{Sample[n]}
The samples after each time stamp are assumed to be separated by the "Sampling Period (ms)"

## Version 3:
Used for streaming syringe data
Text-based header followed by a stream of timestamp/sample pairs in binary format
The timestamp is stored as the number of milliseconds from the start of the acquisition
Header Lines:
File Format: 3
Syringe: {string containing syringe name (e.g. "Insulin")}
Volume Unit: {string containing units of infusion volume ("ul")}
Rate Unit: {string containing units of infusion rate ("ul/min")}
Data Format: {string representing sample format (e.g. "float32")
Datapoints Per Timestamp: {number of datapoints stored per timestamp; default is 2 (infusion volume (uL) and infusion rate (uL/min))}
Bytes per Timestamp: {number of bytes used to store the timestamp}
Start of Acquisition: {timestamp of acquisition in "YYYY-MM-DD_HH:SS" format and in milliseconds from start format}

After the header, data is immediately stored in described format.
The assumption is that infusion volume and infusion rate data are acquired at the same time
{Timestamp[1]}{InfusionVolume[1]}{InfusionRate[1]}{Timestamp[2]}{InfusionVolume[2]}{InfusionRate[2]}
For targeted infusions (i.e. those which stop after a certain volume of fluid has been delivered), InfusionVolume will be non-zero; for non-targeted (i.e. continuous) infusions, InfusionVolume will be '-2' or '-1'; for these continuous infusions, data will be recorded both when the infusion is started ('-2') and stopped ('-1')

## Version 4:
Text-based header followed by a stream of timestamp/sample pairs in binary format
Header Lines:
File Format: 4
Instrument: {string containing name for the CDI Instrument}
Data Format: {string representing sample format (e.g. "int8")
Sample Description: {Each sample includes Time, "Arterial" pH, "Arterial" pC02, "Arterial" pO2, "Arterial" Temperature, "Arterial" HCO3-, "Arterial" Base Excess, Calculated O2 sat, K, VO2, Pump Flow, BSA, "Venous" pH, "Venous" pCO2, "Venous" pO2, "Venous" Temperature, Measured O2 sat, Hct, and Hb}
Bytes per Sample: {number of bytes used to store the sample}
Bytes per Timestamp: {number of bytes used to store the timestamp}
Start of Acquisition: {timestamp of acquisition in "YYYY-MM-DD_HH:SS" format, and in "milliseconds from start" format}

## Version 5:
Text-based header followed by a stream of timestamp/sample pairs in binary format
The timestamp is stored as the number of milliseconds from the start of the acquisition
Header Lines:
File Format: 5
Instrument: {string containing name for the GB100 mixer}
Data Format: {string representing sample format (e.g. "float32")
Datapoints Per Timestamp: {number of datapoints stored per timestamp; default is 6 (Gas 1 ID, Gas 2 ID, Gas 1 Percentage, Gas 2 Percentage, Total Flow (ml/min), and Working Status (0 for OFF, 1 for ON)}
Bytes per Timestamp: {number of bytes used to store the timestamp}
Start of Acquisition: {timestamp of acquisition in "YYYY-MM-DD_HH:SS" format, and in "milliseconds from start" format}

## Version 6:
Used for streaming Dexcom data
Text-based header followed by a stream of timestamp/sample pairs in binary format
The timestamp is stored as the number of milliseconds from the start of the acquisition
Header Lines:
File Format: 6
Sensor: {string containing name of sensor (e.g. "Portal Vein Glucose")}
Glucose Unit: {"mg/dL"}
Data Format: {string representing sample format (e.g. "float32")"
Datapoints Per Timestamp: {number of datapoints stored per timestamp; default is 1 (glucose)}
Bytes per Timestamp: {number of bytes used to store the timestamp}
Start of Acquisition: {timestamp of acquisition in "YYYY-MM-DD_HH:SS" format and in milliseconds from start format}

## Version 7:
Text-based header followed by a stream of timestamp/sample pairs in binary format
The timestamp is stored as the number of milliseconds from the start of the acquisition
Header Lines:
File Format: 7
Data Source: {string specifying the source of the data, e.g. 'Automated Dialysis Pumps'}
Data Format: {string representing sample format (e.g. "float32")
Datapoints Per Timestamp: {number of datapoints stored per timestamp; default is 3 (dialysate inflow rate (ml/min), dialysate outflow rate (ml/min), and working status (0 for Off, 1 for On)}
Bytes per Timestamp: {number of bytes used to store the timestamp}
Start of Acquisition: {timestamp of acquisition in "YYYY-MM-DD_HH:SS" format, and in "milliseconds from start" format}