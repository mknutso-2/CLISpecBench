// iges::eval_helpers — resolver-using evaluators.

#include "eval_helpers.hpp"

#include "../entities/conic_arc_entity.hpp"

#include <cmath>

namespace iges {

namespace {

// Convert a 1-based odd DE index to a 0-based pair index.
// §2.2.4.4: DE pointers are 1, 3, 5, …; (de−1)/2 is the entity's index
// in the Directory Entry section.
bool is_valid_de(int de) {
    return de >= 1 && (de % 2) == 1;
}

struct SurfaceParams {
    Real u;
    Real v;
};

struct TransformData {
    Matrix3x3 rotation;
    Vec3 translation;
};

std::expected<TransformData, Diagnostic>
resolve_transform_entity(int xform_de, EntityResolver const& resolver) {
    if (!is_valid_de(xform_de)) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{"Transformation Matrix DE pointer is invalid: "}
                + std::to_string(xform_de),
            "§3.2"});
    }
    auto resolved = resolver(xform_de);
    if (!resolved) return std::unexpected(resolved.error());
    if (resolved->type != 124) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{"Transformation Matrix pointer must reference Type 124; got type "}
                + std::to_string(resolved->type),
            "§3.2"});
    }

    TransformData tx;
    auto const& rotation = resolved->data.at("rotation");
    for (int r = 0; r < 3; ++r) {
        for (int c = 0; c < 3; ++c) {
            tx.rotation(r, c) = rotation.at(r).at(c).get<Real>();
        }
    }
    auto const& translation = resolved->data.at("translation");
    tx.translation = Vec3{
        translation.at(0).get<Real>(),
        translation.at(1).get<Real>(),
        translation.at(2).get<Real>(),
    };
    return tx;
}

std::expected<Vec3, Diagnostic>
apply_point_transform(Vec3 point,
                      int xform_de,
                      EntityResolver const& resolver) {
    if (xform_de == 0) return point;
    auto tx = resolve_transform_entity(xform_de, resolver);
    if (!tx) return std::unexpected(tx.error());
    return tx->rotation * point + tx->translation;
}

std::expected<Vec3, Diagnostic>
apply_vector_transform(Vec3 vector,
                       int xform_de,
                       EntityResolver const& resolver) {
    if (xform_de == 0) return vector;
    auto tx = resolve_transform_entity(xform_de, resolver);
    if (!tx) return std::unexpected(tx.error());
    return tx->rotation * vector;
}

std::expected<Vec3, Diagnostic>
normalize_or_error(Vec3 v, char const* what, char const* spec_ref) {
    Real len = v.length();
    if (len < 1e-15) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            what, spec_ref});
    }
    return Vec3{v.x / len, v.y / len, v.z / len};
}

std::expected<Vec3, Diagnostic>
resolve_point_entity(int de,
                     char const* what,
                     char const* spec_ref,
                     EntityResolver const& resolver) {
    if (!is_valid_de(de)) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{what} + " has invalid DE pointer " + std::to_string(de),
            spec_ref});
    }
    auto resolved = resolver(de);
    if (!resolved) return std::unexpected(resolved.error());
    if (resolved->type != 116) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{what} + " must be Type 116 Point; got type "
                + std::to_string(resolved->type),
            spec_ref});
    }
    auto const& coords = resolved->data.at("coords");
    auto point = Vec3{
        coords.at(0).get<Real>(),
        coords.at(1).get<Real>(),
        coords.at(2).get<Real>(),
    };
    return apply_point_transform(point, resolved->xform_de, resolver);
}

std::expected<Vec3, Diagnostic>
resolve_direction_entity(int de,
                         char const* what,
                         char const* spec_ref,
                         EntityResolver const& resolver) {
    if (!is_valid_de(de)) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{what} + " has invalid DE pointer " + std::to_string(de),
            spec_ref});
    }
    auto resolved = resolver(de);
    if (!resolved) return std::unexpected(resolved.error());
    if (resolved->type != 123) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{what} + " must be Type 123 Direction; got type "
                + std::to_string(resolved->type),
            spec_ref});
    }
    auto direction = Vec3{
        resolved->data.at("x").get<Real>(),
        resolved->data.at("y").get<Real>(),
        resolved->data.at("z").get<Real>(),
    };
    return apply_vector_transform(direction, resolved->xform_de, resolver);
}

std::expected<Vec3, Diagnostic>
resolve_surface_reference_direction(int de,
                                    char const* what,
                                    char const* spec_ref,
                                    EntityResolver const& resolver) {
    auto raw = resolve_direction_entity(de, what, spec_ref, resolver);
    if (!raw) return std::unexpected(raw.error());
    return normalize_or_error(*raw, what, spec_ref);
}

std::expected<Vec3, Diagnostic>
build_surface_x_axis(Vec3 const& ref_dir,
                     Vec3 const& z_axis,
                     char const* what,
                     char const* spec_ref) {
    Vec3 projected = ref_dir - dot(ref_dir, z_axis) * z_axis;
    return normalize_or_error(projected, what, spec_ref);
}

std::expected<Vec3, Diagnostic>
evaluate_plane_surface_form1(nlohmann::json const& data,
                             Real u,
                             Real v,
                             EntityResolver const& resolver) {
    int deloc = data.at("deloc").get<int>();
    int denrml = data.at("denrml").get<int>();
    int derefd = data.at("derefd").get<int>();
    auto center = resolve_point_entity(
        deloc, "Plane Surface location", "§4.50", resolver);
    if (!center) return std::unexpected(center.error());
    auto normal_raw = resolve_direction_entity(
        denrml, "Plane Surface normal", "§4.50", resolver);
    if (!normal_raw) return std::unexpected(normal_raw.error());
    auto z_axis = normalize_or_error(
        *normal_raw, "Plane Surface normal must be non-zero", "§4.50");
    if (!z_axis) return std::unexpected(z_axis.error());
    auto ref_dir = resolve_surface_reference_direction(
        derefd, "Plane Surface reference direction", "§4.50", resolver);
    if (!ref_dir) return std::unexpected(ref_dir.error());
    auto x_axis = build_surface_x_axis(
        *ref_dir, *z_axis,
        "Plane Surface reference direction must not be parallel to the normal",
        "§4.50");
    if (!x_axis) return std::unexpected(x_axis.error());
    Vec3 y_axis = cross(*z_axis, *x_axis);
    return *center + u * *x_axis + v * y_axis;
}

