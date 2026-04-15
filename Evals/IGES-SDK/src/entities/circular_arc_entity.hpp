#pragma once
// iges::CircularArcEntity — Type 100.

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct CircularArcEntity {
    Real zt = 0.0;   // ZT displacement from XT,YT plane
    Real x1 = 0.0;   // Center X
    Real y1 = 0.0;   // Center Y
    Real x2 = 0.0;   // Start X
    Real y2 = 0.0;   // Start Y
    Real x3 = 0.0;   // Terminate X
    Real y3 = 0.0;   // Terminate Y

    // Derived: radius
    Real radius() const;

    // Evaluate default parameterization at angle t (radians).
    Vec3 evaluate(Real t) const;

    // Start and terminate angles (radians from center).
    Real start_angle() const;
    Real terminate_angle() const;

    // Is this a full circle? (start == terminate point)
    bool is_full_circle() const;
};

std::expected<CircularArcEntity, Diagnostic>
parse_circular_arc_entity(ParamTokenizer& tok);

} // namespace iges
