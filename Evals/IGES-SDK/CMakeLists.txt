cmake_minimum_required(VERSION 3.28)
project(IGES-SDK LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ── Core library ──────────────────────────────────────────────
add_library(iges STATIC)
target_include_directories(iges PUBLIC src)
target_sources(iges PRIVATE
    src/types.cpp
    src/parser/param_tokenizer.cpp
    src/parser/lexer.cpp
    src/parser/file_reader.cpp
    src/model/global_section.cpp
    src/model/directory_entry.cpp
    src/model/validate.cpp
    src/entities/entity.cpp
    src/entities/line_entity.cpp
    src/entities/circular_arc_entity.cpp
    src/entities/transformation_matrix_entity.cpp
    src/entities/point_entity.cpp
    src/entities/composite_curve_entity.cpp
    src/entities/rational_bspline_curve_entity.cpp
    src/entities/rational_bspline_surface_entity.cpp
    src/entities/curve_on_surface_entity.cpp
    src/entities/trimmed_surface_entity.cpp
    src/entities/bounded_surface_entity.cpp
    src/entities/ruled_surface_entity.cpp
    src/entities/surface_of_revolution_entity.cpp
    src/entities/tabulated_cylinder_entity.cpp
    src/entities/offset_curve_entity.cpp
    src/entities/offset_surface_entity.cpp
    src/entities/boundary_entity.cpp
    src/entities/block_entity.cpp
    src/entities/wedge_entity.cpp
    src/entities/right_circular_cylinder_entity.cpp
    src/entities/cone_frustum_entity.cpp
    src/entities/sphere_entity.cpp
    src/entities/torus_entity.cpp
    src/entities/solid_of_revolution_entity.cpp
    src/entities/solid_of_linear_extrusion_entity.cpp
    src/entities/ellipsoid_entity.cpp
    src/entities/boolean_tree_entity.cpp
    src/entities/selected_component_entity.cpp
    src/entities/solid_assembly_entity.cpp
    src/entities/solid_instance_entity.cpp
    src/entities/plane_surface_entity.cpp
    src/entities/cylindrical_surface_entity.cpp
    src/entities/conical_surface_entity.cpp
    src/entities/spherical_surface_entity.cpp
    src/entities/toroidal_surface_entity.cpp
    src/entities/vertex_list_entity.cpp
    src/entities/edge_list_entity.cpp
    src/entities/loop_entity.cpp
    src/entities/face_entity.cpp
    src/entities/shell_entity.cpp
    src/entities/msbo_entity.cpp
    src/entities/null_entity.cpp
    src/entities/subfigure_definition_entity.cpp
    src/entities/subfigure_instance_entity.cpp
    src/entities/color_definition_entity.cpp
    src/entities/external_reference_entity.cpp
    src/entities/connect_point_entity.cpp
    src/entities/property_entity.cpp
    src/entities/view_entity.cpp
    src/entities/drawing_entity.cpp
    src/entities/line_font_definition_entity.cpp
    src/entities/associativity_instance_entity.cpp
    src/entities/general_note_entity.cpp
    src/entities/leader_arrow_entity.cpp
    src/entities/rectangular_array_entity.cpp
    src/entities/circular_array_entity.cpp
    src/entities/linear_dimension_entity.cpp
    src/entities/angular_dimension_entity.cpp
    src/entities/diameter_dimension_entity.cpp
    src/entities/radius_dimension_entity.cpp
    src/entities/ordinate_dimension_entity.cpp
    src/entities/general_label_entity.cpp
    src/entities/copious_data_entity.cpp
    src/entities/conic_arc_entity.cpp
    src/entities/plane_entity.cpp
    src/entities/parametric_spline_curve_entity.cpp
    src/entities/parametric_spline_surface_entity.cpp
    src/entities/direction_entity.cpp
    src/entities/flash_entity.cpp
    src/entities/curve_dimension_entity.cpp
    src/entities/flag_note_entity.cpp
    src/entities/point_dimension_entity.cpp
    src/entities/general_symbol_entity.cpp
    src/entities/sectioned_area_entity.cpp
    src/entities/text_display_template_entity.cpp
    src/entities/units_data_entity.cpp
    src/entities/network_subfigure_definition_entity.cpp
    src/entities/node_entity.cpp
    src/entities/finite_element_entity.cpp
    src/entities/nodal_results_entity.cpp
    src/entities/nodal_displacement_entity.cpp
    src/entities/nodal_load_constraint_entity.cpp
    src/entities/network_subfigure_instance_entity.cpp
    src/entities/element_results_entity.cpp
    src/entities/associativity_definition_entity.cpp
    src/entities/text_font_definition_entity.cpp
    src/entities/attribute_table_definition_entity.cpp
    src/entities/new_general_note_entity.cpp
    src/writer/format.cpp
    src/writer/param_writer.cpp
    src/writer/global_writer.cpp
    src/writer/entity_writer.cpp
    src/writer/file_writer.cpp
)

# ── Catch2 via FetchContent ───────────────────────────────────
include(FetchContent)
FetchContent_Declare(
    Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG        v3.7.1
)
FetchContent_MakeAvailable(Catch2)
list(APPEND CMAKE_MODULE_PATH ${catch2_SOURCE_DIR}/extras)
include(CTest)
include(Catch)

# ── Test executable ───────────────────────────────────────────
file(GLOB_RECURSE TEST_SOURCES tests/*.cpp)
add_executable(iges_tests ${TEST_SOURCES})
target_link_libraries(iges_tests PRIVATE iges Catch2::Catch2WithMain)
target_include_directories(iges_tests PRIVATE src tests)
catch_discover_tests(iges_tests)
