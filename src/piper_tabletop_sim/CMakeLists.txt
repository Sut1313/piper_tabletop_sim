cmake_minimum_required(VERSION 3.8)
project(piper_tabletop_sim)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY config launch meshes urdf worlds
  DESTINATION share/${PROJECT_NAME}
)

install(
  FILES README.md NOTICE
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
