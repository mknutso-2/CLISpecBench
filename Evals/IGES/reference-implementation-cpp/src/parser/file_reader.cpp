// iges::read_iges_file — Full IGES file reader implementation.

#include "file_reader.hpp"
#include "lexer.hpp"
#include "../model/global_section.hpp"
#include <algorithm>
#include <map>

namespace iges {

static Diagnostic make_diag(int line, SectionKind kind,
                            std::string msg, std::string spec_ref) {
    return Diagnostic{Diagnostic::Severity::Error, line, kind,
                      std::move(msg), std::move(spec_ref)};
}

std::expected<IgesFile, DiagList>
read_iges_file(std::istream& input) {
    // Step 1: Lex all lines
    auto lex_result = Lexer::read_all(input);
    if (!lex_result.has_value()) {
        return std::unexpected(lex_result.error());
    }
    auto& lines = lex_result.value();

    IgesFile file;
    DiagList errors;

    // Step 2: Separate lines by section
    std::vector<SectionLine*> start_lines, global_lines, de_lines, pd_lines;

    for (auto& line : lines) {
        switch (line.kind) {
            case SectionKind::Start:     start_lines.push_back(&line); break;
            case SectionKind::Global:    global_lines.push_back(&line); break;
            case SectionKind::Directory: de_lines.push_back(&line); break;
            case SectionKind::Parameter: pd_lines.push_back(&line); break;
            case SectionKind::Terminate: break;  // handled implicitly
            case SectionKind::Flag:      break;  // compressed format flag
        }
    }

    // Step 3: Start section
    for (auto* sl : start_lines) {
        // Trim trailing spaces
        auto data = sl->data;
        auto end = data.find_last_not_of(' ');
        if (end != std::string::npos) {
            data.resize(end + 1);
        } else {
            data.clear();
        }
        file.start_lines.push_back(std::move(data));
    }

    // Step 4: Global section — concatenate all G-line data
    if (global_lines.empty()) {
        errors.push_back(make_diag(0, SectionKind::Global,
            "no Global section lines found", "§2.2.4.3"));
        return std::unexpected(std::move(errors));
    }

    std::string global_data;
    for (auto* gl : global_lines) {
        global_data += gl->data;
    }
    // Trim trailing spaces
    auto gend = global_data.find_last_not_of(' ');
    if (gend != std::string::npos) {
        global_data.resize(gend + 1);
    }

    auto global_result = parse_global_section(global_data);
    if (!global_result.has_value()) {
        return std::unexpected(global_result.error());
    }
    file.global = std::move(global_result.value());

    // Step 5: Directory entries — pairs of lines
    if (de_lines.size() % 2 != 0) {
        errors.push_back(make_diag(0, SectionKind::Directory,
            "odd number of DE lines", "§2.2.4.4"));
        return std::unexpected(std::move(errors));
    }

    std::vector<DirectoryEntry> des;
    for (std::size_t i = 0; i < de_lines.size(); i += 2) {
        // DE lines have data in cols 1-72 but we need the full 80-col line
        // The lexer gives us cols 1-72 in .data. We need to reconstruct
        // the full line for parse_directory_entry which expects 72+ chars.
        auto& d1 = de_lines[i]->data;
        auto& d2 = de_lines[i + 1]->data;

        auto de_result = parse_directory_entry(d1, d2, static_cast<int>(i + 1));
        if (!de_result.has_value()) {
            errors.push_back(de_result.error());
            continue;
        }
        des.push_back(std::move(de_result.value()));
    }

    if (!errors.empty()) {
        return std::unexpected(std::move(errors));
    }

    // Step 6: Parameter data — group PD lines by DE back-pointer
    // PD lines have the DE sequence number in cols 66-72 (the lexer gives
    // us cols 1-64 in .data; we need the back-pointer from the original line).
    // However, our lexer only gives us cols 1-64 for PD lines.
    // We'll reconstruct by ordering PD lines by sequence number and
    // matching them to DEs by the param_data_ptr.

    // Build a map: PD sequence number -> PD data
    std::map<int, std::string> pd_by_seq;
    for (auto* pl : pd_lines) {
        pd_by_seq[pl->sequence_number] = pl->data;
    }

    // For each DE, concatenate its PD lines
    for (auto& de : des) {
        std::string pd_concat;
        for (int seq = de.param_data_ptr;
             seq < de.param_data_ptr + de.param_line_count; ++seq) {
            auto it = pd_by_seq.find(seq);
            if (it != pd_by_seq.end()) {
                // Trim trailing spaces from each PD line's data
                auto data = it->second;
                auto end = data.find_last_not_of(' ');
                if (end != std::string::npos) {
                    data.resize(end + 1);
                } else {
                    data.clear();
                }
                pd_concat += data;
            }
        }

        // Strip entity type number prefix from PD string.
        // PD format is: "entity_type,param1,param2,...;"
        // We need to remove "entity_type," to get just the parameter data.
        auto comma = pd_concat.find(',');
        if (comma != std::string::npos) {
            pd_concat = pd_concat.substr(comma + 1);
        }

        file.entities.push_back({std::move(de), std::move(pd_concat)});
    }

    return file;
}

} // namespace iges
