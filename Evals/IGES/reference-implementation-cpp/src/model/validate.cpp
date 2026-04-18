// iges::validate — Structural validation implementation.

#include "validate.hpp"
#include <set>
#include <format>

namespace iges {

static Diagnostic make_diag(SectionKind kind, std::string msg, std::string spec_ref) {
    return Diagnostic{Diagnostic::Severity::Error, 0, kind,
                      std::move(msg), std::move(spec_ref)};
}

namespace {

// Shared per-entity checks that apply to both parse and write paths.
// These are the checks that only look at DirectoryEntry fields the
// caller supplies (entity_type sign, DE cross-references), not at
// derived fields (param_line_count, pd_string).
void append_shared_de_diags(IgesFile const& file,
                             std::set<int> const& valid_de_seqs,
                             DiagList& diags) {
    for (std::size_t i = 0; i < file.entities.size(); ++i) {
        auto const& ent = file.entities[i];
        int de_seq = static_cast<int>(i) * 2 + 1;

        // §2.2.4.4: entity_type must be >= 0 (Null Entity = 0 is allowed)
        if (ent.de.entity_type.value < 0) {
            diags.push_back(make_diag(SectionKind::Directory,
                std::format("DE {} has negative entity type {}", de_seq, ent.de.entity_type.value),
                "§2.2.4.4"));
        }

        // §2.2.4.4 field 7: xform_matrix must reference a valid DE or be 0
        if (!ent.de.xform_matrix.is_null()) {
            if (valid_de_seqs.find(ent.de.xform_matrix.value) == valid_de_seqs.end()) {
                diags.push_back(make_diag(SectionKind::Directory,
                    std::format("DE {} xform_matrix points to non-existent DE {}",
                                de_seq, ent.de.xform_matrix.value),
                    "§2.2.4.4"));
            }
        }

        // §2.2.4.4 field 6: view must reference a valid DE or be 0
        if (!ent.de.view.is_null()) {
            if (valid_de_seqs.find(ent.de.view.value) == valid_de_seqs.end()) {
                diags.push_back(make_diag(SectionKind::Directory,
                    std::format("DE {} view points to non-existent DE {}",
                                de_seq, ent.de.view.value),
                    "§2.2.4.4"));
            }
        }

        // §2.2.4.4 field 8: label_display must reference a valid DE or be 0
        if (!ent.de.label_display.is_null()) {
            if (valid_de_seqs.find(ent.de.label_display.value) == valid_de_seqs.end()) {
                diags.push_back(make_diag(SectionKind::Directory,
                    std::format("DE {} label_display points to non-existent DE {}",
                                de_seq, ent.de.label_display.value),
                    "§2.2.4.4"));
            }
        }
    }
}

void append_global_diags(GlobalSection const& global, DiagList& diags);

} // namespace

DiagList validate(IgesFile const& file) {
    DiagList diags;

    // Build set of valid DE sequence numbers (odd: 1, 3, 5, ...)
    std::set<int> valid_de_seqs;
    for (std::size_t i = 0; i < file.entities.size(); ++i) {
        int de_seq = static_cast<int>(i) * 2 + 1;
        valid_de_seqs.insert(de_seq);
    }

    append_shared_de_diags(file, valid_de_seqs, diags);

    // Parse-path-only per-entity checks: param_line_count and
    // pd_string.empty(). The write path re-derives param_line_count
    // from the PD layout (see writer/file_writer.cpp) and always
    // builds a non-empty pd_string via entity-specific serializers,
    // so these checks would produce spurious rejections on the
    // write path.
    for (std::size_t i = 0; i < file.entities.size(); ++i) {
        auto const& ent = file.entities[i];
        int de_seq = static_cast<int>(i) * 2 + 1;

        // §2.2.4.4 field 14: param_line_count should be > 0
        // (except Null Entity Type 0)
        if (ent.de.param_line_count <= 0 && ent.de.entity_type.value != 0) {
            diags.push_back(make_diag(SectionKind::Directory,
                std::format("DE {} param_line_count is {} for non-null entity type {}",
                            de_seq, ent.de.param_line_count, ent.de.entity_type.value),
                "§2.2.4.4"));
        }

        // Check that PD string is non-empty for non-null entities
        if (ent.pd_string.empty() && ent.de.entity_type.value != 0) {
            diags.push_back(make_diag(SectionKind::Parameter,
                std::format("DE {} has empty parameter data for entity type {}",
                            de_seq, ent.de.entity_type.value),
                "§2.2.4.5"));
        }
    }

    append_global_diags(file.global, diags);
    return diags;
}

DiagList validate_write_input(IgesFile const& file) {
    DiagList diags;
    std::set<int> valid_de_seqs;
    for (std::size_t i = 0; i < file.entities.size(); ++i) {
        int de_seq = static_cast<int>(i) * 2 + 1;
        valid_de_seqs.insert(de_seq);
    }
    append_shared_de_diags(file, valid_de_seqs, diags);
    append_global_diags(file.global, diags);
    return diags;
}

namespace {

void append_global_diags(GlobalSection const& global, DiagList& diags) {
    // §2.2.4.3 field 7: integer_bits should be > 0
    if (global.integer_bits <= 0) {
        diags.push_back(make_diag(SectionKind::Global,
            "Global field 7 (integer_bits) is not positive",
            "§2.2.4.3"));
    }

    // §2.2.4.3 field 8: sp_magnitude should be > 0
    if (global.sp_magnitude <= 0) {
        diags.push_back(make_diag(SectionKind::Global,
            "Global field 8 (sp_magnitude) is not positive",
            "§2.2.4.3"));
    }

    // §2.2.4.3 field 9: sp_significance should be > 0
    if (global.sp_significance <= 0) {
        diags.push_back(make_diag(SectionKind::Global,
            "Global field 9 (sp_significance) is not positive",
            "§2.2.4.3"));
    }

    // §2.2.4.3 field 10: dp_magnitude should be > 0
    if (global.dp_magnitude <= 0) {
        diags.push_back(make_diag(SectionKind::Global,
            "Global field 10 (dp_magnitude) is not positive",
            "§2.2.4.3"));
    }

    // §2.2.4.3 field 11: dp_significance should be > 0
    if (global.dp_significance <= 0) {
        diags.push_back(make_diag(SectionKind::Global,
            "Global field 11 (dp_significance) is not positive",
            "§2.2.4.3"));
    }

    // §2.2.4.3 field 13: model_space_scale should be > 0
    if (global.model_space_scale <= 0.0) {
        diags.push_back(make_diag(SectionKind::Global,
            "Global field 13 (model_space_scale) is not positive",
            "§2.2.4.3"));
    }

    // §2.2.4.3 field 16: max_line_weight_grads shall be > 0
    if (global.max_line_weight_grads <= 0) {
        diags.push_back(make_diag(SectionKind::Global,
            "Global field 16 (max_line_weight_grads) is not positive",
            "§2.2.4.3"));
    }

    // §2.2.4.3 field 19: min_resolution is required, no default, and
    // TR §1.2 lists it among the non-positive-is-invalid fields.
    if (global.min_resolution <= 0.0) {
        diags.push_back(make_diag(SectionKind::Global,
            "Global field 19 (min_resolution) is not positive",
            "§2.2.4.3"));
    }
}

} // namespace

} // namespace iges
