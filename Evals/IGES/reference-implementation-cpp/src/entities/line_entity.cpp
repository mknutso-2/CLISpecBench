// iges::LineEntity — Full implementation.

#include "line_entity.hpp"

namespace iges {

Vec3 LineEntity::evaluate(Real t) const {
    return start + (terminate - start) * t;
}

std::expected<LineEntity, Diagnostic>
parse_line_entity(ParamTokenizer& tok) {
    LineEntity e;

    auto x1 = tok.next_real();
    if (!x1) return std::unexpected(x1.error());
    e.start.x = *x1;

    auto y1 = tok.next_real();
    if (!y1) return std::unexpected(y1.error());
    e.start.y = *y1;

    auto z1 = tok.next_real();
    if (!z1) return std::unexpected(z1.error());
    e.start.z = *z1;

    auto x2 = tok.next_real();
    if (!x2) return std::unexpected(x2.error());
    e.terminate.x = *x2;

    auto y2 = tok.next_real();
    if (!y2) return std::unexpected(y2.error());
    e.terminate.y = *y2;

    auto z2 = tok.next_real();
    if (!z2) return std::unexpected(z2.error());
    e.terminate.z = *z2;

    // §3.2.5: "All curves shall have non-zero arc length." For a Line
    // this means start != terminate. Form 0 only; Forms 1 and 2 are
    // semi-bounded / unbounded lines and their arc length is always
    // infinite, so the points need only be distinct to define a
    // direction. The same distinctness constraint applies in both
    // cases, so the check is form-independent at parse time.
    if (e.start.x == e.terminate.x &&
        e.start.y == e.terminate.y &&
        e.start.z == e.terminate.z) {
        return std::unexpected(Diagnostic{
            Diagnostic::Severity::Error, 0, SectionKind::Parameter,
            "Line (Type 110) has coincident start and terminate points "
            "(zero arc length)",
            "§3.2.5"});
    }

    return e;
}

} // namespace iges
