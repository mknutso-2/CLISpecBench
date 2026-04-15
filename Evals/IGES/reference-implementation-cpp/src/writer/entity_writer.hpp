#pragma once
// iges::entity_writer — Serialize entity structs to PD parameter strings.
//
// Each write_*_entity() returns a free-format string (comma-separated,
// semicolon-terminated) that parse_*_entity() can consume.

#include "../entities/line_entity.hpp"
#include "../entities/circular_arc_entity.hpp"
#include "../entities/point_entity.hpp"
#include "../entities/composite_curve_entity.hpp"
#include "../entities/null_entity.hpp"
#include "../entities/transformation_matrix_entity.hpp"
#include "../entities/rational_bspline_curve_entity.hpp"
#include "../entities/rational_bspline_surface_entity.hpp"
#include "../entities/trimmed_surface_entity.hpp"
#include "../entities/curve_on_surface_entity.hpp"
#include "../entities/ruled_surface_entity.hpp"
#include "../entities/surface_of_revolution_entity.hpp"
#include "../entities/tabulated_cylinder_entity.hpp"
#include "../entities/offset_curve_entity.hpp"
#include "../entities/offset_surface_entity.hpp"
#include "../entities/bounded_surface_entity.hpp"
#include "../entities/boundary_entity.hpp"
#include "../entities/block_entity.hpp"
#include "../entities/wedge_entity.hpp"
#include "../entities/right_circular_cylinder_entity.hpp"
#include "../entities/cone_frustum_entity.hpp"
#include "../entities/sphere_entity.hpp"
#include "../entities/torus_entity.hpp"
#include "../entities/solid_of_revolution_entity.hpp"
#include "../entities/solid_of_linear_extrusion_entity.hpp"
#include "../entities/ellipsoid_entity.hpp"
#include "../entities/boolean_tree_entity.hpp"
#include "../entities/selected_component_entity.hpp"
#include "../entities/solid_assembly_entity.hpp"
#include "../entities/solid_instance_entity.hpp"
#include "../entities/plane_surface_entity.hpp"
#include "../entities/cylindrical_surface_entity.hpp"
#include "../entities/conical_surface_entity.hpp"
#include "../entities/spherical_surface_entity.hpp"
#include "../entities/toroidal_surface_entity.hpp"
#include "../entities/vertex_list_entity.hpp"
#include "../entities/edge_list_entity.hpp"
#include "../entities/loop_entity.hpp"
#include "../entities/face_entity.hpp"
#include "../entities/shell_entity.hpp"
#include "../entities/msbo_entity.hpp"
#include "../entities/subfigure_definition_entity.hpp"
#include "../entities/subfigure_instance_entity.hpp"
#include "../entities/color_definition_entity.hpp"
#include "../entities/external_reference_entity.hpp"
#include "../entities/connect_point_entity.hpp"
#include "../entities/property_entity.hpp"
#include "../entities/view_entity.hpp"
#include "../entities/drawing_entity.hpp"
#include "../entities/line_font_definition_entity.hpp"
#include "../entities/associativity_instance_entity.hpp"
#include "../entities/general_note_entity.hpp"
#include "../entities/leader_arrow_entity.hpp"
#include "../entities/rectangular_array_entity.hpp"
#include "../entities/circular_array_entity.hpp"
#include "../entities/linear_dimension_entity.hpp"
#include "../entities/angular_dimension_entity.hpp"
#include "../entities/diameter_dimension_entity.hpp"
#include "../entities/radius_dimension_entity.hpp"
#include "../entities/ordinate_dimension_entity.hpp"
#include "../entities/general_label_entity.hpp"
#include "../entities/copious_data_entity.hpp"
#include "../entities/conic_arc_entity.hpp"
#include "../entities/plane_entity.hpp"
#include "../entities/parametric_spline_curve_entity.hpp"
#include "../entities/parametric_spline_surface_entity.hpp"
#include "../entities/direction_entity.hpp"
#include "../entities/flash_entity.hpp"
#include "../entities/curve_dimension_entity.hpp"
#include "../entities/flag_note_entity.hpp"
#include "../entities/point_dimension_entity.hpp"
#include "../entities/general_symbol_entity.hpp"
#include "../entities/sectioned_area_entity.hpp"
#include "../entities/text_display_template_entity.hpp"
#include "../entities/units_data_entity.hpp"
#include "../entities/network_subfigure_definition_entity.hpp"
#include "../entities/node_entity.hpp"
#include "../entities/finite_element_entity.hpp"
#include "../entities/nodal_results_entity.hpp"
#include "../entities/nodal_displacement_entity.hpp"
#include "../entities/nodal_load_constraint_entity.hpp"
#include "../entities/network_subfigure_instance_entity.hpp"
#include "../entities/element_results_entity.hpp"
#include "../entities/associativity_definition_entity.hpp"
#include "../entities/text_font_definition_entity.hpp"
#include "../entities/attribute_table_definition_entity.hpp"
#include "../entities/new_general_note_entity.hpp"
#include <string>

