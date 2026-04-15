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

} // namespace iges
