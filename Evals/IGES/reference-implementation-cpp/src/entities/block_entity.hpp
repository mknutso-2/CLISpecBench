#pragma once
// iges::BlockEntity — Type 150.
//
// §4.37: "The block is a rectangular parallelepipeds, defined with
//   one vertex at (X1,Y1,Z1) and three edges lying along the local
//   +X, +Y, and +Z axes."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>

namespace iges {

struct BlockEntity {
    Real lx = 0.0, ly = 0.0, lz = 0.0;  // Edge lengths
    Vec3 corner = {0, 0, 0};              // Corner point
    Vec3 x_axis = {1, 0, 0};             // Local X-axis
    Vec3 z_axis = {0, 0, 1};             // Local Z-axis
};

std::expected<BlockEntity, Diagnostic>
parse_block_entity(ParamTokenizer& tok);

} // namespace iges
