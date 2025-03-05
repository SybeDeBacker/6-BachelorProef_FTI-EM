/*
Program: Receive Integers From Raspberry Pi
File: receive_ints_from_raspberrypi_strings.ino
Description: Receive integers from a Raspberry Pi
Author: Addison Sears-Collins
Website: https://automaticaddison.com
Date: July 5, 2020
*/
#include <MobaTools.h>

const int dirPin = 1;
const int stepPin = 2;
const int enablePin = 7;
// Initialize the integer variables
int STEPPER_PIPET_MICROSTEPS = 16; //microsteps
float LEAD = 1; // mm/rev
float VOLUME_TO_TRAVEL_RATIO = 0.1; // ml/mm
 
MoToStepper stepper(long(200*STEPPER_PIPET_MICROSTEPS), STEPDIR);

void setup(){
  // Set the baud rate  
  Serial.begin(9600); 
  
}
 
void loop() {
  // Initialize the String variables
  if (Serial.available() > 0){
    String command_str = Serial.readStringUntil('\n');
    String response = execute_command(command_str);
    Serial.println(response);
  }
}

String execute_command(String data) {
  if (data.indexOf('A')==0){
    float aspiration_volume = data.substring(1,data.indexOf('R')-1).toFloat();
    float asprition_rate = data.substring(data.indexOf('R')+1,data.length()).toFloat();
    aspirate(aspiration_volume, asprition_rate);
    return aspirate(aspiration_volume, asprition_rate);
  }
  else if (data.indexOf('D')==0){
    float dispense_volume = data.substring(1,data.indexOf('R')-1).toFloat();
    float dispense_rate = data.substring(data.indexOf('R')+1,data.length()).toFloat();
    
    return dispense(dispense_volume, dispense_rate);
  }
  else if (data == "E"){
    return eject();
  }
  else if (data.indexOf('S')==0){
    int microsteps = data.substring(1,data.indexOf('L')-1).toInt();
    float lead = data.substring(data.indexOf('L')+1,data.indexOf('V')-1).toFloat();
    float volume_tt_ratio = data.substring(data.indexOf('V')+1,data.length()).toFloat();

    if (microsteps > 0){
      STEPPER_PIPET_MICROSTEPS = microsteps;
    }
    if (lead > 0){
      LEAD = microsteps;
    }
    if (volume_tt_ratio > 0){
      VOLUME_TO_TRAVEL_RATIO = volume_tt_ratio;
    }
    return ("{'status':'succes'}");
  }
  else if (data == "Ping"){
    return("{'status':'success','message':'pong'}");
  }
  else if (data == "Z"){
    return("{'status':'success'}");
  }
  else {return ("{'status':'error','message':'No valid parameters given " +String(data)+"'}");}
}

String aspirate(float aspiration_volume, float aspiration_rate){
  float travel = aspiration_volume/VOLUME_TO_TRAVEL_RATIO;
  float rotations = travel/LEAD;
  int steps = round(rotations*200*STEPPER_PIPET_MICROSTEPS);

  float speed = aspiration_rate/VOLUME_TO_TRAVEL_RATIO;
  float rpm = speed/LEAD;
  //stepper.setSpeed(rpm);
  //stepper.move(steps);
  //while(stepper.moving());
  return "{'status':'succes', 'message': Aspirated '"+String(steps)+" steps at "+String(rpm)+" rpm'}";
}

String dispense(float dispense_volume, float dispense_rate){
  float travel = -dispense_volume/VOLUME_TO_TRAVEL_RATIO;
  float rotations = travel/LEAD;
  int steps = round(rotations*200*STEPPER_PIPET_MICROSTEPS);

  float speed = dispense_rate/VOLUME_TO_TRAVEL_RATIO;
  float rpm = speed/LEAD;

  return "{'status':'succes', 'message': Dispensed '"+String(steps)+" steps at "+String(rpm)+" rpm'}";
}

String eject(){
  return "{'status':'succes'}";
}