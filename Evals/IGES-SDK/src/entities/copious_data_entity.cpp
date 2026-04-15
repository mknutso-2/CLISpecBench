// iges::CopiousDataEntity — Full implementation.

#include "copious_data_entity.hpp"

namespace iges {

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