std::expected<Vec3, Diagnostic>
plane_surface_normal_form1(nlohmann::json const& data,
                           EntityResolver const& resolver) {
    auto normal_raw = resolve_direction_entity(
        data.at("denrml").get<int>(),
        "Plane Surface normal",
        "§4.50",
        resolver);
    if (!normal_raw) return std::unexpected(normal_raw.error());
    return normalize_or_error(
        *normal_raw, "Plane Surface normal must be non-zero", "§4.50");
}

std::expected<Vec3, Diagnostic>
evaluate_cylindrical_surface_form1(nlohmann::json const& data,
                                   Real u_degrees,
                                   Real v,
                                   EntityResolver const& resolver) {
    int deloc = data.at("deloc").get<int>();
    int deaxis = data.at("deaxis").get<int>();
    int derefd = data.at("derefd").get<int>();
    Real radius = data.at("radius").get<Real>();

    auto center = resolve_point_entity(
        deloc, "Cylindrical Surface location", "§4.51", resolver);
    if (!center) return std::unexpected(center.error());
    auto axis_raw = resolve_direction_entity(
        deaxis, "Cylindrical Surface axis", "§4.51", resolver);
    if (!axis_raw) return std::unexpected(axis_raw.error());
    auto z_axis = normalize_or_error(
        *axis_raw, "Cylindrical Surface axis must be non-zero", "§4.51");
    if (!z_axis) return std::unexpected(z_axis.error());
    auto ref_dir = resolve_surface_reference_direction(
        derefd, "Cylindrical Surface reference direction", "§4.51", resolver);
    if (!ref_dir) return std::unexpected(ref_dir.error());
    auto x_axis = build_surface_x_axis(
        *ref_dir, *z_axis,
        "Cylindrical Surface reference direction must not be parallel to the axis",
        "§4.51");
    if (!x_axis) return std::unexpected(x_axis.error());
    Vec3 y_axis = cross(*z_axis, *x_axis);
    Real u = u_degrees * 3.14159265358979323846 / 180.0;
    return *center + radius * (std::cos(u) * *x_axis + std::sin(u) * y_axis) + v * *z_axis;
}

std::expected<Vec3, Diagnostic>
cylindrical_surface_normal_form1(nlohmann::json const& data,
                                 Real u_degrees,
                                 EntityResolver const& resolver) {
    int deaxis = data.at("deaxis").get<int>();
    int derefd = data.at("derefd").get<int>();
    auto axis_raw = resolve_direction_entity(
        deaxis, "Cylindrical Surface axis", "§4.51", resolver);
    if (!axis_raw) return std::unexpected(axis_raw.error());
    auto z_axis = normalize_or_error(
        *axis_raw, "Cylindrical Surface axis must be non-zero", "§4.51");
    if (!z_axis) return std::unexpected(z_axis.error());
    auto ref_dir = resolve_surface_reference_direction(
        derefd, "Cylindrical Surface reference direction", "§4.51", resolver);
    if (!ref_dir) return std::unexpected(ref_dir.error());
    auto x_axis = build_surface_x_axis(
        *ref_dir, *z_axis,
        "Cylindrical Surface reference direction must not be parallel to the axis",
        "§4.51");
    if (!x_axis) return std::unexpected(x_axis.error());
    Vec3 y_axis = cross(*z_axis, *x_axis);
    Real u = u_degrees * 3.14159265358979323846 / 180.0;
    return std::cos(u) * *x_axis + std::sin(u) * y_axis;
}

std::expected<Vec3, Diagnostic>
sample_surface_point(int type,
                     int form,
                     int xform_de,
                     nlohmann::json const& data,
                     Real u,
                     Real v,
                     EntityResolver const& resolver);

std::expected<Vec3, Diagnostic>
sample_surface_normal(int type,
                      int form,
                      int xform_de,
                      nlohmann::json const& data,
                      Real u,
                      Real v,
                      EntityResolver const& resolver);

