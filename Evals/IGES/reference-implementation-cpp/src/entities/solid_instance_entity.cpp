// iges::SolidInstanceEntity — Full implementation.

#include "solid_instance_entity.hpp"

namespace iges {

std::expected<SolidInstanceEntity, Diagnostic>
parse_solid_instance_entity(ParamTokenizer& tok) {
    SolidInstanceEntity e;

    auto ptr = tok.next_pointer();
    if (!ptr) return std::unexpected(ptr.error());
    e.ptr = *ptr;

    return e;
}

} // namespace iges
