// iges::write_global_section — Implementation.

#include "global_writer.hpp"
#include "format.hpp"
#include "param_writer.hpp"
#include <format>

namespace iges {

static std::string format_timestamp_str(Timestamp const& ts) {
    // §2.2.4.3.18: "15HYYYYMMDD.HHNNSS" — we emit the 15-char 4-digit year format
    return std::format("{:04}{:02}{:02}.{:02}{:02}{:02}",
        ts.year, ts.month, ts.day, ts.hour, ts.minute, ts.second);
}

std::string write_global_section(GlobalSection const& g) {
    ParamWriter pw(g.param_delimiter, g.record_delimiter);

    // Field 1: parameter delimiter as 1H Hollerith
    pw.write_string(std::string(1, g.param_delimiter));
    // Field 2: record delimiter as 1H Hollerith
    pw.write_string(std::string(1, g.record_delimiter));
    // Field 3: product ID sender
    pw.write_string(g.product_id_sender);
    // Field 4: file name
    pw.write_string(g.file_name);
    // Field 5: native system ID
    pw.write_string(g.native_system_id);
    // Field 6: preprocessor version
    pw.write_string(g.preprocessor_version);
    // Field 7-11: numeric precision
    pw.write_integer(g.integer_bits);
    pw.write_integer(g.sp_magnitude);
    pw.write_integer(g.sp_significance);
    pw.write_integer(g.dp_magnitude);
    pw.write_integer(g.dp_significance);
    // Field 12: product ID receiver
    pw.write_string(g.product_id_receiver.empty() ? g.product_id_sender : g.product_id_receiver);
    // Field 13: model space scale
    pw.write_real(g.model_space_scale);
    // Field 14: units flag
    pw.write_integer(static_cast<int>(g.units));
    // Field 15: units name
    pw.write_string(g.units_name);
    // Field 16: max line weight gradations
    pw.write_integer(g.max_line_weight_grads);
    // Field 17: max line weight width
    pw.write_real(g.max_line_weight_width);
    // Field 18: file timestamp
    pw.write_string(format_timestamp_str(g.file_timestamp));
    // Field 19: min resolution
    pw.write_real(g.min_resolution);
    // Field 20: max coordinate
    pw.write_real(g.max_coordinate);
    // Field 21: author
    pw.write_string(g.author);
    // Field 22: organization
    pw.write_string(g.organization);
    // Field 23: version flag
    pw.write_integer(static_cast<int>(g.spec_version));
    // Field 24: drafting standard
    pw.write_integer(static_cast<int>(g.drafting_std));
    // Field 25: model timestamp
    if (g.model_timestamp.has_value()) {
        pw.write_string(format_timestamp_str(*g.model_timestamp));
    } else {
        pw.write_string("");
    }
    // Field 26: app protocol
    pw.write_string(g.app_protocol);
    // Terminate record (this adds the record delimiter)
    pw.end_record();

    return pw.str();
}

} // namespace iges