namespace iges {

// Geometry
std::string write_line_entity(LineEntity const& e);
std::string write_circular_arc_entity(CircularArcEntity const& e);
std::string write_point_entity(PointEntity const& e);
std::string write_composite_curve_entity(CompositeCurveEntity const& e);
std::string write_null_entity(NullEntity const& e);
std::string write_transformation_matrix_entity(TransformationMatrixEntity const& e);
std::string write_rational_bspline_curve_entity(RationalBSplineCurveEntity const& e);
std::string write_rational_bspline_surface_entity(RationalBSplineSurfaceEntity const& e);
std::string write_trimmed_surface_entity(TrimmedSurfaceEntity const& e);
std::string write_curve_on_surface_entity(CurveOnParametricSurfaceEntity const& e);
std::string write_ruled_surface_entity(RuledSurfaceEntity const& e);
std::string write_surface_of_revolution_entity(SurfaceOfRevolutionEntity const& e);
std::string write_tabulated_cylinder_entity(TabulatedCylinderEntity const& e);
std::string write_offset_curve_entity(OffsetCurveEntity const& e);
std::string write_offset_surface_entity(OffsetSurfaceEntity const& e);
std::string write_bounded_surface_entity(BoundedSurfaceEntity const& e);
std::string write_boundary_entity(BoundaryEntity const& e);
std::string write_copious_data_entity(CopiousDataEntity const& e);
std::string write_conic_arc_entity(ConicArcEntity const& e);
std::string write_plane_entity(PlaneEntity const& e);
std::string write_parametric_spline_curve_entity(ParametricSplineCurveEntity const& e);
std::string write_parametric_spline_surface_entity(ParametricSplineSurfaceEntity const& e);
std::string write_direction_entity(DirectionEntity const& e);

// CSG primitives
std::string write_block_entity(BlockEntity const& e);
std::string write_wedge_entity(WedgeEntity const& e);
std::string write_right_circular_cylinder_entity(RightCircularCylinderEntity const& e);
std::string write_cone_frustum_entity(ConeFrustumEntity const& e);
std::string write_sphere_entity(SphereEntity const& e);
std::string write_torus_entity(TorusEntity const& e);
std::string write_solid_of_revolution_entity(SolidOfRevolutionEntity const& e);
std::string write_solid_of_linear_extrusion_entity(SolidOfLinearExtrusionEntity const& e);
std::string write_ellipsoid_entity(EllipsoidEntity const& e);
std::string write_boolean_tree_entity(BooleanTreeEntity const& e);
std::string write_selected_component_entity(SelectedComponentEntity const& e);
std::string write_solid_assembly_entity(SolidAssemblyEntity const& e);
std::string write_solid_instance_entity(SolidInstanceEntity const& e);

// B-Rep topology
std::string write_plane_surface_entity(PlaneSurfaceEntity const& e, int form);
std::string write_cylindrical_surface_entity(CylindricalSurfaceEntity const& e, int form);
std::string write_conical_surface_entity(ConicalSurfaceEntity const& e, int form);
std::string write_spherical_surface_entity(SphericalSurfaceEntity const& e, int form);
std::string write_toroidal_surface_entity(ToroidalSurfaceEntity const& e, int form);
std::string write_vertex_list_entity(VertexListEntity const& e);
std::string write_edge_list_entity(EdgeListEntity const& e);
std::string write_loop_entity(LoopEntity const& e);
std::string write_face_entity(FaceEntity const& e);
std::string write_shell_entity(ShellEntity const& e);
std::string write_msbo_entity(MSBOEntity const& e);

// Structure + annotation
std::string write_subfigure_definition_entity(SubfigureDefinitionEntity const& e);
std::string write_subfigure_instance_entity(SubfigureInstanceEntity const& e);
std::string write_color_definition_entity(ColorDefinitionEntity const& e);
std::string write_external_reference_entity(ExternalReferenceEntity const& e, int form);
std::string write_connect_point_entity(ConnectPointEntity const& e);
std::string write_property_entity(PropertyEntity const& e);
std::string write_view_entity(ViewEntity const& e, int form);
std::string write_drawing_entity(DrawingEntity const& e, int form = 0);
std::string write_line_font_definition_entity(LineFontDefinitionEntity const& e);
std::string write_associativity_instance_entity(AssociativityInstanceEntity const& e);
std::string write_general_note_entity(GeneralNoteEntity const& e);
std::string write_leader_arrow_entity(LeaderArrowEntity const& e);
std::string write_rectangular_array_entity(RectangularArrayEntity const& e);
std::string write_circular_array_entity(CircularArrayEntity const& e);
std::string write_linear_dimension_entity(LinearDimensionEntity const& e);
std::string write_angular_dimension_entity(AngularDimensionEntity const& e);
std::string write_diameter_dimension_entity(DiameterDimensionEntity const& e);
std::string write_radius_dimension_entity(RadiusDimensionEntity const& e);
std::string write_ordinate_dimension_entity(OrdinateDimensionEntity const& e);
std::string write_general_label_entity(GeneralLabelEntity const& e);
std::string write_flash_entity(FlashEntity const& e);
std::string write_curve_dimension_entity(CurveDimensionEntity const& e);
std::string write_flag_note_entity(FlagNoteEntity const& e);
std::string write_point_dimension_entity(PointDimensionEntity const& e);
std::string write_general_symbol_entity(GeneralSymbolEntity const& e);
std::string write_sectioned_area_entity(SectionedAreaEntity const& e);
std::string write_text_display_template_entity(TextDisplayTemplateEntity const& e);
std::string write_units_data_entity(UnitsDataEntity const& e);
std::string write_network_subfigure_definition_entity(NetworkSubfigureDefinitionEntity const& e);

// FEA
std::string write_node_entity(NodeEntity const& e);
std::string write_finite_element_entity(FiniteElementEntity const& e);
std::string write_nodal_results_entity(NodalResultsEntity const& e);
std::string write_nodal_displacement_entity(NodalDisplacementEntity const& e);
std::string write_nodal_load_constraint_entity(NodalLoadConstraintEntity const& e);
std::string write_network_subfigure_instance_entity(NetworkSubfigureInstanceEntity const& e);
std::string write_element_results_entity(ElementResultsEntity const& e);
std::string write_associativity_definition_entity(AssociativityDefinitionEntity const& e);
std::string write_text_font_definition_entity(TextFontDefinitionEntity const& e);
std::string write_attribute_table_definition_entity(AttributeTableDefinitionEntity const& e, int form);
std::string write_new_general_note_entity(NewGeneralNoteEntity const& e);

} // namespace iges
