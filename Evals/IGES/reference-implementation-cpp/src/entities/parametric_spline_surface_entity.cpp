// iges::ParametricSplineSurfaceEntity — Type 114 implementation.

#include "parametric_spline_surface_entity.hpp"
#include <algorithm>

namespace iges {

Vec3 ParametricSplineSurfaceEntity::evaluate(Real u, Real v) const {
    if (patches.empty()) return {};

    // Clamp u, v
    u = std::clamp(u, tu.front(), tu.back());
    v = std::clamp(v, tv.front(), tv.back());

    // Find u segment index
    int ui = M - 1;
    for (int k = 0; k < M; ++k) {
        if (u < tu[k + 1]) { ui = k; break; }
    }

    // Find v segment index
    int vi = N - 1;
    for (int k = 0; k < N; ++k) {
        if (v < tv[k + 1]) { vi = k; break; }
    }

    Real s = u - tu[ui];
    Real t = v - tv[vi];

    auto const& p = patches[ui * N + vi];

    // Evaluate bicubic polynomial:
    // X(u,v) = sum_{r=0}^{3} sum_{c=0}^{3} coeff[4*r+c] * s^c * t^r
    auto eval_coord = [&](Real const coeff[16]) -> Real {
        Real result = 0.0;
        Real t_pow = 1.0;
        for (int r = 0; r < 4; ++r) {
            Real s_pow = 1.0;
            for (int c = 0; c < 4; ++c) {
                result += coeff[4 * r + c] * s_pow * t_pow;
                s_pow *= s;
            }
            t_pow *= t;
        }
        return result;
    };

    return {eval_coord(p.coeff_x),
            eval_coord(p.coeff_y),
            eval_coord(p.coeff_z)};
}

std::expected<ParametricSplineSurfaceEntity, Diagnostic>
parse_parametric_spline_surface_entity(ParamTokenizer& tok) {
    ParametricSplineSurfaceEntity e;

    auto v_ctype = tok.next_integer();
    if (!v_ctype) return std::unexpected(v_ctype.error());
    e.ctype = *v_ctype;

    auto v_ptype = tok.next_integer();
    if (!v_ptype) return std::unexpected(v_ptype.error());
    e.ptype = *v_ptype;

    auto v_m = tok.next_integer();
    if (!v_m) return std::unexpected(v_m.error());
    e.M = *v_m;

    auto v_n = tok.next_integer();
    if (!v_n) return std::unexpected(v_n.error());
    e.N = *v_n;

    // Read M+1 u breakpoints
    e.tu.resize(e.M + 1);
    for (int k = 0; k <= e.M; ++k) {
        auto v = tok.next_real();
        if (!v) return std::unexpected(v.error());
        e.tu[k] = *v;
    }

    // Read N+1 v breakpoints
    e.tv.resize(e.N + 1);
    for (int k = 0; k <= e.N; ++k) {
        auto v = tok.next_real();
        if (!v) return std::unexpected(v.error());
        e.tv[k] = *v;
    }

    // Read patches. Each patch has 48 coefficients (16 X + 16 Y + 16 Z).
    // Patches are stored in row-major order: for j=1..N, for i=1..M... actually
    // per the spec, the order is: patch (1,1), then (1,2), ... (1,N),
    // then arbitrary values for row 1 boundary, then (2,1), etc.
    // For simplicity, read M*N patches sequentially, skipping arbitrary values.
    int total_patches = e.M * e.N;
    e.patches.resize(total_patches);

    // The spec says patches are laid out with arbitrary boundary values
    // interleaved after each row. For a conforming reader, we read the
    // complete set of 48 coefficients for each patch in (i,j) order
    // where i is the u-index and j is the v-index, row by row.
    // The boundary arbitrary values between rows are for the N+1th column
    // and M+1th row — postprocessors shall ignore them.
    // We read exactly M*(N+1) + 1 groups of 48, but only keep M*N.
    // Actually, per a strict reading, the layout includes:
    //   for each u-row i (1..M):
    //     for each v-col j (1..N): 48 coefficients
    //     48 arbitrary values (boundary column N+1)
    //   then M+1 row: N+1 groups of 48 arbitrary values
    //
    // For a practical parser, read all patches including boundary,
    // but only store the M*N real patches.

    for (int i = 0; i < e.M; ++i) {
        for (int j = 0; j < e.N; ++j) {
            auto& patch = e.patches[i * e.N + j];
            for (int c = 0; c < 16; ++c) {
                auto v = tok.next_real();
                if (!v) return std::unexpected(v.error());
                patch.coeff_x[c] = *v;
            }
            for (int c = 0; c < 16; ++c) {
                auto v = tok.next_real();
                if (!v) return std::unexpected(v.error());
                patch.coeff_y[c] = *v;
            }
            for (int c = 0; c < 16; ++c) {
                auto v = tok.next_real();
                if (!v) return std::unexpected(v.error());
                patch.coeff_z[c] = *v;
            }
        }
        // Skip N+1th column boundary values (48 arbitrary reals)
        for (int c = 0; c < 48; ++c) {
            auto v = tok.next_real();
            if (!v) break;  // may not be present
        }
    }
    // Skip M+1th row boundary values
    // These may or may not be present; read until record delimiter

    return e;
}

} // namespace iges
