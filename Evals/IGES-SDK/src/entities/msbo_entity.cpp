// iges::MSBOEntity — Full implementation.

#include "msbo_entity.hpp"

namespace iges {

std::expected<MSBOEntity, Diagnostic>
parse_msbo_entity(ParamTokenizer& tok) {
    MSBOEntity e;

    auto shell = tok.next_pointer(); if (!shell) return std::unexpected(shell.error()); e.shell = *shell;
    auto sof = tok.next_logical(); if (!sof) return std::unexpected(sof.error()); e.sof = *sof;
    auto n = tok.next_integer(); if (!n) return std::unexpected(n.error()); e.n = *n;

    e.voids.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        VoidShell vs;
        auto vshell = tok.next_pointer(); if (!vshell) return std::unexpected(vshell.error()); vs.shell = *vshell;
        auto vof = tok.next_logical(); if (!vof) return std::unexpected(vof.error()); vs.orientation = *vof;
        e.voids.push_back(vs);
    }

    return e;
}

} // namespace iges
