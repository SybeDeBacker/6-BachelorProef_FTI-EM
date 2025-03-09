void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  Serial.println("Serial started");
}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available() > 0){
    String command_str = Serial.readStringUntil('\n');
    String response = execute_command(command_str);
    Serial.println(response);
  }
}

String execute_command(String data) {
  if (data.indexOf("A")==0){
    return "{\"status\":\"success\",\"message\":\"Aspirated\"}";
  }
  else if (data == "Ping"){
    return("{\"status\":\"success\",\"message\":\"pong\"}");
  }
  else {
    return "{\"status\":\"error\",\"message\":\"Sadly\"}";
  }
}