#pragma once
// iges::Entity — Base for all IGES entity parameter data.
//
// Each concrete entity holds its parsed PD fields. The DirectoryEntry
// holds the DE metadata; the entity struct holds the geometry/topology.

#include "../types.hpp"
#include <array>
#include <cmath>
#include <vector>

namespace iges {

// ── 3D point / vector helpers ───────────────────────────────────

struct Vec3 {
    Real x = 0.0, y = 0.0, z = 0.0;

    constexpr Vec3() = default;
    constexpr Vec3(Real x_, Real y_, Real z_) : x(x_), y(y_), z(z_) {}

    constexpr Vec3 operator+(Vec3 const& o) const { return {x+o.x, y+o.y, z+o.z}; }
    constexpr Vec3 operator-(Vec3 const& o) const { return {x-o.x, y-o.y, z-o.z}; }
    constexpr Vec3 operator*(Real s) const { return {x*s, y*s, z*s}; }

    Real length() const { return std::sqrt(x*x + y*y + z*z); }
    Real length_sq() const { return x*x + y*y + z*z; }

    constexpr bool operator==(Vec3 const&) const = default;
};

inline constexpr Vec3 operator*(Real s, Vec3 const& v) { return v * s; }

inline Real dot(Vec3 const& a, Vec3 const& b) {
    return a.x*b.x + a.y*b.y + a.z*b.z;
}

inline Vec3 cross(Vec3 const& a, Vec3 const& b) {
    return {a.y*b.z - a.z*b.y,
            a.z*b.x - a.x*b.z,
            a.x*b.y - a.y*b.x};
}

// ── 3x3 matrix + translation (Transformation Matrix Entity) ────

struct Matrix3x3 {
    std::array<std::array<Real, 3>, 3> r = {{{1,0,0},{0,1,0},{0,0,1}}};

    constexpr Real& operator()(int row, int col) { return r[row][col]; }
    constexpr Real  operator()(int row, int col) const { return r[row][col]; }

    constexpr bool operator==(Matrix3x3 const&) const = default;
};

inline Vec3 operator*(Matrix3x3 const& m, Vec3 const& v) {
    return {m(0,0)*v.x + m(0,1)*v.y + m(0,2)*v.z,
            m(1,0)*v.x + m(1,1)*v.y + m(1,2)*v.z,
            m(2,0)*v.x + m(2,1)*v.y + m(2,2)*v.z};
}

Real determinant(Matrix3x3 const& m);
Matrix3x3 multiply(Matrix3x3 const& a, Matrix3x3 const& b);
Matrix3x3 transpose(Matrix3x3 const& m);

} // namespace iges
