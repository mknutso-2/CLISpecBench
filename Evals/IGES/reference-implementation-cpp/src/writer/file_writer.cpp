// iges::write_iges_file — Full file assembly implementation.

#include "file_writer.hpp"
#include "format.hpp"
#include "global_writer.hpp"

namespace iges {

std::string write_iges_file(
    std::vector<std::string> const& start_lines,
    GlobalSection const& global,
    std::vector<WritableEntity> const& entities) {

    std::string output;

    // ── 1. Start section ────────────────────────────────────────
    int s_count = 0;
    if (start_lines.empty()) {
        // At least one Start line is required (§2.2.4.2)
        output += format_section_line("", SectionKind::Start, 1);
        output += '\n';
        s_count = 1;
    } else {
        for (auto const& line : start_lines) {
            ++s_count;
            output += format_section_line(line, SectionKind::Start, s_count);
            output += '\n';
        }
    }

    // ── 2. Global section ───────────────────────────────────────
    std::string global_str = write_global_section(global);
    int g_count = 0;
    std::size_t pos = 0;
    while (pos < global_str.size()) {
        auto chunk_len = std::min(static_cast<std::size_t>(72), global_str.size() - pos);
        ++g_count;
        output += format_section_line(global_str.substr(pos, chunk_len),
                                       SectionKind::Global, g_count);
        output += '\n';
        pos += chunk_len;
    }
    if (global_str.empty()) {
        ++g_count;
        output += format_section_line("", SectionKind::Global, g_count);
        output += '\n';
    }

    // ── 3. Entities: PD lines then DE lines ─────────────────────
    // First pass: generate PD lines for all entities, track PD pointers
    struct EntityPdInfo {
        int pd_start_seq = 0;
        int pd_line_count = 0;
        std::string pd_lines;
    };
    std::vector<EntityPdInfo> pd_infos;
    pd_infos.reserve(entities.size());
    int pd_seq = 1;

    for (std::size_t i = 0; i < entities.size(); ++i) {
        auto const& ent = entities[i];
        int de_seq = static_cast<int>(i) * 2 + 1;  // DE sequence numbers: 1, 3, 5, ...
        int start_seq = pd_seq;
        auto result = split_pd_lines(ent.pd_string, ent.de.entity_type.value,
                                      de_seq, pd_seq, global.param_delimiter);
        pd_infos.push_back({start_seq, result.line_count, std::move(result.lines)});
    }
    int p_count = pd_seq - 1;

    // Second pass: build DE lines with correct PD pointers and line counts
    std::string de_section;
    int d_count = 0;
    for (std::size_t i = 0; i < entities.size(); ++i) {
        auto de = entities[i].de;  // copy so we can patch
        de.param_data_ptr = pd_infos[i].pd_start_seq;
        de.param_line_count = pd_infos[i].pd_line_count;
        int de_seq = static_cast<int>(i) * 2 + 1;
        de_section += format_directory_entry(de, de_seq);
        d_count += 2;
    }

    // Append DE section
    output += de_section;

    // Append PD section
    for (auto const& info : pd_infos) {
        output += info.pd_lines;
    }

    // ── 4. Terminate section ────────────────────────────────────
    output += format_terminate_line(s_count, g_count, d_count, p_count);
    output += '\n';

    return output;
}

} // namespace iges
