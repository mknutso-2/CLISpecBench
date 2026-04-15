// iges::entity_writer — Entity serializer implementations.

#include "entity_writer.hpp"
#include "param_writer.hpp"

namespace iges {

std::string write_line_entity(LineEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.start.x);
    pw.write_real(e.start.y);
    pw.write_real(e.start.z);
    pw.write_real(e.terminate.x);
    pw.write_real(e.terminate.y);
    pw.write_real(e.terminate.z);
    pw.end_record();
    return pw.str();
}

std::string write_circular_arc_entity(CircularArcEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.zt);
    pw.write_real(e.x1);
    pw.write_real(e.y1);
    pw.write_real(e.x2);
    pw.write_real(e.y2);
    pw.write_real(e.x3);
    pw.write_real(e.y3);
    pw.end_record();
    return pw.str();
}

std::string write_point_entity(PointEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.coords.x);
    pw.write_real(e.coords.y);
    pw.write_real(e.coords.z);
    pw.write_pointer(e.display_symbol);
    pw.end_record();
    return pw.str();
}

std::string write_composite_curve_entity(CompositeCurveEntity const& e) {
    ParamWriter pw;
    pw.write_integer(static_cast<int>(e.constituents.size()));
    for (auto const& de : e.constituents) {
        pw.write_pointer(de);
    }
    pw.end_record();
    return pw.str();
}

std::string write_null_entity(NullEntity const& /*e*/) {
    ParamWriter pw;
    pw.end_record();
    return pw.str();
}

std::string write_transformation_matrix_entity(TransformationMatrixEntity const& e) {
    ParamWriter pw;
    for (int row = 0; row < 3; ++row) {
        for (int col = 0; col < 3; ++col) {
            pw.write_real(e.rotation(row, col));
        }
        // Translation component after each row
        if (row == 0) pw.write_real(e.translation.x);
        else if (row == 1) pw.write_real(e.translation.y);
        else pw.write_real(e.translation.z);
    }
    pw.end_record();
    return pw.str();
}

std::string write_rational_bspline_curve_entity(RationalBSplineCurveEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.K);
    pw.write_integer(e.M);
    pw.write_integer(e.prop1);
    pw.write_integer(e.prop2);
    pw.write_integer(e.prop3);
    pw.write_integer(e.prop4);
    for (auto const& t : e.knots) pw.write_real(t);
    for (auto const& w : e.weights) pw.write_real(w);
    for (auto const& p : e.control_points) {
        pw.write_real(p.x);
        pw.write_real(p.y);
        pw.write_real(p.z);
    }
    pw.write_real(e.v0);
    pw.write_real(e.v1);
    pw.write_real(e.plane_normal.x);
    pw.write_real(e.plane_normal.y);
    pw.write_real(e.plane_normal.z);
    pw.end_record();
    return pw.str();
}

std::string write_rational_bspline_surface_entity(RationalBSplineSurfaceEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.K1);
    pw.write_integer(e.K2);
    pw.write_integer(e.M1);
    pw.write_integer(e.M2);
    pw.write_integer(e.prop1);
    pw.write_integer(e.prop2);
    pw.write_integer(e.prop3);
    pw.write_integer(e.prop4);
    pw.write_integer(e.prop5);
    for (auto const& t : e.knots_u) pw.write_real(t);
    for (auto const& t : e.knots_v) pw.write_real(t);
    for (auto const& w : e.weights) pw.write_real(w);
    for (auto const& p : e.control_points) {
        pw.write_real(p.x);
        pw.write_real(p.y);
        pw.write_real(p.z);
    }
    pw.write_real(e.u0);
    pw.write_real(e.u1);
    pw.write_real(e.v0);
    pw.write_real(e.v1);
    pw.end_record();
    return pw.str();
}

std::string write_trimmed_surface_entity(TrimmedSurfaceEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.pts);
    pw.write_integer(e.n1);
    pw.write_integer(e.n2);
    pw.write_pointer(e.pto);
    for (auto const& p : e.pti) pw.write_pointer(p);
    pw.end_record();
    return pw.str();
}

std::string write_curve_on_surface_entity(CurveOnParametricSurfaceEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.crtn);
    pw.write_pointer(e.sptr);
    pw.write_pointer(e.bptr);
    pw.write_pointer(e.cptr);
    pw.write_integer(e.pref);
    pw.end_record();
    return pw.str();
}

std::string write_ruled_surface_entity(RuledSurfaceEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.de1);
    pw.write_pointer(e.de2);
    pw.write_integer(e.dirflg);
    pw.write_integer(e.devflg);
    pw.end_record();
    return pw.str();
}