std::expected<SurfaceParams, Diagnostic>
surface_reference_parameters(int type,
                             int form,
                             nlohmann::json const& data,
                             EntityResolver const& resolver) {
    switch (type) {
    case 114: {
        auto const& tu = data.at("tu");
        auto const& tv = data.at("tv");
        return SurfaceParams{
            0.5 * (tu.at(0).get<Real>() + tu.at(tu.size() - 1).get<Real>()),
            0.5 * (tv.at(0).get<Real>() + tv.at(tv.size() - 1).get<Real>()),
        };
    }
    case 118:
        if (form == 0) return SurfaceParams{0.5, 0.5};
        if (form == 1) {
            int de1 = data.at("de1").get<int>();
            if (!is_valid_de(de1)) {
                return std::unexpected(Diagnostic{
                    Diagnostic::Severity::Error, 0, SectionKind::Parameter,
                    "Ruled Surface de1 has invalid DE pointer", "§4.17"});
            }
            auto curve = resolver(de1);
            if (!curve) return std::unexpected(curve.error());
            auto span = curve_native_span(curve->type, curve->form, curve->data);
            if (!span) return std::unexpected(span.error());
            return SurfaceParams{0.5 * (span->first + span->second), 0.5};
        }
        break;
    case 120: {
        int curve_de = data.at("c").get<int>();
        if (!is_valid_de(curve_de)) {
            return std::unexpected(Diagnostic{
                Diagnostic::Severity::Error, 0, SectionKind::Parameter,
                "Surface of Revolution generatrix has invalid DE pointer",
                "§4.18"});
        }
        auto curve = resolver(curve_de);
        if (!curve) return std::unexpected(curve.error());
        auto span = curve_native_span(curve->type, curve->form, curve->data);
        if (!span) return std::unexpected(span.error());
        return SurfaceParams{
            0.5 * (span->first + span->second),
            0.5 * (data.at("sa").get<Real>() + data.at("ta").get<Real>()),
        };
    }
    case 122: {
        int directrix_de = data.at("de").get<int>();
        if (!is_valid_de(directrix_de)) {
            return std::unexpected(Diagnostic{
                Diagnostic::Severity::Error, 0, SectionKind::Parameter,
                "Tabulated Cylinder directrix has invalid DE pointer",
                "§4.19"});
        }
        auto directrix = resolver(directrix_de);
        if (!directrix) return std::unexpected(directrix.error());
        auto span = curve_native_span(
            directrix->type, directrix->form, directrix->data);
        if (!span) return std::unexpected(span.error());
        return SurfaceParams{0.5 * (span->first + span->second), 0.5};
    }
    case 128:
        return SurfaceParams{
            0.5 * (data.at("u0").get<Real>() + data.at("u1").get<Real>()),
            0.5 * (data.at("v0").get<Real>() + data.at("v1").get<Real>()),
        };
    case 140: {
        int de = data.at("de").get<int>();
        if (!is_valid_de(de)) {
            return std::unexpected(Diagnostic{
                Diagnostic::Severity::Error, 0, SectionKind::Parameter,
                "Offset Surface base-surface DE pointer is invalid",
                "§4.30"});
        }
        auto base = resolver(de);
        if (!base) return std::unexpected(base.error());
        return surface_reference_parameters(
            base->type, base->form, base->data, resolver);
    }
    case 190:
    case 192:
    case 194:
    case 196:
    case 198:
        return SurfaceParams{0.0, 0.0};
    default:
        break;
    }
    return std::unexpected(Diagnostic{
        Diagnostic::Severity::Error, 0, SectionKind::Parameter,
        std::string{"Offset Surface does not know reference parameters for base surface type "}
            + std::to_string(type),
        "§4.30"});
}

std::expected<Vec3, Diagnostic>
sample_surface_point(int type,
                     int form,
                     int xform_de,
                     nlohmann::json const& data,
                     Real u,
                     Real v,
                     EntityResolver const& resolver) {
    if (type == 190) {
        if (form != 1) {
            return std::unexpected(Diagnostic{
                Diagnostic::Severity::Error, 0, SectionKind::Parameter,
                "Plane Surface requires form 1 for parametric evaluation",
                "§4.50"});
        }
        auto point = evaluate_plane_surface_form1(data, u, v, resolver);
        if (!point) return std::unexpected(point.error());
        return apply_point_transform(*point, xform_de, resolver);
    }
    if (type == 192) {
        if (form != 1) {
            return std::unexpected(Diagnostic{
                Diagnostic::Severity::Error, 0, SectionKind::Parameter,
                "Cylindrical Surface requires form 1 for parametric evaluation",
                "§4.51"});
        }
        auto point = evaluate_cylindrical_surface_form1(data, u, v, resolver);
        if (!point) return std::unexpected(point.error());
        return apply_point_transform(*point, xform_de, resolver);
    }
    auto sample = evaluate_entity_dispatch(
        type, form, xform_de, data, u, v, resolver);
    if (!sample) return std::unexpected(sample.error());
    return sample->point;
}

std::expected<Vec3, Diagnostic>
sample_surface_normal(int type,
                      int form,
                      int xform_de,
                      nlohmann::json const& data,
                      Real u,
                      Real v,
                      EntityResolver const& resolver) {
    if (type == 190) {
        if (form != 1) {
            return std::unexpected(Diagnostic{
                Diagnostic::Severity::Error, 0, SectionKind::Parameter,
                "Plane Surface requires form 1 for parametric evaluation",
                "§4.50"});
        }
        auto normal = plane_surface_normal_form1(data, resolver);
        if (!normal) return std::unexpected(normal.error());
        auto transformed = apply_vector_transform(*normal, xform_de, resolver);
        if (!transformed) return std::unexpected(transformed.error());
        return normalize_or_error(
            *transformed,
            "Plane Surface transformed normal must be non-zero",
            "§4.50");
    }
    if (type == 192) {
        if (form != 1) {
            return std::unexpected(Diagnostic{
                Diagnostic::Severity::Error, 0, SectionKind::Parameter,
                "Cylindrical Surface requires form 1 for parametric evaluation",
                "§4.51"});
        }
        auto normal = cylindrical_surface_normal_form1(data, u, resolver);
        if (!normal) return std::unexpected(normal.error());
        auto transformed = apply_vector_transform(*normal, xform_de, resolver);
        if (!transformed) return std::unexpected(transformed.error());
        return normalize_or_error(
            *transformed,
            "Cylindrical Surface transformed normal must be non-zero",
            "§4.51");
    }

    Real du = 1e-6 * std::max<Real>(1.0, std::abs(u));
    Real dv = 1e-6 * std::max<Real>(1.0, std::abs(v));
    auto pu_minus = sample_surface_point(
        type, form, xform_de, data, u - du, v, resolver);
    if (!pu_minus) return std::unexpected(pu_minus.error());
    auto pu_plus = sample_surface_point(
        type, form, xform_de, data, u + du, v, resolver);
    if (!pu_plus) return std::unexpected(pu_plus.error());
    auto pv_minus = sample_surface_point(
        type, form, xform_de, data, u, v - dv, resolver);
    if (!pv_minus) return std::unexpected(pv_minus.error());
    auto pv_plus = sample_surface_point(
        type, form, xform_de, data, u, v + dv, resolver);
    if (!pv_plus) return std::unexpected(pv_plus.error());

    Vec3 du_vec = *pu_plus - *pu_minus;
    Vec3 dv_vec = *pv_plus - *pv_minus;
    return normalize_or_error(
        cross(du_vec, dv_vec),
        "Offset Surface base normal is degenerate at the sampled parameters",
        "§4.30");
}

} // namespace


