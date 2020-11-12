INTERNAL NIH USE ONLY

Some information presented is unofficial

# Sensors
Chris Hannemann stated in 2020-10-07 call that Dexcom sensors convert the raw sensor readings to glucose percentages before transfer over Bluetooth
## G6 Pro 
* Latest Sensor
* According to Chris Hannemann (2020-10-07 phone call), hardware is identical to standard G6, but has different firmware
* More locked down than standard G6
* Does not need prescription to obtain (?, recall his from phone call but not sure)
* Does not support Share feature
## G6 Commercial
* This is the "standard" G6 sensor
* Various on-line forums report problems with different serial number ranges
* Chris Hannemann (2020-10-07 phone call) stated this are probably due to minor firmware updates and usually get resolved quickly by online community
# Data Access
Dexcom does not officially support any third-party software or techniques for accessing data from Dexcom glucose sensors. However, they understand how important this is to the community and avoid breaking interoperability (Chris Hannemann phone call 2020-10-07).
## Nightscout
Open-source cloud-based system for remote monitoring of glucose monitors (including Dexcom).
* Known to work with G6 Commercial sensors, but does not currently support G6 Pro
* Uses Dexcom Share service for access to data
* Using Share service, access is real-time with normal network latencies
## Dexcom Smartphone App 
Standard smartphone app for use with Dexcom glucose sensors. Available on iOS and Android. Capable of forwarding data to cloud-based services and well as providing a local visualization of data.
## Dexcom Receiver
Hardware device provided by Dexcom which can receive data from sensor and forward to a cloud service or desktop. A Dexcom sensor can be simultaneously connected to a Dexcom Reciever and the Dexcom smartphone app. Receiver have a USB port and G6 commercial receivers should transmit the data in real-time over this port. It is currently unknown if the G6 Pro receiver has this capability.
According to Chris Hanneman (2020-10-13 phone call), this was a common way of getting data from Dexcom sensors in the early years of the DIY movement. 
## Dexcom Share 
Dexcom cloud service which can provide glucose readings to third-party apps. 
## Dexcom Follow  
Dexcom cloud service which uses the Share service to allow authorized users (e.g. parents, spouse, doctor) to view glucose readings from a given sensor
## Dexcom Clarity 
Dexcom desktop app for downloading data from Dexcom smartphone app or Dexcom receiver. 
Chris Hanneman (2020-10-07 phone call) stated the transfer is not real-time and would not be a reliable way of getting real-time data.
## Spike  
Open-source iOS application to directly get data from glucose sensors. Data is typically forwarded to an application like Nighscout
Unclear if Spike is capable of directly getting data from Dexcom G6 sensors. Most likely gets data from Dexcom Share service.
## xDrip  
Open-source Android application to directly get data from glucose sensors. Data is typically forwarded to an application like Nighscout
Unclear if Spike is capable of directly getting data from Dexcom G6 sensors. Most likely gets data from Dexcom Share service.
## Loop 
Open-source iOS application for use in DIY open pancreas systems. Uses internal iOS Bluetooth services to spy on incoming Dexcom Bluetooth data. Standard Dexcom smartphone app must be running and is used to configure and initiate data collection from sensor.
Chris Hanneman (2020-10-07 phone call) suggested we could develop an iOS app which accepted data from Loop and then forwarded to another location
## Direct Bluetooth communication
Dexcom does not provide documentation on directly communicating with the sensors. The bluetooth protocol used to interact with third-party infusion pumps is tightly held by Dexcom and unlikely to be shared (Chris Hanneman, 2020-10-13 phone call).