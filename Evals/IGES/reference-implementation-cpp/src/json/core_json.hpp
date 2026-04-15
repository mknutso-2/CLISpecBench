#pragma once
// iges::json — ADL serializers for core value types (types.hpp + entity.hpp).
//
// nlohmann::json requires to_json / from_json free functions in the same
// namespace as the type. All of the shared scalar, enum, strong-typedef
// and small aggregate types live in `iges::`, so their serializers live here.

#include "../types.hpp"
#include "../entities/entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <nlohmann/json.hpp>
#include <string>
#include <variant>

namespace iges {

// ── Enums ────────────────────────────────────────────────────
// Using NLOHMANN_JSON_SERIALIZE_ENUM-style table so the JSON stays
// human-readable rather than emitting raw integer codes.

NLOHMANN_JSON_SERIALIZE_ENUM(Units, {
    {Units::Inches,       "inches"},
    {Units::Millimeters,  "millimeters"},
    {Units::SeeField15,   "see_field_15"},
    {Units::Feet,         "feet"},
    {Units::Miles,        "miles"},
    {Units::Meters,       "meters"},
    {Units::Kilometers,   "kilometers"},
    {Units::Mils,         "mils"},
    {Units::Microns,      "microns"},
    {Units::Centimeters,  "centimeters"},
    {Units::Microinches,  "microinches"},
})

NLOHMANN_JSON_SERIALIZE_ENUM(SpecVersion, {
    {SpecVersion::V1_0,      "v1_0"},
    {SpecVersion::ANSI_1981, "ansi_1981"},
    {SpecVersion::V2_0,      "v2_0"},
    {SpecVersion::V3_0,      "v3_0"},
    {SpecVersion::ASME_1987, "asme_1987"},
    {SpecVersion::V4_0,      "v4_0"},
    {SpecVersion::ASME_1989, "asme_1989"},
    {SpecVersion::V5_0,      "v5_0"},
    {SpecVersion::V5_2,      "v5_2"},
    {SpecVersion::V5_1,      "v5_1"},
    {SpecVersion::V5_3,      "v5_3"},
})

NLOHMANN_JSON_SERIALIZE_ENUM(DraftingStandard, {
    {DraftingStandard::None,  "none"},
    {DraftingStandard::ISO,   "iso"},
    {DraftingStandard::AFNOR, "afnor"},
    {DraftingStandard::ANSI,  "ansi"},
    {DraftingStandard::BSI,   "bsi"},
    {DraftingStandard::CSA,   "csa"},
    {DraftingStandard::DIN,   "din"},
    {DraftingStandard::JIS,   "jis"},
})

NLOHMANN_JSON_SERIALIZE_ENUM(BlankStatus, {
    {BlankStatus::Visible, "visible"},
    {BlankStatus::Blanked, "blanked"},
})

NLOHMANN_JSON_SERIALIZE_ENUM(SubordinateSwitch, {
    {SubordinateSwitch::Independent,         "independent"},
    {SubordinateSwitch::PhysicallyDependent, "physically_dependent"},
    {SubordinateSwitch::LogicallyDependent,  "logically_dependent"},
    {SubordinateSwitch::Both,                "both"},
})

NLOHMANN_JSON_SERIALIZE_ENUM(EntityUseFlag, {
    {EntityUseFlag::Geometry,             "geometry"},
    {EntityUseFlag::Annotation,           "annotation"},
    {EntityUseFlag::Definition,           "definition"},
    {EntityUseFlag::Other,                "other"},
    {EntityUseFlag::LogicalPositional,    "logical_positional"},
    {EntityUseFlag::Parametric2D,         "parametric_2d"},
    {EntityUseFlag::ConstructionGeometry, "construction_geometry"},
})

NLOHMANN_JSON_SERIALIZE_ENUM(HierarchyFlag, {
    {HierarchyFlag::GlobalTopDown, "global_top_down"},
    {HierarchyFlag::GlobalDefer,   "global_defer"},
    {HierarchyFlag::UseProperty,   "use_property"},
})

// ── Strong typedefs ──────────────────────────────────────────
// Serialize as raw integer values.

inline void to_json(nlohmann::json& j, DEIndex const& d) { j = d.value; }
inline void from_json(nlohmann::json const& j, DEIndex& d) { d.value = j.get<int>(); }

inline void to_json(nlohmann::json& j, EntityType const& t) { j = t.value; }
inline void from_json(nlohmann::json const& j, EntityType& t) { t.value = j.get<int>(); }

inline void to_json(nlohmann::json& j, FormNumber const& f) { j = f.value; }
inline void from_json(nlohmann::json const& j, FormNumber& f) { f.value = j.get<int>(); }

// ── Variant fields (line_font / level / color) ───────────────
// Emitted as the raw signed integer (positive = value, negative = pointer).

inline void to_json(nlohmann::json& j, LineFontVariant const& v) { j = v.raw; }
inline void from_json(nlohmann::json const& j, LineFontVariant& v) { v.raw = j.get<int>(); }

inline void to_json(nlohmann::json& j, LevelVariant const& v) { j = v.raw; }
inline void from_json(nlohmann::json const& j, LevelVariant& v) { v.raw = j.get<int>(); }

inline void to_json(nlohmann::json& j, ColorVariant const& v) { j = v.raw; }
inline void from_json(nlohmann::json const& j, ColorVariant& v) { v.raw = j.get<int>(); }

// ── Timestamp ────────────────────────────────────────────────

inline void to_json(nlohmann::json& j, Timestamp const& t) {
    j = nlohmann::json{
        {"year",   t.year},
        {"month",  t.month},
        {"day",    t.day},
        {"hour",   t.hour},
        {"minute", t.minute},
        {"second", t.second},
    };
}
inline void from_json(nlohmann::json const& j, Timestamp& t) {
    j.at("year").get_to(t.year);
    j.at("month").get_to(t.month);
    j.at("day").get_to(t.day);
    j.at("hour").get_to(t.hour);
    j.at("minute").get_to(t.minute);
    j.at("second").get_to(t.second);
}

// ── Vec3 ─────────────────────────────────────────────────────

inline void to_json(nlohmann::json& j, Vec3 const& v) {
    j = nlohmann::json::array({v.x, v.y, v.z});
}
inline void from_json(nlohmann::json const& j, Vec3& v) {
    if (!j.is_array() || j.size() != 3) {
        throw nlohmann::json::type_error::create(302, "Vec3 must be an array of three numbers", &j);
    }
    j.at(0).get_to(v.x);
    j.at(1).get_to(v.y);
    j.at(2).get_to(v.z);
}

// ── Matrix3x3 ────────────────────────────────────────────────

inline void to_json(nlohmann::json& j, Matrix3x3 const& m) {
    j = nlohmann::json::array();
    for (int r = 0; r < 3; ++r) {
        nlohmann::json row = nlohmann::json::array();
        for (int c = 0; c < 3; ++c) row.push_back(m(r, c));
        j.push_back(row);
    }
}
inline void from_json(nlohmann::json const& j, Matrix3x3& m) {
    if (!j.is_array() || j.size() != 3) {
        throw nlohmann::json::type_error::create(302, "Matrix3x3 must be a 3x3 array", &j);
    }
    for (int r = 0; r < 3; ++r) {
        auto const& row = j.at(r);
        if (!row.is_array() || row.size() != 3) {
            throw nlohmann::json::type_error::create(302, "Matrix3x3 row must have three numbers", &j);
        }
        for (int c = 0; c < 3; ++c) row.at(c).get_to(m(r, c));
    }
}

// ── AttributeValue (std::variant<int, Real, std::string, DEIndex>) ───
// Emit as a tagged object so roundtrip is unambiguous.
// { "kind": "int"|"real"|"string"|"pointer", "value": <scalar> }

inline void to_json(nlohmann::json& j, std::variant<int, Real, std::string, DEIndex> const& v) {
    std::visit([&j](auto const& x) {
        using T = std::decay_t<decltype(x)>;
        if constexpr (std::is_same_v<T, int>) {
            j = nlohmann::json{{"kind", "int"}, {"value", x}};
        } else if constexpr (std::is_same_v<T, Real>) {
            j = nlohmann::json{{"kind", "real"}, {"value", x}};
        } else if constexpr (std::is_same_v<T, std::string>) {
            j = nlohmann::json{{"kind", "string"}, {"value", x}};
        } else if constexpr (std::is_same_v<T, DEIndex>) {
            j = nlohmann::json{{"kind", "pointer"}, {"value", x.value}};
        }
    }, v);
}

inline void from_json(nlohmann::json const& j, std::variant<int, Real, std::string, DEIndex>& v) {
    auto kind = j.at("kind").get<std::string>();
    auto const& value = j.at("value");
    if      (kind == "int")     v = value.get<int>();
    else if (kind == "real")    v = value.get<Real>();
    else if (kind == "string")  v = value.get<std::string>();
    else if (kind == "pointer") v = DEIndex{value.get<int>()};
    else throw nlohmann::json::type_error::create(302, "AttributeValue: unknown kind", &j);
}

// ── FieldValue (ParamTokenizer variant) ──────────────────────
// FieldValue = variant<DefaultedField, int, Real, std::string, bool>
// Emitted as a tagged object so roundtrip is unambiguous.
// { "kind": "defaulted"|"int"|"real"|"string"|"bool", "value": <scalar> }
// For the "defaulted" case, "value" is null.

inline void to_json(nlohmann::json& j, DefaultedField const&) {
    j = nlohmann::json{{"kind", "defaulted"}, {"value", nullptr}};
}
inline void from_json(nlohmann::json const&, DefaultedField&) {
    // Nothing to read — the tag itself carries all information.
}

inline void to_json(nlohmann::json& j, FieldValue const& v) {
    std::visit([&j](auto const& x) {
        using T = std::decay_t<decltype(x)>;
        if constexpr (std::is_same_v<T, DefaultedField>) {
            j = nlohmann::json{{"kind", "defaulted"}, {"value", nullptr}};
        } else if constexpr (std::is_same_v<T, int>) {
            j = nlohmann::json{{"kind", "int"}, {"value", x}};
        } else if constexpr (std::is_same_v<T, Real>) {
            j = nlohmann::json{{"kind", "real"}, {"value", x}};
        } else if constexpr (std::is_same_v<T, std::string>) {
            j = nlohmann::json{{"kind", "string"}, {"value", x}};
        } else if constexpr (std::is_same_v<T, bool>) {
            j = nlohmann::json{{"kind", "bool"}, {"value", x}};
        }
    }, v);
}

inline void from_json(nlohmann::json const& j, FieldValue& v) {
    auto kind = j.at("kind").get<std::string>();
    auto const& value = j.at("value");
    if      (kind == "defaulted") v = DefaultedField{};
    else if (kind == "int")       v = value.get<int>();
    else if (kind == "real")      v = value.get<Real>();
    else if (kind == "string")    v = value.get<std::string>();
    else if (kind == "bool")      v = value.get<bool>();
    else throw nlohmann::json::type_error::create(302, "FieldValue: unknown kind", &j);
}

} // namespace iges