std::expected<std::pair<Real, Real>, Diagnostic>
curve_native_span(int type, int form, nlohmann::json const& data) {
    switch (type) {
    case 100: {
        // Circular Arc (§4.3): [start_angle, terminate_angle]. Atan2
        // handles the wrap into [−π, π]; composite accumulation needs a
        // non-negative span, so if the terminate angle is ≤ start angle
        // we add 2π (full-turn wrap per spec's CCW convention).
        auto x1 = data.at("x1").get<Real>();
        auto y1 = data.at("y1").get<Real>();
        auto x2 = data.at("x2").get<Real>();
        auto y2 = data.at("y2").get<Real>();
        auto x3 = data.at("x3").get<Real>();
        auto y3 = data.at("y3").get<Real>();
        Real start = std::atan2(y2 - y1, x2 - x1);
        Real end = std::atan2(y3 - y1, x3 - x1);
        if (end <= start) end += 2.0 * 3.14159265358979323846;
        (void)form;
        return std::pair<Real, Real>{start, end};
    }
    case 104: {
        // Conic Arc (§4.5): form-specific default parameterization from
        // the standard-position conic coefficients and the declared
        // start/terminate points.
        ConicArcEntity ent;
        ent.A = data.at("A").get<Real>();
        ent.B = data.at("B").get<Real>();
        ent.C = data.at("C").get<Real>();
        ent.D = data.at("D").get<Real>();
        ent.E = data.at("E").get<Real>();
        ent.F = data.at("F").get<Real>();
        ent.zt = data.at("zt").get<Real>();
        ent.x1 = data.at("x1").get<Real>();
        ent.y1 = data.at("y1").get<Real>();
        ent.x2 = data.at("x2").get<Real>();
        ent.y2 = data.at("y2").get<Real>();
        (void)form;
        return ent.parameter_span();
    }
    case 106: {
        // Copious Data (§4.6 forms 11/12/63): [0, N−1].
        auto n = data.at("n").get<int>();
        if (n < 2) {
            return std::unexpected(Diagnostic{
                Diagnostic::Severity::Error, 0, SectionKind::Parameter,
                "Copious Data needs at least 2 points to parameterize", "§4.6"});
        }
        (void)form;
        return std::pair<Real, Real>{0.0, static_cast<Real>(n - 1)};
    }
    case 110: {
        // Line (§4.13): Form 0 is [0, 1]. Forms 1/2 have infinite
        // domains that are not composable; reject them here.
        if (form != 0) {
            return std::unexpected(Diagnostic{
                Diagnostic::Severity::Error, 0, SectionKind::Parameter,
                "Line forms 1/2 have unbounded parameter domain — "
                "not usable as composite curve constituents", "§4.13"});
        }
        return std::pair<Real, Real>{0.0, 1.0};
    }
    case 126: {
        // Rational B-Spline Curve (§4.23): [v0, v1].
        auto v0 = data.at("v0").get<Real>();
        auto v1 = data.at("v1").get<Real>();
        (void)form;
        return std::pair<Real, Real>{v0, v1};
    }
    default:
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{"Composite Curve constituent type "}
                + std::to_string(type)
                + " does not have a resolver-independent native span",
            "§4.4"});
    }
}


std::expected<EvalResult, Diagnostic>
evaluate_composite_curve(CompositeCurveEntity const& ent,
                         Real t,
                         EntityResolver const& resolver) {
    if (ent.constituents.empty()) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            "Composite Curve has no constituents", "§4.4"});
    }

    // Resolve each constituent and cache (resolved entity, native span).
    struct Leg {
        ResolvedEntity resolved;
        Real v0;
        Real v1;
        Real t_start;  // cumulative composite parameter at the start
    };
    std::vector<Leg> legs;
    legs.reserve(ent.constituents.size());

    Real cumulative = 0.0;
    for (auto const& de : ent.constituents) {
        if (!is_valid_de(de.value)) {
            return std::unexpected(Diagnostic{
                Diagnostic::Severity::Error, 0, SectionKind::Parameter,
                std::string{"Composite Curve has invalid constituent DE pointer "}
                    + std::to_string(de.value),
                "§4.4"});
        }
        auto resolved = resolver(de.value);
        if (!resolved) return std::unexpected(resolved.error());
        auto span = curve_native_span(resolved->type, resolved->form, resolved->data);
        if (!span) return std::unexpected(span.error());
        Leg leg{*resolved, span->first, span->second, cumulative};
        cumulative += (span->second - span->first);
        legs.push_back(std::move(leg));
    }

    // Domain for the composite parameter is [0, cumulative].
    if (t < 0.0 || t > cumulative) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{"Composite Curve parameter t="} + std::to_string(t)
                + " is outside [0, " + std::to_string(cumulative) + "]",
            "§4.4"});
    }

    // Locate the constituent whose sub-interval contains t. Endpoint at
    // t == cumulative goes to the last constituent.
    std::size_t active = 0;
    for (std::size_t i = 0; i < legs.size(); ++i) {
        Real next = (i + 1 < legs.size()) ? legs[i + 1].t_start : cumulative;
        if (t <= next) {
            active = i;
            break;
        }
    }

    Leg const& leg = legs[active];
    Real local_t = leg.v0 + (t - leg.t_start);

    auto child = evaluate_entity_dispatch(
        leg.resolved.type, leg.resolved.form, leg.resolved.xform_de, leg.resolved.data,
        local_t, std::nullopt, resolver);
    if (!child) return std::unexpected(child.error());

    // Propagate the point; clear any tangent the child may have set —
    // the composite's default parameterization does not necessarily have
    // C¹ continuity at leg boundaries.
    EvalResult r;
    r.point = child->point;
    return r;
}


