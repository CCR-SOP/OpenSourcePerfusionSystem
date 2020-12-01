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

-Connected pins 2 and 3 to pin 1(GND), and connected pin 5 to AO to successfully vary pump speed/gain remote control


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
- Gained remote control through USB

# Peristaltic Pump
- Ismatec Ecoline VC-280
- 3.5-350 RPM
- See pages 25 and 26 of manual for pump flow rates based on ID/wall thickness of tubing
- 8-pin socket DIN 45326
- Pin 1, GND
- Pin 2, shield (GND)
	- used to couple cable shielding to ground
- Pin 3, stop-run
	- Pump startes when connected to GND
- Pin 4, direction
	- If open, pumps run CW
	- if grounded, pump runs CCW
- Pin 5, speed In
	- 0-5V, 0-10V, 0-20mA, 4-20mA, set by DIP S1
- Pin 6, speed intern
	- if connected to ground, speed controlled by front panel
- Pin 7, +5V
	- Output, Ri = 330ohm
- Pin 8, unused
- Connected Pin 3 to Pin 1, and connected Pin 5 to AO to vary speed of pump successfully/gain remote control


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
	
# BGA circuit
- Reglo 78018
	- For BGA circuit
	- Front Panel Controls
	- DB-25 connector (see page 3-40 in manual for full pin out)
		- Pin 1 - Speed Control Voltage (0-10V; can be changed to 0-5V using touchscreen)
		- Pin 3 - Speed Control Input Reference (GND)
		- Pin 15 - Remote Start/Stop input
		- Pin 16 - Remote CW/CCW Input
		- Pin 17 - Remote Reference (GND)
		- Remote pins are contact closure to GND

- Connected pins 3, 15, and 17 to GND, and pin 1 to AO to successfully gain remote control/vary speed 




