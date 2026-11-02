cmake_minimum_required(VERSION 3.8)
project(robot_bringup)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

install(DIRECTORY config/
  DESTINATION share/${PROJECT_NAME}/config
)

install(DIRECTORY web/
  DESTINATION share/${PROJECT_NAME}/web
  FILES_MATCHING
    PATTERN "*.html"
    PATTERN "*.js"
    PATTERN "*.css"
)

install(PROGRAMS scripts/ros2_to_http.py
  DESTINATION lib/${PROJECT_NAME}
)

install(PROGRAMS scripts/vision_distance.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()