std::string write_surface_of_revolution_entity(SurfaceOfRevolutionEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.l);
    pw.write_pointer(e.c);
    pw.write_real(e.sa);
    pw.write_real(e.ta);
    pw.end_record();
    return pw.str();
}

std::string write_tabulated_cylinder_entity(TabulatedCylinderEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.de);
    pw.write_real(e.terminate_point.x);
    pw.write_real(e.terminate_point.y);
    pw.write_real(e.terminate_point.z);
    pw.end_record();
    return pw.str();
}

std::string write_offset_curve_entity(OffsetCurveEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.de1);
    pw.write_integer(e.flag);
    pw.write_pointer(e.de2);
    pw.write_integer(e.ndim);
    pw.write_integer(e.ptype);
    pw.write_real(e.d1);
    pw.write_real(e.td1);
    pw.write_real(e.d2);
    pw.write_real(e.td2);
    pw.write_real(e.vx);
    pw.write_real(e.vy);
    pw.write_real(e.vz);
    pw.write_real(e.tt1);
    pw.write_real(e.tt2);
    pw.end_record();
    return pw.str();
}

std::string write_offset_surface_entity(OffsetSurfaceEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.nx);
    pw.write_real(e.ny);
    pw.write_real(e.nz);
    pw.write_real(e.d);
    pw.write_pointer(e.de);
    pw.end_record();
    return pw.str();
}

std::string write_bounded_surface_entity(BoundedSurfaceEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.type);
    pw.write_pointer(e.sptr);
    pw.write_integer(e.n);
    for (auto const& p : e.bdpt) pw.write_pointer(p);
    pw.end_record();
    return pw.str();
}

// ── Boundary entity (Type 141) ──────────────────────────────────

std::string write_boundary_entity(BoundaryEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.type);
    pw.write_integer(e.pref);
    pw.write_pointer(e.sptr);
    pw.write_integer(e.n);
    for (auto const& c : e.curves) {
        pw.write_pointer(c.crvpt);
        pw.write_integer(c.sense);
        pw.write_integer(c.k);
        for (auto const& p : c.pscpt) pw.write_pointer(p);
    }
    pw.end_record();
    return pw.str();
}

// ── Copious data (Type 106) ─────────────────────────────────────

std::string write_copious_data_entity(CopiousDataEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.ip);
    pw.write_integer(e.n);
    if (e.ip == 1) pw.write_real(e.zt);
    for (auto const& v : e.data) pw.write_real(v);
    pw.end_record();
    return pw.str();
}

// ── CSG primitives ──────────────────────────────────────────────

std::string write_block_entity(BlockEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.lx); pw.write_real(e.ly); pw.write_real(e.lz);
    pw.write_real(e.corner.x); pw.write_real(e.corner.y); pw.write_real(e.corner.z);
    pw.write_real(e.x_axis.x); pw.write_real(e.x_axis.y); pw.write_real(e.x_axis.z);
    pw.write_real(e.z_axis.x); pw.write_real(e.z_axis.y); pw.write_real(e.z_axis.z);
    pw.end_record();
    return pw.str();
}

std::string write_wedge_entity(WedgeEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.lx); pw.write_real(e.ly); pw.write_real(e.lz);
    pw.write_real(e.ltx);
    pw.write_real(e.corner.x); pw.write_real(e.corner.y); pw.write_real(e.corner.z);
    pw.write_real(e.x_axis.x); pw.write_real(e.x_axis.y); pw.write_real(e.x_axis.z);
    pw.write_real(e.z_axis.x); pw.write_real(e.z_axis.y); pw.write_real(e.z_axis.z);
    pw.end_record();
    return pw.str();
}

std::string write_right_circular_cylinder_entity(RightCircularCylinderEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.h); pw.write_real(e.r);
    pw.write_real(e.face_center.x); pw.write_real(e.face_center.y); pw.write_real(e.face_center.z);
    pw.write_real(e.axis.x); pw.write_real(e.axis.y); pw.write_real(e.axis.z);
    pw.end_record();
    return pw.str();
}

std::string write_cone_frustum_entity(ConeFrustumEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.h); pw.write_real(e.r1); pw.write_real(e.r2);
    pw.write_real(e.face_center.x); pw.write_real(e.face_center.y); pw.write_real(e.face_center.z);
    pw.write_real(e.axis.x); pw.write_real(e.axis.y); pw.write_real(e.axis.z);
    pw.end_record();
    return pw.str();
}

std::string write_sphere_entity(SphereEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.radius);
    pw.write_real(e.center.x); pw.write_real(e.center.y); pw.write_real(e.center.z);
    pw.end_record();
    return pw.str();
}

std::string write_torus_entity(TorusEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.r1); pw.write_real(e.r2);
    pw.write_real(e.center.x); pw.write_real(e.center.y); pw.write_real(e.center.z);
    pw.write_real(e.axis.x); pw.write_real(e.axis.y); pw.write_real(e.axis.z);
    pw.end_record();
    return pw.str();
}

