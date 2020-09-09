# Centrifugal Pump Control
- Hugo Sachs Elektronik (Harvard Apparatus)
- BVP-BP
	- D-Sub 15 
	- Gender?? 
	- Pin 1 – Ground 
	- Pin 2 – Remote (connect to ground to activate remote interface)
	- Pin 3 – Start/Stop (connect to ground to start)
	- Pin 5 – Input (speed control, DIP switch controls parameters)
		- Supports 0-5V, 0-10V, 0-20mA, 4-20mA
	- Pin 7 – 36VDC power
		- Output, Max load 1A
	- Pin 9 – Motor Speed
		- 0-5V output proportional to speed 0-3000rpm
	- Pin 10 – 5VDC 
		- Output
	- Pin 12 – Overload Status
		- Open collector, active low
	- Pin 13 
		- If connected to Pin1, speed can be set on front-panel instead of Pin 5


# VCS Control
- Warner Instruments Valve Control System
- 25-pin female D-sub connector
	- Alternate Row Pin Numbering (even pins on short row)
	- Input Pins: 6-21 (Bit 1-16, respectively, level controlled)
	- Ground: Pins 1-5, 22-25
	- TTL: VIL <= 0.8V, VIH >=2V

# Flow Meter
- Hugo Sachs Elektronik TTFM-2 Type 714
- BNC
- +/- 5V Analog Output
- Output Freq Range depends on filter setting
- Shows pulsatile flow at filter positions 100Hz, 30Hz
- Show avg flow at filter position 0.1Hz
- Zero Calibration = 0V out, Scale Factor flow = 1V +/-2%
- Output Resistance = 500ohm
- Full Range for flows = +/-5V (bi-directional flows, +/-4 times scale factor)


# Syringe Control
- Harvard Apparatus Pump 11 Elite
- 15-pin female D-sub connector
- Digital Input: Pin 2 (Falling-edge triggered method event)
- Digital Input: Pin 3 (footswitch input, edge-triggered toggle or start/stop level control)
- Ground: Pins 9-13
- VIH >= 2V, IIH <=20uA
- VIL <= 0.4V, IIL <=0.5mA

# Pressure Transducer
- APT300, 733862
	- Hepatic Artery
	- 5uV/V/mmHg
	- Interfaces to PLUGSYS Amp Module TAM-A
- P75, 730020
	- Venous Pressure 
	- 1mV/mmHg
	- Interfaces to PLUGSYS Amp Module TAM-A
- TAM-A 730065
	- Front panel controls for calibration, low pass filter, and gain settings
	- BNC connector for output
	- +/-10V fixed
	- Will need to know gain settings for conversion to mmHg
	- Jumper J4 controls pulsatile output to BNC




