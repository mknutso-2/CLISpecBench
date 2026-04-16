// iges::ConicArcEntity — Type 104 implementation.

#include "conic_arc_entity.hpp"
#include <cmath>

namespace iges {

namespace {

constexpr Real kPi = 3.14159265358979323846;
constexpr Real kTwoPi = 2.0 * kPi;

Real wrap_angle_0_2pi(Real angle) {
    while (angle < 0.0) angle += kTwoPi;
    while (angle >= kTwoPi) angle -= kTwoPi;
    return angle;
}

} // namespace

Real ConicArcEntity::Q1() const {
    // det |A   B/2 D/2|
    //     |B/2 C   E/2|
    //     |D/2 E/2 F  |
    Real b2 = B / 2.0;
    Real d2 = D / 2.0;
    Real e2 = E / 2.0;
    return A * (C * F - e2 * e2)
         - b2 * (b2 * F - e2 * d2)
         + d2 * (b2 * e2 - C * d2);
}

Real ConicArcEntity::Q2() const {
    return A * C - (B / 2.0) * (B / 2.0);
}

Real ConicArcEntity::Q3() const {
    return A + C;
}

bool ConicArcEntity::is_ellipse() const {
    Real q2 = Q2();
    return q2 > 0.0 && q2 * Q3() < 0.0;
}

bool ConicArcEntity::is_hyperbola() const {
    return Q2() < 0.0;
}

bool ConicArcEntity::is_parabola() const {
    Real q2 = Q2();
    return q2 == 0.0 && Q1() != 0.0;
}

std::pair<Real, Real> ConicArcEntity::parameter_span() const {
    if (is_parabola()) {
        if (A != 0.0 && E != 0.0) {
            if (x2 < x1) return {-x1, -x2};
            return {x1, x2};
        }
        if (C != 0.0 && D != 0.0) {
            if (y2 < y1) return {-y1, -y2};
            return {y1, y2};
        }
    }

    if (is_ellipse()) {
        Real a = std::sqrt(-F / A);
        Real b = std::sqrt(-F / C);
        auto angle_at = [&](Real x, Real y) -> Real {
            return wrap_angle_0_2pi(std::atan2(y / b, x / a));
        };
        Real t1 = angle_at(x1, y1);
        Real t2 = angle_at(x2, y2);
        if (t2 < t1) t2 += kTwoPi;
        return {t1, t2};
    }

    if (is_hyperbola()) {
        if (F * A < 0.0 && F * C > 0.0) {
            Real b = std::sqrt(F / C);
            Real t1 = std::atan(y1 / b);
            Real t2 = std::atan(y2 / b);
            if (t2 < t1) return {-t1, -t2};
            return {t1, t2};
        }
        if (F * A > 0.0 && F * C < 0.0) {
            Real a = std::sqrt(F / A);
            Real t1 = std::atan(x1 / a);
            Real t2 = std::atan(x2 / a);
            if (t2 < t1) return {-t1, -t2};
            return {t1, t2};
        }
    }

    return {0.0, 0.0};
}

Vec3 ConicArcEntity::evaluate(Real t) const {
    if (is_parabola()) {
        if (A != 0.0 && E != 0.0) {
            if (x2 < x1) return Vec3{-t, -(A / E) * t * t, zt};
            return Vec3{t, -(A / E) * t * t, zt};
        }
        if (C != 0.0 && D != 0.0) {
            if (y2 < y1) return Vec3{-(C / D) * t * t, -t, zt};
            return Vec3{-(C / D) * t * t, t, zt};
        }
    }

    if (is_ellipse()) {
        Real a = std::sqrt(-F / A);
        Real b = std::sqrt(-F / C);
        return Vec3{a * std::cos(t), b * std::sin(t), zt};
    }

    if (is_hyperbola()) {
        if (F * A < 0.0 && F * C > 0.0) {
            Real a = std::sqrt(-F / A);
            Real b = std::sqrt(F / C);
            Real t1 = std::atan(y1 / b);
            Real t2 = std::atan(y2 / b);
            if (t2 < t1) {
                return Vec3{a / std::cos(t), -b * std::tan(t), zt};
            }
            return Vec3{a / std::cos(t), b * std::tan(t), zt};
        }
        if (F * A > 0.0 && F * C < 0.0) {
            Real a = std::sqrt(F / A);
            Real b = std::sqrt(-F / C);
            Real t1 = std::atan(x1 / a);
            Real t2 = std::atan(x2 / a);
            if (t2 < t1) {
                return Vec3{-a * std::tan(t), b / std::cos(t), zt};
            }
            return Vec3{a * std::tan(t), b / std::cos(t), zt};
        }
    }

    return Vec3{0.0, 0.0, zt};
}

std::expected<ConicArcEntity, Diagnostic>
parse_conic_arc_entity(ParamTokenizer& tok) {
    ConicArcEntity e;

    auto va = tok.next_real();
    if (!va) return std::unexpected(va.error());
    e.A = *va;

    auto vb = tok.next_real();
    if (!vb) return std::unexpected(vb.error());
    e.B = *vb;

    auto vc = tok.next_real();
    if (!vc) return std::unexpected(vc.error());
    e.C = *vc;

    auto vd = tok.next_real();
    if (!vd) return std::unexpected(vd.error());
    e.D = *vd;

    auto ve = tok.next_real();
    if (!ve) return std::unexpected(ve.error());
    e.E = *ve;

    auto vf = tok.next_real();
    if (!vf) return std::unexpected(vf.error());
    e.F = *vf;

    auto vzt = tok.next_real();
    if (!vzt) return std::unexpected(vzt.error());
    e.zt = *vzt;

    auto vx1 = tok.next_real();
    if (!vx1) return std::unexpected(vx1.error());
    e.x1 = *vx1;

    auto vy1 = tok.next_real();
    if (!vy1) return std::unexpected(vy1.error());
    e.y1 = *vy1;

    auto vx2 = tok.next_real();
    if (!vx2) return std::unexpected(vx2.error());
    e.x2 = *vx2;

    auto vy2 = tok.next_real();
    if (!vy2) return std::unexpected(vy2.error());
    e.y2 = *vy2;

    return e;
}

} // namespace iges
