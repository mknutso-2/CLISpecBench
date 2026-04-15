// iges::ShellEntity — Full implementation.

#include "shell_entity.hpp"

namespace iges {

std::expected<ShellEntity, Diagnostic>
parse_shell_entity(ParamTokenizer& tok) {
    ShellEntity e;

    auto n = tok.next_integer(); if (!n) return std::unexpected(n.error()); e.n = *n;

    e.faces.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        FaceUse fu;
        auto face = tok.next_pointer(); if (!face) return std::unexpected(face.error()); fu.face = *face;
        auto of = tok.next_logical(); if (!of) return std::unexpected(of.error()); fu.orientation = *of;
        e.faces.push_back(fu);
    }

    return e;
}

} // namespace iges
