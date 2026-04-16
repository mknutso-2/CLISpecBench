// iges::GlobalSection — Full implementation.
// Parses all 26 fields of §2.2.4.3.

#include "global_section.hpp"
#include "../parser/param_tokenizer.hpp"

namespace iges {

std::expected<GlobalSection, DiagList>
parse_global_section(std::string_view data) {
    GlobalSection g;
    DiagList errors;
    auto push_error = [&](Diagnostic d) {
        d.section = SectionKind::Global;
        errors.push_back(std::move(d));
    };

    // First, we need to detect the delimiters from fields 1-2.
    // Field 1 may be: "1Hx," where x is the custom param delimiter,
    // or defaulted (starts with ",,") meaning comma is default.
    // Field 2 is similar for the record delimiter.

    char pd = ',';  // param delimiter (default)
    char rd = ';';  // record delimiter (default)

    std::size_t pos = 0;

    // Try to parse field 1 (param delimiter)
    if (data.size() > 2 && data[0] == '1' && data[1] == 'H') {
        // 1Hx form: custom param delimiter
        pd = data[2];
        pos = 3;
        // Consume the delimiter after field 1
        if (pos < data.size() && (data[pos] == ',' || data[pos] == pd)) {
            // Use the ORIGINAL comma for now until we know the new pd
            pos++;
        }
    } else if (data.size() > 0 && data[0] == ',') {
        // Defaulted field 1: comma stays
        pos = 1;
    }

    // Try to parse field 2 (record delimiter)
    if (pos < data.size() && data.size() > pos + 2 &&
        data[pos] == '1' && data[pos+1] == 'H') {
        rd = data[pos+2];
        pos += 3;
        // Consume delimiter after field 2
        if (pos < data.size() && (data[pos] == pd || data[pos] == ',')) {
            pos++;
        }
    } else if (pos < data.size() && (data[pos] == pd || data[pos] == ',')) {
        // Defaulted field 2: semicolon stays
        pos++;
    }

    g.param_delimiter = pd;
    g.record_delimiter = rd;

    // Now tokenize remaining fields (3-26) using the detected delimiters
    auto remaining = data.substr(pos);
    ParamTokenizer tok(remaining, pd, rd);

    // Field 3: Product identification from sender (required, no default)
    if (auto r = tok.next_string(); r.has_value()) {
        g.product_id_sender = r.value();
    } else {
        push_error(r.error());
    }

    // Field 4: File name (required, no default)
    if (auto r = tok.next_string(); r.has_value()) {
        g.file_name = r.value();
    } else {
        push_error(r.error());
    }

    // Field 5: Native System ID
    if (auto r = tok.next_string(); r.has_value()) {
        g.native_system_id = r.value();
    } else {
        push_error(r.error());
    }

    // Field 6: Preprocessor version
    if (auto r = tok.next_string(); r.has_value()) {
        g.preprocessor_version = r.value();
    } else {
        push_error(r.error());
    }

    // Field 7: Integer bits
    if (auto r = tok.next_integer(); r.has_value()) {
        g.integer_bits = r.value();
    } else {
        push_error(r.error());
    }

    // Field 8: SP magnitude
    if (auto r = tok.next_integer(); r.has_value()) {
        g.sp_magnitude = r.value();
    } else {
        push_error(r.error());
    }

    // Field 9: SP significance
    if (auto r = tok.next_integer(); r.has_value()) {
        g.sp_significance = r.value();
    } else {
        push_error(r.error());
    }

    // Field 10: DP magnitude
    if (auto r = tok.next_integer(); r.has_value()) {
        g.dp_magnitude = r.value();
    } else {
        push_error(r.error());
    }

    // Field 11: DP significance
    if (auto r = tok.next_integer(); r.has_value()) {
        g.dp_significance = r.value();
    } else {
        push_error(r.error());
    }

    // Field 12: Product ID receiver (default = field 3)
    if (auto r = tok.next_string_or(g.product_id_sender); r.has_value()) {
        g.product_id_receiver = r.value();
    } else {
        push_error(r.error());
    }

    // Field 13: Model space scale (default 1.0)
    if (auto r = tok.next_real_or(1.0); r.has_value()) {
        g.model_space_scale = r.value();
    } else {
        push_error(r.error());
    }

    // Field 14: Units flag (default 1)
    if (auto r = tok.next_integer_or(1); r.has_value()) {
        g.units = static_cast<Units>(r.value());
    } else {
        push_error(r.error());
    }

    // Field 15: Units name (default "IN")
    if (auto r = tok.next_string_or("IN"); r.has_value()) {
        g.units_name = r.value();
    } else {
        push_error(r.error());
    }

    // Field 16: Max line weight gradations (default 1)
    if (auto r = tok.next_integer_or(1); r.has_value()) {
        g.max_line_weight_grads = r.value();
    } else {
        push_error(r.error());
    }

    // Field 17: Max line weight width (required, no default)
    if (auto r = tok.next_real_or(0.0); r.has_value()) {
        g.max_line_weight_width = r.value();
    } else {
        push_error(r.error());
    }

    // Field 18: File timestamp (required, no default)
    if (auto r = tok.next_string(); r.has_value()) {
        if (auto ts = parse_timestamp(r.value()); ts.has_value()) {
            g.file_timestamp = ts.value();
        } else {
            push_error(ts.error());
        }
    } else {
        push_error(r.error());
    }

    // Field 19: Minimum resolution
    if (auto r = tok.next_real_or(0.0); r.has_value()) {
        g.min_resolution = r.value();
    } else {
        push_error(r.error());
    }

    // Field 20: Max coordinate (default 0.0)
    if (auto r = tok.next_real_or(0.0); r.has_value()) {
        g.max_coordinate = r.value();
    } else {
        push_error(r.error());
    }

    // Field 21: Author (default empty)
    if (auto r = tok.next_string_or(""); r.has_value()) {
        g.author = r.value();
    } else {
        push_error(r.error());
    }

    // Field 22: Organization (default empty)
    if (auto r = tok.next_string_or(""); r.has_value()) {
        g.organization = r.value();
    } else {
        push_error(r.error());
    }

    // Field 23: Version flag (default 3)
    {
        auto r = tok.next_integer_or(3);
        if (r.has_value()) {
            int v = r.value();
            // §2.2.4.3.23: clamp unrecognized values
            if (v < 1) v = 3;
            if (v > 11) v = 11;
            g.spec_version = static_cast<SpecVersion>(v);
        } else {
            push_error(r.error());
        }
    }

    // Field 24: Drafting standard (default 0)
    if (auto r = tok.next_integer_or(0); r.has_value()) {
        g.drafting_std = static_cast<DraftingStandard>(r.value());
    } else {
        push_error(r.error());
    }

    // Field 25: Model timestamp (default unspecified)
    {
        auto r = tok.next_string_or("");
        if (r.has_value() && !r.value().empty()) {
            if (auto ts = parse_timestamp(r.value()); ts.has_value()) {
                g.model_timestamp = ts.value();
            } else {
                push_error(ts.error());
            }
        } else if (!r.has_value()) {
            push_error(r.error());
        }
    }

    // Field 26: Application protocol (default empty)
    if (auto r = tok.next_string_or(""); r.has_value()) {
        g.app_protocol = r.value();
    } else {
        push_error(r.error());
    }

    if (!errors.empty()) {
        return std::unexpected(std::move(errors));
    }
    return g;
}

} // namespace iges
