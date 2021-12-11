/* MIT License

Copyright (c) 2021 Manish Kumar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

// This file is written as a part of the Crossbill project and provides necessary software support for hardware integration.
// Crossbill is detailed at doi: https://doi.org/10.1101/2021.04.30.442190


//## Analog IN - Digital OUT to control two lasers output using one analog input
//# Pin configurations
//# analog input pin: GP26 : machine.ADC(26)
//# laser 1 (blue_laser) output pin: GP14 : machine.Pin(14, machine.Pin.OUT)
//# laser 2 (green_laser) output pin: GP15 : machine.Pin(15, machine.Pin.OUT)

int led_onboard = 25;
int analog_pin = 26;
int blue_laser = 14;
int green_laser = 15;
int val = 0; // hold voltage value 

void setup() {
  // put your setup code here, to run once:
  pinMode(led_onboard, OUTPUT);
  pinMode(analog_pin, INPUT);
  pinMode(blue_laser, OUTPUT);
  pinMode(green_laser, OUTPUT);
  //Serial.begin(115200);           //  setup serial
}

void loop() {
  // put your main code here, to run repeatedly:
  val = analogRead(analog_pin);  // read the input pin. 0-1023 belong to 0-3v3
  //Serial.println(val);          // debug value
  if (val < 300) {
    digitalWrite(led_onboard, LOW);
    digitalWrite(blue_laser, LOW);
    digitalWrite(green_laser, LOW);
  }
  else if (val < 600) {
    digitalWrite(led_onboard, HIGH);
    digitalWrite(blue_laser, HIGH);
    digitalWrite(green_laser, LOW);
  }
  else {
    digitalWrite(led_onboard, HIGH);
    digitalWrite(blue_laser, LOW);
    digitalWrite(green_laser, HIGH);
  }
}
