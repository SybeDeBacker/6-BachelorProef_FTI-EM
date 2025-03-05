/*
Program: Receive Integers From Raspberry Pi
File: receive_ints_from_raspberrypi_strings.ino
Description: Receive integers from a Raspberry Pi
Author: Addison Sears-Collins
Website: https://automaticaddison.com
Date: July 5, 2020
*/
 
// Initialize the integer variables
int dispense_volume = 0;
int dispense_rate = 0;

int stepper_pipet_microsteps = 16; //microsteps
int pipet_lead = 1; // mm/rev
int VolumeToTravel_ratio = 0.1; // ml/mm
 
void setup(){
  // Set the baud rate  
  Serial.begin(9600);
   
}
 
void loop() {
  // Initialize the String variables
  char command_str = get_command();

  if (!isArrayAllZeroes(steps_array, AMOUNT_OF_MOTORS)) {
    // Print the array only if it is not all zeroes
    for (int i = 0; i < AMOUNT_OF_MOTORS; ++i) {
      Serial.print(steps_array[i]);
      if (i < AMOUNT_OF_MOTORS - 1) {
        Serial.print(",");
      }
    }
    Serial.println();
  } else {

  }
}


void command() {
  if (Serial.available() > 0) {
    // Read string until the new line character
    String data = Serial.readStringUntil('\n');

    if (data.indexOf('A')==0){
      int aspiration_volume = data.substring(1,data.indexOf('R')-1);
      int asprition_rate = data.substring(data.indexOf('R')+1,data.end());
      aspirate(aspiration_volume, asprition_rate);
    }
    else if (data.indexOf('D')==0){
      int dispense_volume = data.substring(1,data.indexOf('R')-1);
      int dispense_rate = data.substring(data.indexOf('R')+1,data.end());
      dispense(dispense_volume, dispense_rate);
    }
    else if (data.indexOf('E')==0){
      eject();
    }
    int comma_position = data.indexOf(',');
    stepper_steps_str = data.substring(0, comma_position);
    stepper_steps = stepper_steps_str.toInt();
    steps_array[i] = stepper_steps;

      data = data.substring(comma_position + 1);
    }

    // Compute a sum to prove we have integers
    int sum = steps_array[0] + steps_array[1];
    Serial.println("Checksum of first two integers: " + String(sum));
  }
}

bool isArrayAllZeroes(int arr[], int size) {
  for (int i = 0; i < size; i++) {
    if (arr[i] != 0) {
      return false; // Return false if any element is not zero
    }
  }
  return true; // Return true if all elements are zero
}
