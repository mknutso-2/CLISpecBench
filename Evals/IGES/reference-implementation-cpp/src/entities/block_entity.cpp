// iges::BlockEntity — Full implementation.

#include "block_entity.hpp"

namespace iges {

std::expected<BlockEntity, Diagnostic>
parse_block_entity(ParamTokenizer& tok) {
    BlockEntity e;

    auto lx = tok.next_real();
    if (!lx) return std::unexpected(lx.error());
    e.lx = *lx;

    auto ly = tok.next_real();
    if (!ly) return std::unexpected(ly.error());
    e.ly = *ly;

    auto lz = tok.next_real();
    if (!lz) return std::unexpected(lz.error());
    e.lz = *lz;

    auto x1 = tok.next_real_or(0.0);
    if (!x1) return std::unexpected(x1.error());
    e.corner.x = *x1;

    auto y1 = tok.next_real_or(0.0);
    if (!y1) return std::unexpected(y1.error());
    e.corner.y = *y1;

    auto z1 = tok.next_real_or(0.0);
    if (!z1) return std::unexpected(z1.error());
    e.corner.z = *z1;

    auto i1 = tok.next_real_or(1.0);
    if (!i1) return std::unexpected(i1.error());
    e.x_axis.x = *i1;

    auto j1 = tok.next_real_or(0.0);
    if (!j1) return std::unexpected(j1.error());
    e.x_axis.y = *j1;

    auto k1 = tok.next_real_or(0.0);
    if (!k1) return std::unexpected(k1.error());
    e.x_axis.z = *k1;

    auto i2 = tok.next_real_or(0.0);
    if (!i2) return std::unexpected(i2.error());
    e.z_axis.x = *i2;

    auto j2 = tok.next_real_or(0.0);
    if (!j2) return std::unexpected(j2.error());
    e.z_axis.y = *j2;

    auto k2 = tok.next_real_or(1.0);
    if (!k2) return std::unexpected(k2.error());
    e.z_axis.z = *k2;

    return e;
}

} // namespace iges
