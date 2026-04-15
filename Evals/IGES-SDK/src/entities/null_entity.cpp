// iges::NullEntity — Full implementation.

#include "null_entity.hpp"

namespace iges {

std::expected<NullEntity, Diagnostic>
parse_null_entity(ParamTokenizer& /*tok*/) {
    // §4.1: No parameters — the PD section contains only the entity type number
    return NullEntity{};
}

} // namespace iges
