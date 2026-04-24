cmake_minimum_required(VERSION 3.20)
project(ical LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(ical
  src/main.cpp
  src/parser.cpp
  src/rrule.cpp
  src/json_writer.cpp
  src/datetime.cpp
)
target_include_directories(ical PRIVATE src)
