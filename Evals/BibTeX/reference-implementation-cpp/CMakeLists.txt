cmake_minimum_required(VERSION 3.20)
project(bibtex LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(bibtex
  src/main.cpp
  src/lexer.cpp
  src/parser.cpp
  src/names.cpp
  src/bst_parser.cpp
  src/bst_interpreter.cpp
  src/json_writer.cpp
)
target_include_directories(bibtex PRIVATE src)