std::string write_solid_of_revolution_entity(SolidOfRevolutionEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.ptr);
    pw.write_real(e.f);
    pw.write_real(e.axis_point.x); pw.write_real(e.axis_point.y); pw.write_real(e.axis_point.z);
    pw.write_real(e.axis_dir.x); pw.write_real(e.axis_dir.y); pw.write_real(e.axis_dir.z);
    pw.end_record();
    return pw.str();
}

std::string write_solid_of_linear_extrusion_entity(SolidOfLinearExtrusionEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.ptr);
    pw.write_real(e.length);
    pw.write_real(e.direction.x); pw.write_real(e.direction.y); pw.write_real(e.direction.z);
    pw.end_record();
    return pw.str();
}

std::string write_ellipsoid_entity(EllipsoidEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.lx); pw.write_real(e.ly); pw.write_real(e.lz);
    pw.write_real(e.center.x); pw.write_real(e.center.y); pw.write_real(e.center.z);
    pw.write_real(e.x_axis.x); pw.write_real(e.x_axis.y); pw.write_real(e.x_axis.z);
    pw.write_real(e.z_axis.x); pw.write_real(e.z_axis.y); pw.write_real(e.z_axis.z);
    pw.end_record();
    return pw.str();
}

std::string write_boolean_tree_entity(BooleanTreeEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.n);
    for (auto v : e.entries) pw.write_integer(v);
    pw.end_record();
    return pw.str();
}

std::string write_selected_component_entity(SelectedComponentEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.btree);
    pw.write_real(e.sel_point.x); pw.write_real(e.sel_point.y); pw.write_real(e.sel_point.z);
    pw.end_record();
    return pw.str();
}

std::string write_solid_assembly_entity(SolidAssemblyEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.n);
    for (int i = 0; i < e.n; ++i)
        pw.write_pointer(e.items[i]);
    for (int i = 0; i < e.n; ++i)
        pw.write_pointer(e.transforms[i]);
    pw.end_record();
    return pw.str();
}

std::string write_solid_instance_entity(SolidInstanceEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.ptr);
    pw.end_record();
    return pw.str();
}

// ── B-Rep analytical surfaces ───────────────────────────────────

std::string write_plane_surface_entity(PlaneSurfaceEntity const& e, int form) {
    ParamWriter pw;
    pw.write_pointer(e.deloc);
    pw.write_pointer(e.denrml);
    if (form == 1) pw.write_pointer(e.derefd);
    pw.end_record();
    return pw.str();
}

std::string write_cylindrical_surface_entity(CylindricalSurfaceEntity const& e, int form) {
    ParamWriter pw;
    pw.write_pointer(e.deloc);
    pw.write_pointer(e.deaxis);
    pw.write_real(e.radius);
    if (form == 1) pw.write_pointer(e.derefd);
    pw.end_record();
    return pw.str();
}

std::string write_conical_surface_entity(ConicalSurfaceEntity const& e, int form) {
    ParamWriter pw;
    pw.write_pointer(e.deloc);
    pw.write_pointer(e.deaxis);
    pw.write_real(e.radius);
    pw.write_real(e.sangle);
    if (form == 1) pw.write_pointer(e.derefd);
    pw.end_record();
    return pw.str();
}

std::string write_spherical_surface_entity(SphericalSurfaceEntity const& e, int form) {
    ParamWriter pw;
    pw.write_pointer(e.deloc);
    pw.write_real(e.radius);
    if (form == 1) {
        pw.write_pointer(e.deaxis);
        pw.write_pointer(e.derefd);
    }
    pw.end_record();
    return pw.str();
}

std::string write_toroidal_surface_entity(ToroidalSurfaceEntity const& e, int form) {
    ParamWriter pw;
    pw.write_pointer(e.deloc);
    pw.write_pointer(e.deaxis);
    pw.write_real(e.majrad);
    pw.write_real(e.minrad);
    if (form == 1) pw.write_pointer(e.derefd);
    pw.end_record();
    return pw.str();
}

// ── B-Rep topology ──────────────────────────────────────────────

std::string write_vertex_list_entity(VertexListEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.n);
    for (auto const& v : e.vertices) {
        pw.write_real(v.x); pw.write_real(v.y); pw.write_real(v.z);
    }
    pw.end_record();
    return pw.str();
}

std::string write_edge_list_entity(EdgeListEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.n);
    for (auto const& edge : e.edges) {
        pw.write_pointer(edge.curve);
        pw.write_pointer(edge.svp);
        pw.write_integer(edge.sv);
        pw.write_pointer(edge.tvp);
        pw.write_integer(edge.tv);
    }
    pw.end_record();
    return pw.str();
}

