cmake_minimum_required(VERSION 3.20)

project(IGESReferenceImplementation VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ── nlohmann/json (vendored single-header) ────────────────────
# Single-header snapshot lives in third_party/nlohmann/. The ref-impl
# ships with this vendored to keep builds hermetic (no network fetch).
add_library(nlohmann_json INTERFACE)
target_include_directories(nlohmann_json INTERFACE third_party)

# ── iges executable ───────────────────────────────────────────
file(GLOB IGES_ENTITY_SOURCES CONFIGURE_DEPENDS src/entities/*.cpp)
file(GLOB IGES_PARSER_SOURCES CONFIGURE_DEPENDS src/parser/*.cpp)
file(GLOB IGES_WRITER_SOURCES CONFIGURE_DEPENDS src/writer/*.cpp)
file(GLOB IGES_MODEL_SOURCES  CONFIGURE_DEPENDS src/model/*.cpp)
file(GLOB IGES_JSON_SOURCES   CONFIGURE_DEPENDS src/json/*.cpp)

add_executable(iges
    src/main.cpp
    src/types.cpp
    ${IGES_ENTITY_SOURCES}
    ${IGES_PARSER_SOURCES}
    ${IGES_WRITER_SOURCES}
    ${IGES_MODEL_SOURCES}
    ${IGES_JSON_SOURCES}
)

target_include_directories(iges PRIVATE src)
target_link_libraries(iges PRIVATE nlohmann_json)
