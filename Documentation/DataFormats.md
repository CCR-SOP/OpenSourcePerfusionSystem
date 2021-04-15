# Data Formats

## Version 1:
Text-based header followed by a stream of samples stored in binary format
Header Lines:
File Format: 1
Sensor: {string containing sensor name (e.g. "HA Flow")}
Unit: {string containing units of data (e.g. "ml/min")}
Data Format: {string representing sample format (e.g. "float32")
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
Data Format: {string representing sample format (e.g. "float32")
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
Text-based header followed by a stream of timestamp/sample pairs in binary format
The timestamp is stored as the number of milliseconds from the start of the acquisition
Header Lines:
File Format: 3
Syringe: {string containing syringe name (e.g. "Insulin Syringe")}
Volume Unit: {string containing units of infusion volume (e.g. "ml")}
Rate Unit: {string containing units of infusion rate (e.g. "ml/min")}
Data Format: {string representing sample format (e.g. "float32")
Datapoints Per Timestamp: {number of datapoints stored per timestamp; default is 2 (infusion volume and infusion rate)}
Bytes per Timestamp: {number of bytes used to store the timestamp}
Start of Acquisition: {timestamp of acquisition in "YYYY-MM-DD_HH:SS" format}

After the header, data is immediately stored in described format.
The assumption is that infusion volume and infusion rate data are acquired at the same time
{Timestamp[1]}{InfusionVolume[1]}{InfusionRate[1]}{Timestamp[2]}{InfusionVolume[2]}{InfusionRate[2]}
For targeted infusions (i.e. those which stop after a certain volume of fluid has been delivered), InfusionVolume will be non-zero; for non-targeted (i.e. continuous) infusions, InfusionVolume will be '2222' or '1111'; for these continuous infusions, data will be recorded both when the infusion is started ('2222') and stopped ('1111'); if a non-continuous infusion is interrupted before it can be completely delivered, '8888' will be written