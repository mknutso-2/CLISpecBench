// iges::ExternalReferenceEntity — Full implementation.

#include "external_reference_entity.hpp"

namespace iges {

std::expected<ExternalReferenceEntity, Diagnostic>
parse_external_reference_entity(ParamTokenizer& tok, int form) {
    ExternalReferenceEntity e;

    if (form == 0 || form == 2) {
        // §4.138 Forms 0 and 2: EXTFID + EXTNAM
        auto fn = tok.next_string(); if (!fn) return std::unexpected(fn.error()); e.filename = *fn;
        auto en = tok.next_string(); if (!en) return std::unexpected(en.error()); e.entity_name = *en;
    } else if (form == 1) {
        // §4.138 Form 1: EXTFID only (entire file)
        auto fn = tok.next_string(); if (!fn) return std::unexpected(fn.error()); e.filename = *fn;
    } else if (form == 3) {
        // §4.138 Form 3: EXTNAM only
        auto en = tok.next_string(); if (!en) return std::unexpected(en.error()); e.entity_name = *en;
    } else if (form == 4) {
        // §4.138 Form 4: LIBNAM + EXTNAM
        auto fn = tok.next_string(); if (!fn) return std::unexpected(fn.error()); e.filename = *fn;
        auto en = tok.next_string(); if (!en) return std::unexpected(en.error()); e.entity_name = *en;
    }

    return e;
}

} // namespace iges