std::expected<EvalResult, Diagnostic>
evaluate_offset_curve(OffsetCurveEntity const& ent,
                      Real t,
                      EntityResolver const& resolver) {
    if (ent.flag != 1) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{"Offset Curve evaluator supports only FLAG=1 "}
                + "(uniform offset); got FLAG=" + std::to_string(ent.flag),
            "§4.25"});
    }
    if (!is_valid_de(ent.de1.value)) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{"Offset Curve has invalid base curve DE pointer "}
                + std::to_string(ent.de1.value),
            "§4.25"});
    }
    if (t < ent.tt1 || t > ent.tt2) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{"Offset Curve parameter t="} + std::to_string(t)
                + " is outside [TT1, TT2] = ["
                + std::to_string(ent.tt1) + ", " + std::to_string(ent.tt2) + "]",
            "§4.25"});
    }

    auto base = resolver(ent.de1.value);
    if (!base) return std::unexpected(base.error());
    auto child = evaluate_entity_dispatch(
        base->type, base->form, base->xform_de, base->data, t, std::nullopt, resolver);
    if (!child) return std::unexpected(child.error());

    // Uniform offset: displace the base point by d1 along (vx, vy, vz).
    // §4.25 defines (VX, VY, VZ) as a unit vector; the offset magnitude
    // is d1, so the displacement is d1 · (vx, vy, vz). We do not
    // re-normalize here — agents are expected to produce unit normals
    // in their output (validation lives in the writer/parser layer).
    EvalResult r;
    r.point.x = child->point.x + ent.d1 * ent.vx;
    r.point.y = child->point.y + ent.d1 * ent.vy;
    r.point.z = child->point.z + ent.d1 * ent.vz;
    return r;
}


// Helper for Ruled Surface: sample a resolved curve at a native
// parameter and return just the point.
static std::expected<Vec3, Diagnostic>
sample_curve_point(ResolvedEntity const& curve,
                   Real u,
                   EntityResolver const& resolver) {
    auto r = evaluate_entity_dispatch(
        curve.type, curve.form, curve.xform_de, curve.data, u, std::nullopt, resolver);
    if (!r) return std::unexpected(r.error());
    return r->point;
}

std::expected<EvalResult, Diagnostic>
evaluate_tabulated_cylinder(TabulatedCylinderEntity const& ent,
                            Real t,
                            Real s,
                            EntityResolver const& resolver) {
    if (!is_valid_de(ent.de.value)) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{"Tabulated Cylinder has invalid directrix DE pointer "}
                + std::to_string(ent.de.value),
            "§4.19"});
    }
    if (s < 0.0 || s > 1.0) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{"Tabulated Cylinder s="} + std::to_string(s)
                + " must lie in [0, 1]",
            "§4.19"});
    }

    auto directrix = resolver(ent.de.value);
    if (!directrix) return std::unexpected(directrix.error());

    auto span = curve_native_span(
        directrix->type, directrix->form, directrix->data);
    if (!span) return std::unexpected(span.error());

    if (t < span->first || t > span->second) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{"Tabulated Cylinder parameter t="} + std::to_string(t)
                + " is outside the directrix domain ["
                + std::to_string(span->first) + ", "
                + std::to_string(span->second) + "]",
            "§4.19"});
    }

    auto directrix_start = sample_curve_point(*directrix, span->first, resolver);
    if (!directrix_start) return std::unexpected(directrix_start.error());
    auto directrix_point = sample_curve_point(*directrix, t, resolver);
    if (!directrix_point) return std::unexpected(directrix_point.error());

    Vec3 generatrix{
        ent.terminate_point.x - directrix_start->x,
        ent.terminate_point.y - directrix_start->y,
        ent.terminate_point.z - directrix_start->z,
    };

    EvalResult r;
    r.point.x = directrix_point->x + s * generatrix.x;
    r.point.y = directrix_point->y + s * generatrix.y;
    r.point.z = directrix_point->z + s * generatrix.z;
    return r;
}

std::expected<EvalResult, Diagnostic>
evaluate_offset_surface(OffsetSurfaceEntity const& ent,
                        Real t,
                        Real s,
                        EntityResolver const& resolver) {
    if (!is_valid_de(ent.de.value)) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{"Offset Surface has invalid base surface DE pointer "}
                + std::to_string(ent.de.value),
            "§4.30"});
    }

    auto base = resolver(ent.de.value);
    if (!base) return std::unexpected(base.error());

    auto point = sample_surface_point(
        base->type, base->form, base->xform_de, base->data, t, s, resolver);
    if (!point) return std::unexpected(point.error());
    auto normal = sample_surface_normal(
        base->type, base->form, base->xform_de, base->data, t, s, resolver);
    if (!normal) return std::unexpected(normal.error());
    auto ref_params = surface_reference_parameters(
        base->type, base->form, base->data, resolver);
    if (!ref_params) return std::unexpected(ref_params.error());
    auto ref_normal = sample_surface_normal(
        base->type, base->form, base->xform_de, base->data,
        ref_params->u, ref_params->v, resolver);
    if (!ref_normal) return std::unexpected(ref_normal.error());

    auto indicator = normalize_or_error(
        Vec3{ent.nx, ent.ny, ent.nz},
        "Offset Surface indicator vector must be non-zero",
        "§4.30");
    if (!indicator) return std::unexpected(indicator.error());

    // The indicator vector selects which global orientation counts as the
    // surface's positive normal. Anchor that choice at a stable reference
    // parameter pair, then apply the same sign to the local normal at (t, s).
    Vec3 oriented_normal = *normal;
    if (dot(*ref_normal, *indicator) < 0.0) {
        oriented_normal = -1.0 * oriented_normal;
    }

    EvalResult r;
    r.point = *point + ent.d * oriented_normal;
    return r;
}

