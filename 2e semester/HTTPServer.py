from PythonServer_Package import RobotObject, RobotServer

robot = RobotObject()
robot.set_safe_bounds([0, 1000])
server = RobotServer(robot)
server.run(host='127.0.0.1', port=80)
