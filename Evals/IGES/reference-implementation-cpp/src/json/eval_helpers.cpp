// iges::eval_helpers — resolver-using evaluators.

#include "eval_helpers.hpp"

#include <cmath>

namespace iges {

namespace {

// Convert a 1-based odd DE index to a 0-based pair index.
// §2.2.4.4: DE pointers are 1, 3, 5, …; (de−1)/2 is the entity's index
// in the Directory Entry section.
bool is_valid_de(int de) {
    return de >= 1 && (de % 2) == 1;
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
        leg.resolved.type, leg.resolved.form, leg.resolved.data,
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
        base->type, base->form, base->data, t, std::nullopt, resolver);
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
        curve.type, curve.form, curve.data, u, std::nullopt, resolver);
    if (!r) return std::unexpected(r.error());
    return r->point;
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

} // namespace iges