std::string write_loop_entity(LoopEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.n);
    for (auto const& eu : e.edge_uses) {
        pw.write_integer(eu.type);
        pw.write_pointer(eu.edge);
        pw.write_integer(eu.ndx);
        pw.write_logical(eu.orientation);
        pw.write_integer(eu.k);
        for (auto const& pc : eu.param_curves) {
            pw.write_logical(pc.isoparametric);
            pw.write_pointer(pc.curve);
        }
    }
    pw.end_record();
    return pw.str();
}

std::string write_face_entity(FaceEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.surf);
    pw.write_integer(e.n);
    pw.write_logical(e.outer_loop_flag);
    for (auto const& l : e.loops) pw.write_pointer(l);
    pw.end_record();
    return pw.str();
}

std::string write_shell_entity(ShellEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.n);
    for (auto const& fu : e.faces) {
        pw.write_pointer(fu.face);
        pw.write_logical(fu.orientation);
    }
    pw.end_record();
    return pw.str();
}

std::string write_msbo_entity(MSBOEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.shell);
    pw.write_logical(e.sof);
    pw.write_integer(e.n);
    for (auto const& vs : e.voids) {
        pw.write_pointer(vs.shell);
        pw.write_logical(vs.orientation);
    }
    pw.end_record();
    return pw.str();
}

// ── Structure + annotation ──────────────────────────────────────

std::string write_subfigure_definition_entity(SubfigureDefinitionEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.depth);
    pw.write_string(e.name);
    pw.write_integer(e.n);
    for (auto const& de : e.entities) pw.write_pointer(de);
    pw.end_record();
    return pw.str();
}

std::string write_subfigure_instance_entity(SubfigureInstanceEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.de);
    pw.write_real(e.translation.x);
    pw.write_real(e.translation.y);
    pw.write_real(e.translation.z);
    pw.write_real(e.scale);
    pw.end_record();
    return pw.str();
}

std::string write_color_definition_entity(ColorDefinitionEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.red);
    pw.write_real(e.green);
    pw.write_real(e.blue);
    if (!e.name.empty()) pw.write_string(e.name);
    pw.end_record();
    return pw.str();
}

std::string write_external_reference_entity(ExternalReferenceEntity const& e, int form) {
    ParamWriter pw;
    if (form == 0 || form == 2 || form == 4) {
        pw.write_string(e.filename);
        pw.write_string(e.entity_name);
    } else if (form == 1) {
        pw.write_string(e.filename);
    } else if (form == 3) {
        pw.write_string(e.entity_name);
    }
    pw.end_record();
    return pw.str();
}

std::string write_connect_point_entity(ConnectPointEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.location.x);
    pw.write_real(e.location.y);
    pw.write_real(e.location.z);
    pw.write_pointer(e.display_symbol);
    pw.write_integer(e.tf);
    pw.write_integer(e.ff);
    pw.write_string(e.cid);
    pw.write_pointer(e.pttcid);
    pw.write_string(e.cfn);
    pw.write_pointer(e.pttcfn);
    pw.write_integer(e.cpid);
    pw.write_integer(e.fc);
    pw.write_integer(e.sf);
    pw.write_pointer(e.psfi);
    pw.end_record();
    return pw.str();
}

std::string write_property_entity(PropertyEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.np);
    for (auto const& val : e.values) {
        std::visit([&](auto const& v) {
            using T = std::decay_t<decltype(v)>;
            if constexpr (std::is_same_v<T, DefaultedField>) {
                // Write nothing for defaulted fields
            } else if constexpr (std::is_same_v<T, int>) {
                pw.write_integer(v);
            } else if constexpr (std::is_same_v<T, Real>) {
                pw.write_real(v);
            } else if constexpr (std::is_same_v<T, std::string>) {
                pw.write_string(v);
            } else if constexpr (std::is_same_v<T, bool>) {
                pw.write_logical(v);
            }
        }, val);
    }
    pw.end_record();
    return pw.str();
}

std::string write_view_entity(ViewEntity const& e, int form) {
    ParamWriter pw;
    pw.write_integer(e.view_number);
    pw.write_real(e.scale);
    if (form == 1) {
        pw.write_real(e.view_plane_normal.x);
        pw.write_real(e.view_plane_normal.y);
        pw.write_real(e.view_plane_normal.z);
        pw.write_real(e.view_reference_point.x);
        pw.write_real(e.view_reference_point.y);
        pw.write_real(e.view_reference_point.z);
        pw.write_real(e.center_of_projection.x);
        pw.write_real(e.center_of_projection.y);
        pw.write_real(e.center_of_projection.z);
        pw.write_real(e.view_up_vector.x);
        pw.write_real(e.view_up_vector.y);
        pw.write_real(e.view_up_vector.z);
        pw.write_real(e.view_plane_distance);
        pw.write_real(e.umin);
        pw.write_real(e.umax);
        pw.write_real(e.vmin);
        pw.write_real(e.vmax);
        pw.write_integer(e.depth_clipping);
        pw.write_real(e.wmin);
        pw.write_real(e.wmax);
    } else {
        for (auto const& cp : e.clip_planes) pw.write_pointer(cp);
    }
    pw.end_record();
    return pw.str();
}

