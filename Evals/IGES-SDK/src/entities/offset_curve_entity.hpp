#pragma once
// iges::OffsetCurveEntity — Type 130.
//
// §4.25: "The Offset Curve Entity defines the data necessary to
//   determine the curve offset from a given base curve C."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct OffsetCurveEntity {
    DEIndex de1;              // Pointer to base curve to be offset
    int flag = 0;             // 1=uniform, 2=linear, 3=function
    DEIndex de2;              // Pointer to function curve (FLAG=3), else 0
    int ndim = 0;             // Coordinate of DE2 for offset (FLAG=3)
    int ptype = 0;            // 1=arc length, 2=parameter
    Real d1 = 0.0;            // First offset distance
    Real td1 = 0.0;           // Arc length or param of first offset (FLAG=2)
    Real d2 = 0.0;            // Second offset distance
    Real td2 = 0.0;           // Arc length or param of second offset (FLAG=2)
    Real vx = 0.0;            // Normal vector X component
    Real vy = 0.0;            // Normal vector Y component
    Real vz = 0.0;            // Normal vector Z component
    Real tt1 = 0.0;           // Starting parameter value
    Real tt2 = 0.0;           // Ending parameter value
};

std::expected<OffsetCurveEntity, Diagnostic>
parse_offset_curve_entity(ParamTokenizer& tok);

} // namespace iges
