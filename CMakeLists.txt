cmake_minimum_required(VERSION 3.0.2)
project(ur5_imitation)

find_package(catkin REQUIRED COMPONENTS
  rospy
  roscpp
  std_msgs
  sensor_msgs
  geometry_msgs
  trajectory_msgs
  control_msgs
  tf
  cv_bridge
  image_transport
)

catkin_package(
  CATKIN_DEPENDS 
    rospy 
    roscpp 
    std_msgs 
    sensor_msgs 
    geometry_msgs 
    trajectory_msgs
    control_msgs
    tf
    cv_bridge
    image_transport
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

# 安装Python脚本
catkin_install_python(PROGRAMS
  scripts/leader_follower_teleop.py
  scripts/data_recorder.py
  scripts/train_policy.py
  scripts/execute_policy.py
  scripts/keyboard_teleop.py
  scripts/evaluate_policy.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

# 安装launch文件
install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)

# 安装配置文件
install(DIRECTORY config/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/config
)