std::string write_drawing_entity(DrawingEntity const& e, int form) {
    ParamWriter pw;
    pw.write_integer(e.n);
    for (auto const& v : e.views) {
        pw.write_pointer(v.view);
        pw.write_real(v.x_origin);
        pw.write_real(v.y_origin);
        if (form == 1) pw.write_real(v.angle);
    }
    pw.write_integer(e.m);
    for (auto const& a : e.annotations) pw.write_pointer(a);
    pw.end_record();
    return pw.str();
}

std::string write_line_font_definition_entity(LineFontDefinitionEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.m);
    if (e.form == 1) {
        pw.write_pointer(e.l1);
        pw.write_real(e.l2);
        pw.write_real(e.l3);
    } else {
        for (auto const& s : e.segments) pw.write_real(s);
        pw.write_string(e.bitmask);
    }
    pw.end_record();
    return pw.str();
}

std::string write_associativity_instance_entity(AssociativityInstanceEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.n);
    for (auto const& de : e.entries) pw.write_pointer(de);
    pw.end_record();
    return pw.str();
}

std::string write_general_note_entity(GeneralNoteEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.ns);
    for (auto const& s : e.strings) {
        pw.write_integer(s.nc);
        pw.write_real(s.wc);
        pw.write_real(s.hc);
        pw.write_integer(s.fc);
        pw.write_real(s.slant);
        pw.write_real(s.angle);
        pw.write_integer(s.mirror);
        pw.write_integer(s.vh);
        pw.write_real(s.start.x);
        pw.write_real(s.start.y);
        pw.write_real(s.start.z);
        pw.write_string(s.text);
    }
    pw.end_record();
    return pw.str();
}

std::string write_leader_arrow_entity(LeaderArrowEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.n);
    pw.write_real(e.ad1);
    pw.write_real(e.ad2);
    pw.write_real(e.zt);
    pw.write_real(e.xh);
    pw.write_real(e.yh);
    for (auto const& seg : e.segments) {
        pw.write_real(seg.x);
        pw.write_real(seg.y);
    }
    pw.end_record();
    return pw.str();
}

std::string write_rectangular_array_entity(RectangularArrayEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.de);
    pw.write_real(e.s);
    pw.write_real(e.position.x);
    pw.write_real(e.position.y);
    pw.write_real(e.position.z);
    pw.write_integer(e.nc);
    pw.write_integer(e.nr);
    pw.write_real(e.dx);
    pw.write_real(e.dy);
    pw.write_real(e.ax);
    pw.write_integer(e.lc);
    pw.write_integer(e.ddf);
    for (auto v : e.positions) pw.write_integer(v);
    pw.end_record();
    return pw.str();
}

std::string write_circular_array_entity(CircularArrayEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.de);
    pw.write_integer(e.ne);
    pw.write_real(e.center.x);
    pw.write_real(e.center.y);
    pw.write_real(e.center.z);
    pw.write_real(e.r);
    pw.write_real(e.as);
    pw.write_real(e.ad);
    pw.write_integer(e.lc);
    pw.write_integer(e.ddf);
    for (auto v : e.positions) pw.write_integer(v);
    pw.end_record();
    return pw.str();
}

std::string write_linear_dimension_entity(LinearDimensionEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.denote);
    pw.write_pointer(e.dearrw1);
    pw.write_pointer(e.dearrw2);
    pw.write_pointer(e.dewit1);
    pw.write_pointer(e.dewit2);
    pw.end_record();
    return pw.str();
}

std::string write_angular_dimension_entity(AngularDimensionEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.denote);
    pw.write_pointer(e.dewit1);
    pw.write_pointer(e.dewit2);
    pw.write_real(e.xt);
    pw.write_real(e.yt);
    pw.write_real(e.radius);
    pw.write_pointer(e.dearrw1);
    pw.write_pointer(e.dearrw2);
    pw.end_record();
    return pw.str();
}

std::string write_diameter_dimension_entity(DiameterDimensionEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.denote);
    pw.write_pointer(e.dearrw1);
    pw.write_pointer(e.dearrw2);
    pw.write_real(e.xt);
    pw.write_real(e.yt);
    pw.end_record();
    return pw.str();
}

