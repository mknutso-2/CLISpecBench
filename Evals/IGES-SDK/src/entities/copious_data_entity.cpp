// iges::CopiousDataEntity — Full implementation.

#include "copious_data_entity.hpp"

#include <cmath>

namespace iges {

Vec3 CopiousDataEntity::point_at(int k) const {
    if (ip == 1) {
        return Vec3{data[k * 2], data[k * 2 + 1], zt};
    }
    if (ip == 2) {
        return Vec3{data[k * 3], data[k * 3 + 1], data[k * 3 + 2]};
    }
    // ip == 3: 6 values per tuple (point + vector); return point component only.
    return Vec3{data[k * 6], data[k * 6 + 1], data[k * 6 + 2]};
}

Vec3 CopiousDataEntity::evaluate(Real t) const {
    if (n <= 0) return Vec3{0.0, 0.0, 0.0};
    if (n == 1) return point_at(0);

    // Clamp to domain [0, n-1].
    if (t <= 0.0) return point_at(0);
    if (t >= static_cast<Real>(n - 1)) return point_at(n - 1);

    int i = static_cast<int>(std::floor(t));
    Real frac = t - static_cast<Real>(i);
    Vec3 a = point_at(i);
    Vec3 b = point_at(i + 1);
    return Vec3{
        a.x + frac * (b.x - a.x),
        a.y + frac * (b.y - a.y),
        a.z + frac * (b.z - a.z),
    };
}

std::expected<CopiousDataEntity, Diagnostic>
parse_copious_data_entity(ParamTokenizer& tok) {
    CopiousDataEntity e;

    auto ip = tok.next_integer(); if (!ip) return std::unexpected(ip.error()); e.ip = *ip;
    auto n = tok.next_integer(); if (!n) return std::unexpected(n.error()); e.n = *n;

    if (e.ip == 1) {
        auto zt = tok.next_real(); if (!zt) return std::unexpected(zt.error()); e.zt = *zt;
    }

    int values_per_tuple = 0;
    if (e.ip == 1) values_per_tuple = 2;
    else if (e.ip == 2) values_per_tuple = 3;
    else if (e.ip == 3) values_per_tuple = 6;

    int total = e.n * values_per_tuple;
    e.data.reserve(total);
    for (int i = 0; i < total; ++i) {
        auto v = tok.next_real(); if (!v) return std::unexpected(v.error());
        e.data.push_back(*v);
    }

    return e;
}

} // namespace iges
