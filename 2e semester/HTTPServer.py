from PythonServer_Package import RobotObject, RobotServer

robot = RobotObject(serial_port='COM7', baud_rate=115200)
server = RobotServer(robot)
server.run(host='127.0.0.1', port=80)