std::string write_radius_dimension_entity(RadiusDimensionEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.denote);
    pw.write_pointer(e.dearrw);
    pw.write_real(e.xt);
    pw.write_real(e.yt);
    if (e.form == 1) {
        pw.write_pointer(e.dearrw2);
    }
    pw.end_record();
    return pw.str();
}

std::string write_ordinate_dimension_entity(OrdinateDimensionEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.denote);
    if (e.form == 1) {
        pw.write_pointer(e.deord);
        pw.write_pointer(e.desupp);
    } else {
        pw.write_pointer(e.dewit);
    }
    pw.end_record();
    return pw.str();
}

std::string write_general_label_entity(GeneralLabelEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.denote);
    pw.write_integer(e.n);
    for (auto const& l : e.leaders) pw.write_pointer(l);
    pw.end_record();
    return pw.str();
}

std::string write_conic_arc_entity(ConicArcEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.A);
    pw.write_real(e.B);
    pw.write_real(e.C);
    pw.write_real(e.D);
    pw.write_real(e.E);
    pw.write_real(e.F);
    pw.write_real(e.zt);
    pw.write_real(e.x1);
    pw.write_real(e.y1);
    pw.write_real(e.x2);
    pw.write_real(e.y2);
    pw.end_record();
    return pw.str();
}

std::string write_plane_entity(PlaneEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.A);
    pw.write_real(e.B);
    pw.write_real(e.C);
    pw.write_real(e.D);
    pw.write_pointer(e.ptr);
    pw.write_real(e.x);
    pw.write_real(e.y);
    pw.write_real(e.z);
    pw.write_real(e.size);
    pw.end_record();
    return pw.str();
}

std::string write_parametric_spline_curve_entity(ParametricSplineCurveEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.ctype);
    pw.write_integer(e.H);
    pw.write_integer(e.ndim);
    int N = static_cast<int>(e.segments.size());
    pw.write_integer(N);
    for (auto const& t : e.breakpoints) pw.write_real(t);
    for (auto const& seg : e.segments) {
        pw.write_real(seg.ax); pw.write_real(seg.bx);
        pw.write_real(seg.cx); pw.write_real(seg.dx);
        pw.write_real(seg.ay); pw.write_real(seg.by);
        pw.write_real(seg.cy); pw.write_real(seg.dy);
        pw.write_real(seg.az); pw.write_real(seg.bz);
        pw.write_real(seg.cz); pw.write_real(seg.dz);
    }
    pw.write_real(e.tpx0); pw.write_real(e.tpx1);
    pw.write_real(e.tpx2); pw.write_real(e.tpx3);
    pw.write_real(e.tpy0); pw.write_real(e.tpy1);
    pw.write_real(e.tpy2); pw.write_real(e.tpy3);
    pw.write_real(e.tpz0); pw.write_real(e.tpz1);
    pw.write_real(e.tpz2); pw.write_real(e.tpz3);
    pw.end_record();
    return pw.str();
}

std::string write_parametric_spline_surface_entity(ParametricSplineSurfaceEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.ctype);
    pw.write_integer(e.ptype);
    pw.write_integer(e.M);
    pw.write_integer(e.N);
    for (auto const& t : e.tu) pw.write_real(t);
    for (auto const& t : e.tv) pw.write_real(t);
    for (int i = 0; i < e.M; ++i) {
        for (int j = 0; j < e.N; ++j) {
            auto const& p = e.patches[i * e.N + j];
            for (int c = 0; c < 16; ++c) pw.write_real(p.coeff_x[c]);
            for (int c = 0; c < 16; ++c) pw.write_real(p.coeff_y[c]);
            for (int c = 0; c < 16; ++c) pw.write_real(p.coeff_z[c]);
        }
        // Write 48 zeros for boundary column
        for (int c = 0; c < 48; ++c) pw.write_real(0.0);
    }
    // Write boundary row: (N+1) groups of 48 zeros
    for (int j = 0; j <= e.N; ++j) {
        for (int c = 0; c < 48; ++c) pw.write_real(0.0);
    }
    pw.end_record();
    return pw.str();
}

std::string write_direction_entity(DirectionEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.x);
    pw.write_real(e.y);
    pw.write_real(e.z);
    pw.end_record();
    return pw.str();
}

std::string write_flash_entity(FlashEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.x);
    pw.write_real(e.y);
    pw.write_real(e.dim1);
    pw.write_real(e.dim2);
    pw.write_real(e.rot);
    pw.write_pointer(e.de);
    pw.end_record();
    return pw.str();
}