std::expected<EvalResult, Diagnostic>
evaluate_ruled_surface(RuledSurfaceEntity const& ent,
                       int form,
                       Real t,
                       Real s,
                       EntityResolver const& resolver) {
    if (!is_valid_de(ent.de1.value) || !is_valid_de(ent.de2.value)) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            "Ruled Surface has invalid DE pointer for de1 or de2", "§4.17"});
    }
    if (s < 0.0 || s > 1.0) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{"Ruled Surface s="} + std::to_string(s)
                + " must lie in [0, 1]",
            "§4.17"});
    }

    auto c1 = resolver(ent.de1.value);
    if (!c1) return std::unexpected(c1.error());
    auto c2 = resolver(ent.de2.value);
    if (!c2) return std::unexpected(c2.error());

    // Decide the curve parameter for each curve from t.
    Real u1 = 0.0;
    Real u2 = 0.0;
    if (form == 0) {
        // Form 0: t ∈ [0, 1] is a fraction of each curve's native span.
        if (t < 0.0 || t > 1.0) {
            return std::unexpected(Diagnostic{
                Diagnostic::Severity::Error, 0, SectionKind::Parameter,
                std::string{"Ruled Surface form 0 expects t ∈ [0, 1]; got "}
                    + std::to_string(t),
                "§4.17"});
        }
        auto sp1 = curve_native_span(c1->type, c1->form, c1->data);
        if (!sp1) return std::unexpected(sp1.error());
        auto sp2 = curve_native_span(c2->type, c2->form, c2->data);
        if (!sp2) return std::unexpected(sp2.error());
        u1 = sp1->first + t * (sp1->second - sp1->first);
        // dirflg=1 traverses curve 2 in reverse.
        Real t2 = (ent.dirflg == 1) ? (1.0 - t) : t;
        u2 = sp2->first + t2 * (sp2->second - sp2->first);
    } else if (form == 1) {
        // Form 1: t is directly the native curve parameter for both
        // curves. Spec assumes both domains are identical; we do not
        // enforce that here (the evaluator just samples both at t).
        u1 = t;
        u2 = t;
        if (ent.dirflg == 1) {
            // Flip by reflecting within the second curve's native span.
            auto sp2 = curve_native_span(c2->type, c2->form, c2->data);
            if (!sp2) return std::unexpected(sp2.error());
            u2 = sp2->first + sp2->second - t;
        }
    } else {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{"Ruled Surface has unsupported form "}
                + std::to_string(form),
            "§4.17"});
    }

    auto p1 = sample_curve_point(*c1, u1, resolver);
    if (!p1) return std::unexpected(p1.error());
    auto p2 = sample_curve_point(*c2, u2, resolver);
    if (!p2) return std::unexpected(p2.error());

    // Linear rule: P(t, s) = (1 − s) · P1 + s · P2.
    EvalResult r;
    r.point.x = (1.0 - s) * p1->x + s * p2->x;
    r.point.y = (1.0 - s) * p1->y + s * p2->y;
    r.point.z = (1.0 - s) * p1->z + s * p2->z;
    return r;
}


// Rotate vector v around unit axis k by angle a (Rodrigues' formula).
static Vec3 rotate_around_unit_axis(Vec3 const& v, Vec3 const& k, Real a) {
    Real c = std::cos(a);
    Real sn = std::sin(a);
    Real dot = k.x * v.x + k.y * v.y + k.z * v.z;
    Vec3 cross{
        k.y * v.z - k.z * v.y,
        k.z * v.x - k.x * v.z,
        k.x * v.y - k.y * v.x,
    };
    return Vec3{
        v.x * c + cross.x * sn + k.x * dot * (1.0 - c),
        v.y * c + cross.y * sn + k.y * dot * (1.0 - c),
        v.z * c + cross.z * sn + k.z * dot * (1.0 - c),
    };
}

