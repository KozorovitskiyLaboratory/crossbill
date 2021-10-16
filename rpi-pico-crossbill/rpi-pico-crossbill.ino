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