std::string write_curve_dimension_entity(CurveDimensionEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.denote);
    pw.write_pointer(e.decurv1);
    pw.write_pointer(e.decurv2);
    pw.write_pointer(e.dearr1);
    pw.write_pointer(e.dearr2);
    pw.write_pointer(e.dewit1);
    pw.write_pointer(e.dewit2);
    pw.end_record();
    return pw.str();
}

std::string write_flag_note_entity(FlagNoteEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.xt);
    pw.write_real(e.yt);
    pw.write_real(e.zt);
    pw.write_real(e.angle);
    pw.write_pointer(e.denote);
    pw.write_integer(e.n);
    for (auto const& l : e.leaders) pw.write_pointer(l);
    pw.end_record();
    return pw.str();
}

std::string write_point_dimension_entity(PointDimensionEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.denote);
    pw.write_pointer(e.dearrw);
    pw.write_pointer(e.degeom);
    pw.end_record();
    return pw.str();
}

std::string write_general_symbol_entity(GeneralSymbolEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.denote);
    pw.write_integer(e.n);
    for (auto const& g : e.geometries) pw.write_pointer(g);
    pw.write_integer(e.l);
    for (auto const& l : e.leaders) pw.write_pointer(l);
    pw.end_record();
    return pw.str();
}

std::string write_sectioned_area_entity(SectionedAreaEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.bndp);
    pw.write_integer(e.patrn);
    pw.write_real(e.xt);
    pw.write_real(e.yt);
    pw.write_real(e.zt);
    pw.write_real(e.dist);
    pw.write_real(e.angle);
    pw.write_integer(e.n);
    for (auto const& isl : e.islands) pw.write_pointer(isl);
    pw.end_record();
    return pw.str();
}

std::string write_text_display_template_entity(TextDisplayTemplateEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.cbw);
    pw.write_real(e.cbh);
    pw.write_integer(e.fc);
    pw.write_real(e.sl);
    pw.write_real(e.a);
    pw.write_integer(e.m);
    pw.write_integer(e.vh);
    pw.write_real(e.xs);
    pw.write_real(e.ys);
    pw.write_real(e.zs);
    pw.end_record();
    return pw.str();
}

std::string write_units_data_entity(UnitsDataEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.np);
    for (auto const& u : e.units) {
        pw.write_string(u.typ);
        pw.write_string(u.val);
        pw.write_real(u.sf);
    }
    pw.end_record();
    return pw.str();
}

std::string write_network_subfigure_definition_entity(NetworkSubfigureDefinitionEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.depth);
    pw.write_string(e.name);
    pw.write_integer(e.na);
    for (auto const& a : e.associated) pw.write_pointer(a);
    pw.write_integer(e.tf);
    pw.write_string(e.prd);
    pw.write_pointer(e.dptr);
    pw.write_integer(e.nc);
    for (auto const& c : e.connects) pw.write_pointer(c);
    pw.end_record();
    return pw.str();
}

std::string write_node_entity(NodeEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.x);
    pw.write_real(e.y);
    pw.write_real(e.z);
    pw.write_pointer(e.ndcsp);
    pw.end_record();
    return pw.str();
}

std::string write_finite_element_entity(FiniteElementEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.itop);
    pw.write_integer(e.n);
    for (auto const& de : e.nodes) pw.write_pointer(de);
    pw.write_string(e.etyp);
    pw.end_record();
    return pw.str();
}

std::string write_nodal_results_entity(NodalResultsEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.gnote);
    pw.write_integer(e.scn);
    pw.write_real(e.time);
    pw.write_integer(e.nv);
    pw.write_integer(e.nn);
    for (auto const& node : e.nodes) {
        pw.write_integer(node.node_id);
        pw.write_pointer(node.np);
        for (auto v : node.values) pw.write_real(v);
    }
    pw.end_record();
    return pw.str();
}

std::string write_nodal_displacement_entity(NodalDisplacementEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.nc);
    for (auto const& g : e.gp) pw.write_pointer(g);
    pw.write_integer(e.nn);
    for (auto const& node : e.nodes) {
        pw.write_integer(node.node_id);
        pw.write_pointer(node.np);
        for (auto const& c : node.cases) {
            pw.write_real(c.x);
            pw.write_real(c.y);
            pw.write_real(c.z);
            pw.write_real(c.rx);
            pw.write_real(c.ry);
            pw.write_real(c.rz);
        }
    }
    pw.end_record();
    return pw.str();
}

std::string write_nodal_load_constraint_entity(NodalLoadConstraintEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.nc);
    pw.write_integer(e.type);
    pw.write_pointer(e.de);
    for (auto const& p : e.ptrs) pw.write_pointer(p);
    pw.end_record();
    return pw.str();
}

