// iges::ParametricSplineCurveEntity — Type 112 implementation.

#include "parametric_spline_curve_entity.hpp"
#include <algorithm>

namespace iges {

Vec3 ParametricSplineCurveEntity::evaluate(Real u) const {
    if (segments.empty()) return {};

    // Clamp u to valid range
    Real u_min = breakpoints.front();
    Real u_max = breakpoints.back();
    u = std::clamp(u, u_min, u_max);

    // Find segment index i such that T(i) <= u < T(i+1)
    int N = static_cast<int>(segments.size());
    int i = N - 1;  // default to last segment
    for (int k = 0; k < N; ++k) {
        if (u < breakpoints[k + 1]) {
            i = k;
            break;
        }
    }

    Real s = u - breakpoints[i];
    Real s2 = s * s;
    Real s3 = s2 * s;

    auto const& seg = segments[i];
    return {seg.ax + seg.bx * s + seg.cx * s2 + seg.dx * s3,
            seg.ay + seg.by * s + seg.cy * s2 + seg.dy * s3,
            seg.az + seg.bz * s + seg.cz * s2 + seg.dz * s3};
}

std::expected<ParametricSplineCurveEntity, Diagnostic>
parse_parametric_spline_curve_entity(ParamTokenizer& tok) {
    ParametricSplineCurveEntity e;

    auto v_ctype = tok.next_integer();
    if (!v_ctype) return std::unexpected(v_ctype.error());
    e.ctype = *v_ctype;

    auto v_h = tok.next_integer();
    if (!v_h) return std::unexpected(v_h.error());
    e.H = *v_h;

    auto v_ndim = tok.next_integer();
    if (!v_ndim) return std::unexpected(v_ndim.error());
    e.ndim = *v_ndim;

    auto v_n = tok.next_integer();
    if (!v_n) return std::unexpected(v_n.error());
    int N = *v_n;

    // Read N+1 breakpoints
    e.breakpoints.resize(N + 1);
    for (int k = 0; k <= N; ++k) {
        auto v = tok.next_real();
        if (!v) return std::unexpected(v.error());
        e.breakpoints[k] = *v;
    }

    // Read N segments, each with 12 coefficients
    e.segments.resize(N);
    for (int k = 0; k < N; ++k) {
        auto& seg = e.segments[k];
        auto read = [&](Real& out) -> bool {
            auto v = tok.next_real();
            if (!v) return false;
            out = *v;
            return true;
        };
        if (!read(seg.ax) || !read(seg.bx) || !read(seg.cx) || !read(seg.dx) ||
            !read(seg.ay) || !read(seg.by) || !read(seg.cy) || !read(seg.dy) ||
            !read(seg.az) || !read(seg.bz) || !read(seg.cz) || !read(seg.dz)) {
            return std::unexpected(Diagnostic{
                Diagnostic::Severity::Error, 0, SectionKind::Parameter,
                "Expected 12 coefficients for spline segment", "§4.14"});
        }
    }

    // Read terminate point derivatives (12 values)
    auto read_tp = [&](Real& out) -> bool {
        auto v = tok.next_real();
        if (!v) return false;
        out = *v;
        return true;
    };
    if (!read_tp(e.tpx0) || !read_tp(e.tpx1) || !read_tp(e.tpx2) || !read_tp(e.tpx3) ||
        !read_tp(e.tpy0) || !read_tp(e.tpy1) || !read_tp(e.tpy2) || !read_tp(e.tpy3) ||
        !read_tp(e.tpz0) || !read_tp(e.tpz1) || !read_tp(e.tpz2) || !read_tp(e.tpz3)) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            "Expected 12 terminate point derivatives", "§4.14"});
    }

    return e;
}

} // namespace iges
