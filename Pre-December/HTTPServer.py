from PythonServer_Package import RobotObject, RobotServer

robot = RobotObject()
server = RobotServer(robot)
server.run(host='127.0.0.1', port=80, debug=False)
