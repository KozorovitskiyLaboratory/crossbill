# Crossbill
Crossbill project covers an open access single objective light-sheet microscopy platform. This repository mainly covers the software aspect of this project.


## RPi_pico_Crossbill
This contains an arduino compatible code which can be uploaded to a Raspberry Pi Pico board to be used with Crossbill microscope.

### How to use Arduino IDE to program RPi pico?

1.	Enable RP2040 boards in Tools>Boards>Boards Manager. Look for 'pico' in the search box to get to this board installation.
2.	Connect Pico with ‘bootsel’ pressed
3.	Goto Files>Examples>Basics>Blink and click on upload. This makes the board identifiable by the arduino IDE. 
4.	Check for ports and connect to the correct port where Pico is identified. 
5.	Start programming like a normal arduino board. 

### Pin configurations
- analog input pin: GP26 : machine.ADC(26)
- laser 1 (blue_laser) output pin: GP14 : machine.Pin(14, machine.Pin.OUT)
- laser 2 (green_laser) output pin: GP15 : machine.Pin(15, machine.Pin.OUT)
