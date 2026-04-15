#pragma once
// iges::json — ADL serializers for GlobalSection, DirectoryEntry, StatusNumber,
// and the top-level envelope produced by `iges parse`.

#include "core_json.hpp"
#include "../model/directory_entry.hpp"
#include "../model/global_section.hpp"
#include <nlohmann/json.hpp>

namespace iges {

// ── StatusNumber ─────────────────────────────────────────────

inline void to_json(nlohmann::json& j, StatusNumber const& s) {
    j = nlohmann::json{
        {"blank",       s.blank},
        {"subordinate", s.subordinate},
        {"entity_use",  s.entity_use},
        {"hierarchy",   s.hierarchy},
    };
}
inline void from_json(nlohmann::json const& j, StatusNumber& s) {
    j.at("blank").get_to(s.blank);
    j.at("subordinate").get_to(s.subordinate);
    j.at("entity_use").get_to(s.entity_use);
    j.at("hierarchy").get_to(s.hierarchy);
}

// ── DirectoryEntry ───────────────────────────────────────────
// Field 10 (sequence number) and 20 are derived, so not serialized.
// Field 11 mirrors field 1, so not serialized separately.

inline void to_json(nlohmann::json& j, DirectoryEntry const& de) {
    j = nlohmann::json{
        {"entity_type",       de.entity_type},
        {"param_data_ptr",    de.param_data_ptr},
        {"structure",         de.structure},
        {"line_font",         de.line_font},
        {"level",             de.level},
        {"view",              de.view},
        {"xform_matrix",      de.xform_matrix},
        {"label_display",     de.label_display},
        {"status",            de.status},
        {"line_weight",       de.line_weight},
        {"color",             de.color},
        {"param_line_count",  de.param_line_count},
        {"form",              de.form},
        {"entity_label",      de.entity_label},
        {"entity_subscript",  de.entity_subscript},
    };
}
inline void from_json(nlohmann::json const& j, DirectoryEntry& de) {
    j.at("entity_type").get_to(de.entity_type);
    j.at("param_data_ptr").get_to(de.param_data_ptr);
    j.at("structure").get_to(de.structure);
    j.at("line_font").get_to(de.line_font);
    j.at("level").get_to(de.level);
    j.at("view").get_to(de.view);
    j.at("xform_matrix").get_to(de.xform_matrix);
    j.at("label_display").get_to(de.label_display);
    j.at("status").get_to(de.status);
    j.at("line_weight").get_to(de.line_weight);
    j.at("color").get_to(de.color);
    j.at("param_line_count").get_to(de.param_line_count);
    j.at("form").get_to(de.form);
    j.at("entity_label").get_to(de.entity_label);
    j.at("entity_subscript").get_to(de.entity_subscript);
}

// ── GlobalSection ────────────────────────────────────────────

inline void to_json(nlohmann::json& j, GlobalSection const& g) {
    j = nlohmann::json{
        {"param_delimiter",       std::string(1, g.param_delimiter)},
        {"record_delimiter",      std::string(1, g.record_delimiter)},
        {"product_id_sender",     g.product_id_sender},
        {"file_name",             g.file_name},
        {"native_system_id",      g.native_system_id},
        {"preprocessor_version",  g.preprocessor_version},
        {"integer_bits",          g.integer_bits},
        {"sp_magnitude",          g.sp_magnitude},
        {"sp_significance",       g.sp_significance},
        {"dp_magnitude",          g.dp_magnitude},
        {"dp_significance",       g.dp_significance},
        {"product_id_receiver",   g.product_id_receiver},
        {"model_space_scale",     g.model_space_scale},
        {"units",                 g.units},
        {"units_name",            g.units_name},
        {"max_line_weight_grads", g.max_line_weight_grads},
        {"max_line_weight_width", g.max_line_weight_width},
        {"file_timestamp",        g.file_timestamp},
        {"min_resolution",        g.min_resolution},
        {"max_coordinate",        g.max_coordinate},
        {"author",                g.author},
        {"organization",          g.organization},
        {"spec_version",          g.spec_version},
        {"drafting_std",          g.drafting_std},
        {"model_timestamp",       g.model_timestamp ? nlohmann::json(*g.model_timestamp) : nlohmann::json(nullptr)},
        {"app_protocol",          g.app_protocol},
    };
}
inline void from_json(nlohmann::json const& j, GlobalSection& g) {
    auto pd = j.at("param_delimiter").get<std::string>();
    auto rd = j.at("record_delimiter").get<std::string>();
    g.param_delimiter  = pd.empty() ? ',' : pd[0];
    g.record_delimiter = rd.empty() ? ';' : rd[0];
    j.at("product_id_sender").get_to(g.product_id_sender);
    j.at("file_name").get_to(g.file_name);
    j.at("native_system_id").get_to(g.native_system_id);
    j.at("preprocessor_version").get_to(g.preprocessor_version);
    j.at("integer_bits").get_to(g.integer_bits);
    j.at("sp_magnitude").get_to(g.sp_magnitude);
    j.at("sp_significance").get_to(g.sp_significance);
    j.at("dp_magnitude").get_to(g.dp_magnitude);
    j.at("dp_significance").get_to(g.dp_significance);
    j.at("product_id_receiver").get_to(g.product_id_receiver);
    j.at("model_space_scale").get_to(g.model_space_scale);
    j.at("units").get_to(g.units);
    j.at("units_name").get_to(g.units_name);
    j.at("max_line_weight_grads").get_to(g.max_line_weight_grads);
    j.at("max_line_weight_width").get_to(g.max_line_weight_width);
    j.at("file_timestamp").get_to(g.file_timestamp);
    j.at("min_resolution").get_to(g.min_resolution);
    j.at("max_coordinate").get_to(g.max_coordinate);
    j.at("author").get_to(g.author);
    j.at("organization").get_to(g.organization);
    j.at("spec_version").get_to(g.spec_version);
    j.at("drafting_std").get_to(g.drafting_std);
    auto const& ts = j.at("model_timestamp");
    if (ts.is_null()) g.model_timestamp.reset();
    else              g.model_timestamp = ts.get<Timestamp>();
    j.at("app_protocol").get_to(g.app_protocol);
}

} // namespace iges
