#include "ical.hpp"

#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace {

bool read_file(const std::string& path, std::string& content) {
    std::ifstream in(path, std::ios::binary);
    if (!in) return false;
    std::ostringstream ss;
    ss << in.rdbuf();
    content = ss.str();
    return true;
}
bool write_file(const std::string& path, const std::string& content) {
    std::ofstream out(path, std::ios::binary);
    if (!out) return false;
    out.write(content.data(), static_cast<std::streamsize>(content.size()));
    return static_cast<bool>(out);
}

int cmd_parse(const std::string& input, const std::string& output) {
    std::string src;
    if (!read_file(input, src)) {
        std::fprintf(stderr, "error: cannot read %s\n", input.c_str());
        return 1;
    }
    ical::Calendar cal;
    auto err = ical::parse_ics(src, cal);
    if (err) {
        auto json = ical::emit_error_json(*err, cal.warnings);
        write_file(output, json);
        return 1;
    }
    write_file(output, ical::emit_parse_json(cal));
    return 0;
}

int cmd_expand(const std::string& input, const std::string& from, const std::string& to,
               const std::string& output) {
    std::string src;
    if (!read_file(input, src)) {
        std::fprintf(stderr, "error: cannot read %s\n", input.c_str());
        return 1;
    }
    ical::Calendar cal;
    auto err = ical::parse_ics(src, cal);
    if (err) { write_file(output, ical::emit_error_json(*err, cal.warnings)); return 1; }

    auto parse_bound = [](const std::string& s) -> std::optional<ical::DateOrDateTime> {
        if (auto dt = ical::parse_iso_datetime(s); dt) {
            ical::DateOrDateTime d; d.datetime = *dt; return d;
        }
        if (s.size() == 10 && s[4] == '-' && s[7] == '-') {
            int y = 0, m = 0, d = 0;
            if (std::sscanf(s.c_str(), "%4d-%2d-%2d", &y, &m, &d) == 3) {
                ical::DateOrDateTime r; r.date = ical::Date{y, m, d}; return r;
            }
        }
        return std::nullopt;
    };
    auto fd = parse_bound(from);
    auto td = parse_bound(to);
    if (!fd || !td) {
        ical::ParseError pe{0, 0, "invalid --from or --to date-time"};
        write_file(output, ical::emit_error_json(pe, cal.warnings));
        return 1;
    }
    std::vector<ical::Warning> expand_warnings;
    auto occs = ical::expand_events(cal, *fd, *td, expand_warnings);
    std::vector<ical::Warning> combined = cal.warnings;
    for (const auto& w : expand_warnings) combined.push_back(w);
    write_file(output, ical::emit_expand_json(occs, combined));
    return 0;
}

} // namespace

int main(int argc, char** argv) try {
    if (argc < 2) {
        std::fprintf(stderr, "usage: ical parse --input FILE --output FILE\n"
                             "       ical expand --input FILE --from ISO --to ISO --output FILE\n");
        return 1;
    }
    std::string cmd = argv[1];
    std::string input, output, from, to;
    for (int i = 2; i < argc; ++i) {
        std::string a = argv[i];
        auto next = [&](const char* flag) -> std::string {
            if (i + 1 >= argc) { std::fprintf(stderr, "error: %s requires arg\n", flag); std::exit(1); }
            return std::string(argv[++i]);
        };
        if (a == "--input") input = next("--input");
        else if (a == "--output") output = next("--output");
        else if (a == "--from") from = next("--from");
        else if (a == "--to") to = next("--to");
        else { std::fprintf(stderr, "error: unknown arg %s\n", a.c_str()); return 1; }
    }
    if (cmd == "parse") {
        if (input.empty() || output.empty()) { std::fprintf(stderr, "error: --input and --output required\n"); return 1; }
        return cmd_parse(input, output);
    }
    if (cmd == "expand") {
        if (input.empty() || output.empty() || from.empty() || to.empty()) {
            std::fprintf(stderr, "error: --input, --output, --from, --to required\n");
            return 1;
        }
        return cmd_expand(input, from, to, output);
    }
    std::fprintf(stderr, "error: unknown subcommand %s\n", cmd.c_str());
    return 1;
} catch (const std::exception& e) {
    std::fprintf(stderr, "internal error: %s\n", e.what());
    return 2;
} catch (...) {
    std::fprintf(stderr, "internal error: unknown exception\n");
    return 2;
}