std::string write_network_subfigure_instance_entity(NetworkSubfigureInstanceEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.de);
    pw.write_real(e.x);
    pw.write_real(e.y);
    pw.write_real(e.z);
    pw.write_real(e.xs);
    pw.write_real(e.ys);
    pw.write_real(e.zs);
    pw.write_integer(e.tf);
    pw.write_string(e.prd);
    pw.write_pointer(e.dptr);
    pw.write_integer(e.nc);
    for (auto const& c : e.cptrs) pw.write_pointer(c);
    pw.end_record();
    return pw.str();
}

std::string write_element_results_entity(ElementResultsEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.gnote);
    pw.write_integer(e.scn);
    pw.write_real(e.time);
    pw.write_integer(e.nv);
    pw.write_integer(e.rrf);
    pw.write_integer(e.ne);
    for (auto const& elem : e.elements) {
        pw.write_integer(elem.en);
        pw.write_pointer(elem.ep);
        pw.write_integer(elem.itop);
        pw.write_integer(elem.nl);
        pw.write_integer(elem.dlf);
        pw.write_integer(elem.nrl);
        for (auto r : elem.rdrl) pw.write_integer(r);
        pw.write_integer(elem.numv);
        for (auto v : elem.values) pw.write_real(v);
    }
    pw.end_record();
    return pw.str();
}

std::string write_text_font_definition_entity(TextFontDefinitionEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.fc);
    pw.write_string(e.fname);
    pw.write_integer(e.sf);
    pw.write_integer(e.scale);
    pw.write_integer(e.n);
    for (auto const& ch : e.characters) {
        pw.write_integer(ch.ac);
        pw.write_integer(ch.nx);
        pw.write_integer(ch.ny);
        pw.write_integer(ch.nm);
        for (auto const& pm : ch.motions) {
            pw.write_integer(pm.pf);
            pw.write_integer(pm.x);
            pw.write_integer(pm.y);
        }
    }
    pw.end_record();
    return pw.str();
}

std::string write_attribute_table_definition_entity(AttributeTableDefinitionEntity const& e, int form) {
    ParamWriter pw;
    pw.write_string(e.name);
    pw.write_integer(e.alt);
    pw.write_integer(e.na);
    for (auto const& attr : e.attributes) {
        pw.write_integer(attr.at);
        pw.write_integer(attr.avdt);
        pw.write_integer(attr.avc);
        if (form == 1 || form == 2) {
            for (int j = 0; j < attr.avc; ++j) {
                auto const& v = attr.values[static_cast<size_t>(j)];
                switch (attr.avdt) {
                    case 1: case 6: pw.write_integer(std::get<int>(v)); break;
                    case 2: pw.write_real(std::get<Real>(v)); break;
                    case 3: pw.write_string(std::get<std::string>(v)); break;
                    case 4: pw.write_pointer(std::get<DEIndex>(v)); break;
                    default: break;
                }
                if (form == 2) {
                    pw.write_pointer(attr.display_ptrs[static_cast<size_t>(j)]);
                }
            }
        }
    }
    pw.end_record();
    return pw.str();
}

std::string write_associativity_definition_entity(AssociativityDefinitionEntity const& e) {
    ParamWriter pw;
    pw.write_integer(e.k);
    for (auto const& cls : e.classes) {
        pw.write_integer(cls.bp);
        pw.write_integer(cls.order);
        pw.write_integer(cls.n);
        for (auto it : cls.item_types) pw.write_integer(it);
    }
    pw.end_record();
    return pw.str();
}

std::string write_new_general_note_entity(NewGeneralNoteEntity const& e) {
    ParamWriter pw;
    pw.write_real(e.txtcw);
    pw.write_real(e.txtch);
    pw.write_integer(e.justcd);
    pw.write_real(e.txtcx);
    pw.write_real(e.txtcy);
    pw.write_real(e.txtcz);
    pw.write_real(e.txtag);
    pw.write_real(e.baselx);
    pw.write_real(e.basely);
    pw.write_real(e.baselz);
    pw.write_real(e.nils);
    pw.write_integer(e.ns);
    for (auto const& s : e.strings) {
        pw.write_integer(s.fixvar);
        pw.write_real(s.chrwid);
        pw.write_real(s.chrhgt);
        pw.write_real(s.cspace);
        pw.write_real(s.lspace);
        pw.write_integer(s.font);
        pw.write_real(s.chrang);
        pw.write_string(s.cctext);
        pw.write_integer(s.nc);
        pw.write_real(s.wt);
        pw.write_real(s.ht);
        pw.write_integer(s.chrset);
        pw.write_real(s.sl);
        pw.write_real(s.a);
        pw.write_integer(s.m);
        pw.write_integer(s.vh);
        pw.write_real(s.xs);
        pw.write_real(s.ys);
        pw.write_real(s.zs);
        pw.write_string(s.text);
    }
    pw.end_record();
    return pw.str();
}

} // namespace iges
