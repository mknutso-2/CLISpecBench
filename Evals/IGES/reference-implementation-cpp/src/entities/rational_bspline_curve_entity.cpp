// iges::RationalBSplineCurveEntity — Full implementation.

#include "rational_bspline_curve_entity.hpp"
#include <algorithm>

namespace iges {

// de Boor's algorithm for evaluating a B-spline curve at parameter t.
// For a rational B-spline, we evaluate in homogeneous coordinates
// (w*x, w*y, w*z, w) and then divide by w.
Vec3 RationalBSplineCurveEntity::evaluate(Real t) const {
    int n = K + 1;  // number of control points
    int p = M;      // degree

    // Clamp t to the valid range
    t = std::clamp(t, knots[p], knots[K + 1]);

    // Find the knot span index: the largest index i such that
    // knots[i] <= t < knots[i+1], with special handling for the
    // end of the range.
    int span = p;
    for (int i = p; i < K + 1; ++i) {
        if (t < knots[i + 1]) {
            span = i;
            break;
        }
        span = i;
    }

    // de Boor's algorithm in homogeneous coordinates
    // Initialize with the relevant control points weighted
    struct Homo { Real x, y, z, w; };
    std::vector<Homo> d(p + 1);
    for (int j = 0; j <= p; ++j) {
        int idx = span - p + j;
        Real w = weights[idx];
        d[j] = {control_points[idx].x * w,
                control_points[idx].y * w,
                control_points[idx].z * w,
                w};
    }

    for (int r = 1; r <= p; ++r) {
        for (int j = p; j >= r; --j) {
            int idx = span - p + j;
            Real left  = knots[idx];
            Real right = knots[idx + p - r + 1];
            Real denom = right - left;
            if (denom == 0.0) {
                // Overlapping knots — keep the value
                continue;
            }
            Real alpha = (t - left) / denom;
            d[j].x = (1.0 - alpha) * d[j-1].x + alpha * d[j].x;
            d[j].y = (1.0 - alpha) * d[j-1].y + alpha * d[j].y;
            d[j].z = (1.0 - alpha) * d[j-1].z + alpha * d[j].z;
            d[j].w = (1.0 - alpha) * d[j-1].w + alpha * d[j].w;
        }
    }

    // Dehomogenize
    Real iw = 1.0 / d[p].w;
    return {d[p].x * iw, d[p].y * iw, d[p].z * iw};
}

std::expected<RationalBSplineCurveEntity, Diagnostic>
parse_rational_bspline_curve_entity(ParamTokenizer& tok) {
    RationalBSplineCurveEntity e;

    // K and M
    auto k_v = tok.next_integer();
    if (!k_v) return std::unexpected(k_v.error());
    e.K = *k_v;

    auto m_v = tok.next_integer();
    if (!m_v) return std::unexpected(m_v.error());
    e.M = *m_v;

    // PROP1-4
    auto p1 = tok.next_integer();
    if (!p1) return std::unexpected(p1.error());
    e.prop1 = *p1;

    auto p2 = tok.next_integer();
    if (!p2) return std::unexpected(p2.error());
    e.prop2 = *p2;

    auto p3 = tok.next_integer();
    if (!p3) return std::unexpected(p3.error());
    e.prop3 = *p3;

    auto p4 = tok.next_integer();
    if (!p4) return std::unexpected(p4.error());
    e.prop4 = *p4;

    // Knot vector: A+1 values
    int num_knots = e.A() + 1;
    e.knots.reserve(num_knots);
    for (int i = 0; i < num_knots; ++i) {
        auto v = tok.next_real();
        if (!v) return std::unexpected(v.error());
        e.knots.push_back(*v);
    }

    // Weights: K+1 values
    int num_weights = e.K + 1;
    e.weights.reserve(num_weights);
    for (int i = 0; i < num_weights; ++i) {
        auto v = tok.next_real();
        if (!v) return std::unexpected(v.error());
        e.weights.push_back(*v);
    }

    // Control points: K+1 triples (X, Y, Z)
    int num_pts = e.K + 1;
    e.control_points.reserve(num_pts);
    for (int i = 0; i < num_pts; ++i) {
        auto x = tok.next_real();
        if (!x) return std::unexpected(x.error());
        auto y = tok.next_real();
        if (!y) return std::unexpected(y.error());
        auto z = tok.next_real();
        if (!z) return std::unexpected(z.error());
        e.control_points.push_back({*x, *y, *z});
    }

    // V(0) and V(1)
    auto v0 = tok.next_real();
    if (!v0) return std::unexpected(v0.error());
    e.v0 = *v0;

    auto v1 = tok.next_real();
    if (!v1) return std::unexpected(v1.error());
    e.v1 = *v1;

    // Plane normal (3 reals) — present regardless of PROP1
    auto nx = tok.next_real_or(0.0);
    if (nx) e.plane_normal.x = *nx;
    auto ny = tok.next_real_or(0.0);
    if (ny) e.plane_normal.y = *ny;
    auto nz = tok.next_real_or(0.0);
    if (nz) e.plane_normal.z = *nz;

    return e;
}

} // namespace iges
