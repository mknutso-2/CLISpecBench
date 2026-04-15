// iges::AttributeTableDefinitionEntity — Full implementation.

#include "attribute_table_definition_entity.hpp"

namespace iges {

namespace {

// Read a single attribute value based on AVDT.
std::expected<AttributeValue, Diagnostic>
read_value(ParamTokenizer& tok, int avdt) {
    switch (avdt) {
        case 1: case 6: { // Integer or Logical
            auto v = tok.next_integer();
            if (!v) return std::unexpected(v.error());
            return AttributeValue{*v};
        }
        case 2: { // Real
            auto v = tok.next_real();
            if (!v) return std::unexpected(v.error());
            return AttributeValue{*v};
        }
        case 3: { // String
            auto v = tok.next_string();
            if (!v) return std::unexpected(v.error());
            return AttributeValue{*v};
        }
        case 4: { // Pointer
            auto v = tok.next_pointer();
            if (!v) return std::unexpected(v.error());
            return AttributeValue{*v};
        }
        default:
            return std::unexpected(Diagnostic{
                Diagnostic::Severity::Error, 0, SectionKind::Parameter,
                "unsupported AVDT value", "§4.79"});
    }
}

} // namespace

std::expected<AttributeTableDefinitionEntity, Diagnostic>
parse_attribute_table_definition_entity(ParamTokenizer& tok, int form) {
    AttributeTableDefinitionEntity e;

    auto name = tok.next_string(); if (!name) return std::unexpected(name.error()); e.name = *name;
    auto alt = tok.next_integer(); if (!alt) return std::unexpected(alt.error()); e.alt = *alt;
    auto na = tok.next_integer(); if (!na) return std::unexpected(na.error()); e.na = *na;

    e.attributes.reserve(e.na);
    for (int i = 0; i < e.na; ++i) {
        AttributeEntry attr;

        auto at = tok.next_integer(); if (!at) return std::unexpected(at.error()); attr.at = *at;
        auto avdt = tok.next_integer(); if (!avdt) return std::unexpected(avdt.error()); attr.avdt = *avdt;
        auto avc = tok.next_integer(); if (!avc) return std::unexpected(avc.error()); attr.avc = *avc;

        if (form == 1) {
            // Form 1: AVC values follow each attribute definition
            attr.values.reserve(attr.avc);
            for (int j = 0; j < attr.avc; ++j) {
                auto v = read_value(tok, attr.avdt);
                if (!v) return std::unexpected(v.error());
                attr.values.push_back(std::move(*v));
            }
        } else if (form == 2) {
            // Form 2: {value, display pointer} pairs follow
            attr.values.reserve(attr.avc);
            attr.display_ptrs.reserve(attr.avc);
            for (int j = 0; j < attr.avc; ++j) {
                auto v = read_value(tok, attr.avdt);
                if (!v) return std::unexpected(v.error());
                attr.values.push_back(std::move(*v));
                auto dp = tok.next_pointer();
                if (!dp) return std::unexpected(dp.error());
                attr.display_ptrs.push_back(*dp);
            }
        }

        e.attributes.push_back(std::move(attr));
    }

    return e;
}

} // namespace iges