std::expected<EvalResult, Diagnostic>
evaluate_surface_of_revolution(SurfaceOfRevolutionEntity const& ent,
                               Real t,
                               Real s,
                               EntityResolver const& resolver) {
    if (!is_valid_de(ent.l.value) || !is_valid_de(ent.c.value)) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            "Surface of Revolution has invalid axis or generatrix DE pointer",
            "§4.18"});
    }

    auto axis = resolver(ent.l.value);
    if (!axis) return std::unexpected(axis.error());
    if (axis->type != 110) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{"Surface of Revolution axis must be Type 110 Line; got type "}
                + std::to_string(axis->type),
            "§4.18"});
    }
    // Pull axis line endpoints directly from JSON so we don't need the
    // entity struct include here.
    Vec3 ax_start{
        axis->data.at("start").at(0).get<Real>(),
        axis->data.at("start").at(1).get<Real>(),
        axis->data.at("start").at(2).get<Real>(),
    };
    Vec3 ax_end{
        axis->data.at("terminate").at(0).get<Real>(),
        axis->data.at("terminate").at(1).get<Real>(),
        axis->data.at("terminate").at(2).get<Real>(),
    };
    auto transformed_ax_start = apply_point_transform(
        ax_start, axis->xform_de, resolver);
    if (!transformed_ax_start) return std::unexpected(transformed_ax_start.error());
    auto transformed_ax_end = apply_point_transform(
        ax_end, axis->xform_de, resolver);
    if (!transformed_ax_end) return std::unexpected(transformed_ax_end.error());
    ax_start = *transformed_ax_start;
    ax_end = *transformed_ax_end;
    Vec3 axis_dir{
        ax_end.x - ax_start.x,
        ax_end.y - ax_start.y,
        ax_end.z - ax_start.z,
    };
    Real axis_len = std::sqrt(
        axis_dir.x * axis_dir.x
        + axis_dir.y * axis_dir.y
        + axis_dir.z * axis_dir.z);
    if (axis_len < 1e-15) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            "Surface of Revolution axis has zero length", "§4.18"});
    }
    Vec3 k{axis_dir.x / axis_len, axis_dir.y / axis_len, axis_dir.z / axis_len};

    // Evaluate generatrix at native parameter t.
    auto gen = resolver(ent.c.value);
    if (!gen) return std::unexpected(gen.error());
    auto genpt = sample_curve_point(*gen, t, resolver);
    if (!genpt) return std::unexpected(genpt.error());

    if (s < ent.sa || s > ent.ta) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            std::string{"Surface of Revolution s="} + std::to_string(s)
                + " is outside [SA, TA] = ["
                + std::to_string(ent.sa) + ", " + std::to_string(ent.ta) + "]",
            "§4.18"});
    }

    // Radius vector from axis-projected foot to the generatrix point.
    Vec3 rel{
        genpt->x - ax_start.x,
        genpt->y - ax_start.y,
        genpt->z - ax_start.z,
    };
    Real along = rel.x * k.x + rel.y * k.y + rel.z * k.z;
    Vec3 foot{
        ax_start.x + along * k.x,
        ax_start.y + along * k.y,
        ax_start.z + along * k.z,
    };
    Vec3 radial{genpt->x - foot.x, genpt->y - foot.y, genpt->z - foot.z};

    Vec3 rotated = rotate_around_unit_axis(radial, k, s);
    EvalResult r;
    r.point.x = foot.x + rotated.x;
    r.point.y = foot.y + rotated.y;
    r.point.z = foot.z + rotated.z;
    return r;
}

std::expected<EvalResult, Diagnostic>
evaluate_plane_surface(PlaneSurfaceEntity const& ent,
                       Real t,
                       Real s,
                       EntityResolver const& resolver) {
    if (ent.derefd.is_null()) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            "Plane Surface requires form 1 for parametric evaluation",
            "§4.50"});
    }
    auto center = resolve_point_entity(
        ent.deloc.value, "Plane Surface location", "§4.50", resolver);
    if (!center) return std::unexpected(center.error());
    auto normal_raw = resolve_direction_entity(
        ent.denrml.value, "Plane Surface normal", "§4.50", resolver);
    if (!normal_raw) return std::unexpected(normal_raw.error());
    auto z_axis = normalize_or_error(
        *normal_raw, "Plane Surface normal must be non-zero", "§4.50");
    if (!z_axis) return std::unexpected(z_axis.error());
    auto ref_dir = resolve_surface_reference_direction(
        ent.derefd.value, "Plane Surface reference direction", "§4.50", resolver);
    if (!ref_dir) return std::unexpected(ref_dir.error());
    auto x_axis = build_surface_x_axis(
        *ref_dir, *z_axis,
        "Plane Surface reference direction must not be parallel to the normal",
        "§4.50");
    if (!x_axis) return std::unexpected(x_axis.error());

    EvalResult r;
    r.point = *center + t * *x_axis + s * cross(*z_axis, *x_axis);
    return r;
}

std::expected<EvalResult, Diagnostic>
evaluate_cylindrical_surface(CylindricalSurfaceEntity const& ent,
                             Real t,
                             Real s,
                             EntityResolver const& resolver) {
    if (ent.derefd.is_null()) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            "Cylindrical Surface requires form 1 for parametric evaluation",
            "§4.51"});
    }
    auto center = resolve_point_entity(
        ent.deloc.value, "Cylindrical Surface location", "§4.51", resolver);
    if (!center) return std::unexpected(center.error());
    auto axis_raw = resolve_direction_entity(
        ent.deaxis.value, "Cylindrical Surface axis", "§4.51", resolver);
    if (!axis_raw) return std::unexpected(axis_raw.error());
    auto z_axis = normalize_or_error(
        *axis_raw, "Cylindrical Surface axis must be non-zero", "§4.51");
    if (!z_axis) return std::unexpected(z_axis.error());
    auto ref_dir = resolve_surface_reference_direction(
        ent.derefd.value, "Cylindrical Surface reference direction", "§4.51", resolver);
    if (!ref_dir) return std::unexpected(ref_dir.error());
    auto x_axis = build_surface_x_axis(
        *ref_dir, *z_axis,
        "Cylindrical Surface reference direction must not be parallel to the axis",
        "§4.51");
    if (!x_axis) return std::unexpected(x_axis.error());
    Vec3 y_axis = cross(*z_axis, *x_axis);
    Real u = t * 3.14159265358979323846 / 180.0;

    EvalResult r;
    r.point = *center + ent.radius * (std::cos(u) * *x_axis + std::sin(u) * y_axis) + s * *z_axis;
    return r;
}

