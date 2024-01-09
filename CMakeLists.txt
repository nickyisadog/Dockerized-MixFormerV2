cmake_minimum_required(VERSION 3.10)

project(cpp_client)

set(CMAKE_CXX_STANDARD 14)

find_package(PythonInterp REQUIRED)
find_package(PkgConfig REQUIRED)
find_package(OpenCV REQUIRED)
pkg_check_modules(GLFW REQUIRED glfw3)

include_directories(${GLFW_INCLUDE_DIRS})
include_directories(imgui)

add_executable(${PROJECT_NAME}
        main.cpp)

target_link_libraries(${PROJECT_NAME} 
        PRIVATE 
        X11 Xrandr Xinerama Xi Xcursor GL pthread dl curl rt
        ${GLFW_LIBRARIES} 
        ${OpenCV_LIBS})