std::expected<EvalResult, Diagnostic>
evaluate_conical_surface(ConicalSurfaceEntity const& ent,
                         Real t,
                         Real s,
                         EntityResolver const& resolver) {
    if (ent.derefd.is_null()) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            "Conical Surface requires form 1 for parametric evaluation",
            "§4.52"});
    }
    auto center = resolve_point_entity(
        ent.deloc.value, "Conical Surface location", "§4.52", resolver);
    if (!center) return std::unexpected(center.error());
    auto axis_raw = resolve_direction_entity(
        ent.deaxis.value, "Conical Surface axis", "§4.52", resolver);
    if (!axis_raw) return std::unexpected(axis_raw.error());
    auto z_axis = normalize_or_error(
        *axis_raw, "Conical Surface axis must be non-zero", "§4.52");
    if (!z_axis) return std::unexpected(z_axis.error());
    auto ref_dir = resolve_surface_reference_direction(
        ent.derefd.value, "Conical Surface reference direction", "§4.52", resolver);
    if (!ref_dir) return std::unexpected(ref_dir.error());
    auto x_axis = build_surface_x_axis(
        *ref_dir, *z_axis,
        "Conical Surface reference direction must not be parallel to the axis",
        "§4.52");
    if (!x_axis) return std::unexpected(x_axis.error());
    Vec3 y_axis = cross(*z_axis, *x_axis);
    Real u = t * 3.14159265358979323846 / 180.0;
    Real radius = ent.radius + s * std::tan(ent.sangle * 3.14159265358979323846 / 180.0);

    EvalResult r;
    r.point = *center + radius * (std::cos(u) * *x_axis + std::sin(u) * y_axis) + s * *z_axis;
    return r;
}

std::expected<EvalResult, Diagnostic>
evaluate_spherical_surface(SphericalSurfaceEntity const& ent,
                           Real t,
                           Real s,
                           EntityResolver const& resolver) {
    if (ent.deaxis.is_null() || ent.derefd.is_null()) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            "Spherical Surface requires form 1 for parametric evaluation",
            "§4.53"});
    }
    auto center = resolve_point_entity(
        ent.deloc.value, "Spherical Surface center", "§4.53", resolver);
    if (!center) return std::unexpected(center.error());
    auto axis_raw = resolve_direction_entity(
        ent.deaxis.value, "Spherical Surface axis", "§4.53", resolver);
    if (!axis_raw) return std::unexpected(axis_raw.error());
    auto z_axis = normalize_or_error(
        *axis_raw, "Spherical Surface axis must be non-zero", "§4.53");
    if (!z_axis) return std::unexpected(z_axis.error());
    auto ref_dir = resolve_surface_reference_direction(
        ent.derefd.value, "Spherical Surface reference direction", "§4.53", resolver);
    if (!ref_dir) return std::unexpected(ref_dir.error());
    auto x_axis = build_surface_x_axis(
        *ref_dir, *z_axis,
        "Spherical Surface reference direction must not be parallel to the axis",
        "§4.53");
    if (!x_axis) return std::unexpected(x_axis.error());
    Vec3 y_axis = cross(*z_axis, *x_axis);
    Real u = t * 3.14159265358979323846 / 180.0;
    Real v = s * 3.14159265358979323846 / 180.0;

    EvalResult r;
    r.point = *center + ent.radius * (
        std::cos(v) * (std::cos(u) * *x_axis + std::sin(u) * y_axis)
        + std::sin(v) * *z_axis
    );
    return r;
}

std::expected<EvalResult, Diagnostic>
evaluate_toroidal_surface(ToroidalSurfaceEntity const& ent,
                          Real t,
                          Real s,
                          EntityResolver const& resolver) {
    if (ent.derefd.is_null()) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            "Toroidal Surface requires form 1 for parametric evaluation",
            "§4.54"});
    }
    auto center = resolve_point_entity(
        ent.deloc.value, "Toroidal Surface center", "§4.54", resolver);
    if (!center) return std::unexpected(center.error());
    auto axis_raw = resolve_direction_entity(
        ent.deaxis.value, "Toroidal Surface axis", "§4.54", resolver);
    if (!axis_raw) return std::unexpected(axis_raw.error());
    auto z_axis = normalize_or_error(
        *axis_raw, "Toroidal Surface axis must be non-zero", "§4.54");
    if (!z_axis) return std::unexpected(z_axis.error());
    auto ref_dir = resolve_surface_reference_direction(
        ent.derefd.value, "Toroidal Surface reference direction", "§4.54", resolver);
    if (!ref_dir) return std::unexpected(ref_dir.error());
    auto x_axis = build_surface_x_axis(
        *ref_dir, *z_axis,
        "Toroidal Surface reference direction must not be parallel to the axis",
        "§4.54");
    if (!x_axis) return std::unexpected(x_axis.error());
    Vec3 y_axis = cross(*z_axis, *x_axis);
    Real u = t * 3.14159265358979323846 / 180.0;
    Real v = s * 3.14159265358979323846 / 180.0;

    EvalResult r;
    r.point = *center
        + (ent.majrad + ent.minrad * std::cos(u))
            * (std::cos(v) * *x_axis - std::sin(v) * y_axis)
        + ent.minrad * std::sin(u) * *z_axis;
    return r;
}

std::expected<EvalResult, Diagnostic>
apply_entity_transform(EvalResult result,
                       int xform_de,
                       EntityResolver const& resolver) {
    if (xform_de == 0) return result;

    auto point = apply_point_transform(result.point, xform_de, resolver);
    if (!point) return std::unexpected(point.error());
    result.point = *point;

    if (result.tangent.has_value()) {
        auto tangent = apply_vector_transform(*result.tangent, xform_de, resolver);
        if (!tangent) return std::unexpected(tangent.error());
        result.tangent = *tangent;
    }
    if (result.normal.has_value()) {
        auto normal = apply_vector_transform(*result.normal, xform_de, resolver);
        if (!normal) return std::unexpected(normal.error());
        result.normal = *normal;
    }
    return result;
}

} // namespace iges
