// iges — reference implementation CLI.
//
// Five subcommands (see Evals/IGES/prompt/technical-requirements-prompt.md §1):
//   parse     <in.iges> → <out.json>
//   write     <in.json> → <out.iges>
//   query     <in.iges> --de <n> → <entity.json>
//   eval      <in.iges> --de <n> --t <f> [--s <f>] → <point.json>
//   roundtrip <in.iges> → <out.iges>
//
// Exit codes:
//   0 — success
//   1 — invalid input (malformed file, bad JSON, DE out of range, etc.)
//   2 — internal error (unexpected exception, I/O failure, etc.)

#include "types.hpp"
#include "parser/file_reader.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"
#include "writer/file_writer.hpp"
#include "model/directory_entry.hpp"
#include "model/global_section.hpp"
#include "model/validate.hpp"

#include "json/core_json.hpp"
#include "json/model_json.hpp"
#include "json/dispatch.hpp"

#include <nlohmann/json.hpp>

#include <cstdio>
#include <cstdlib>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <sstream>
#include <cctype>
#include <string>
#include <string_view>
#include <vector>

using nlohmann::json;

namespace {

// ── Arg parsing ──────────────────────────────────────────────

struct Args {
    std::string subcommand;
    std::string input;
    std::string output;
    std::optional<int> de;
    std::optional<iges::Real> t;
    std::optional<iges::Real> s;
};

std::optional<std::string> pop_value(int& i, int argc, char** argv) {
    if (i + 1 >= argc) return std::nullopt;
    return std::string{argv[++i]};
}

std::optional<Args> parse_args(int argc, char** argv) {
    if (argc < 2) return std::nullopt;
    Args a;
    a.subcommand = argv[1];
    for (int i = 2; i < argc; ++i) {
        std::string_view arg = argv[i];
        auto value = [&](std::string& dst) -> bool {
            auto v = pop_value(i, argc, argv);
            if (!v) return false;
            dst = *v;
            return true;
        };
        if (arg == "--input") { if (!value(a.input)) return std::nullopt; }
        else if (arg == "--output") { if (!value(a.output)) return std::nullopt; }
        else if (arg == "--de") {
            std::string tmp; if (!value(tmp)) return std::nullopt;
            try { a.de = std::stoi(tmp); } catch (...) { return std::nullopt; }
        }
        else if (arg == "--t") {
            std::string tmp; if (!value(tmp)) return std::nullopt;
            try { a.t = std::stod(tmp); } catch (...) { return std::nullopt; }
        }
        else if (arg == "--s") {
            std::string tmp; if (!value(tmp)) return std::nullopt;
            try { a.s = std::stod(tmp); } catch (...) { return std::nullopt; }
        }
        else return std::nullopt;
    }
    return a;
}

// ── JSON output helpers ──────────────────────────────────────

json diag_to_json(iges::Diagnostic const& d) {
    const char* sev =
        d.severity == iges::Diagnostic::Severity::Error   ? "error" :
        d.severity == iges::Diagnostic::Severity::Warning ? "warning" :
                                                            "info";
    const char* section =
        d.section == iges::SectionKind::Flag      ? "flag" :
        d.section == iges::SectionKind::Start     ? "start" :
        d.section == iges::SectionKind::Global    ? "global" :
        d.section == iges::SectionKind::Directory ? "directory" :
        d.section == iges::SectionKind::Parameter ? "parameter" :
        d.section == iges::SectionKind::Terminate ? "terminate" :
                                                    "unknown";
    return json{
        {"severity", sev},
        {"line", d.line},
        {"section", section},
        {"message", d.message},
        {"spec_ref", d.spec_ref},
    };
}

json make_error(std::string const& message, std::string const& spec_ref,
                int line = 0, std::string const& section = "unknown",
                json const& diagnostics = json::array()) {
    return json{
        {"ok", false},
        {"error", message},
        {"spec_ref", spec_ref},
        {"line", line},
        {"section", section},
        {"diagnostics", diagnostics},
    };
}

json error_from_diagnostics(iges::DiagList const& diags) {
    if (diags.empty()) {
        return make_error("Unknown parse error", "§3");
    }
    auto const& primary = diags.front();
    json all = json::array();
    for (auto const& d : diags) all.push_back(diag_to_json(d));
    const char* section =
        primary.section == iges::SectionKind::Flag      ? "flag" :
        primary.section == iges::SectionKind::Start     ? "start" :
        primary.section == iges::SectionKind::Global    ? "global" :
        primary.section == iges::SectionKind::Directory ? "directory" :
        primary.section == iges::SectionKind::Parameter ? "parameter" :
        primary.section == iges::SectionKind::Terminate ? "terminate" :
                                                          "unknown";
    return make_error(primary.message, primary.spec_ref, primary.line, section, all);
}

// ── I/O helpers ──────────────────────────────────────────────

std::string read_file(std::string const& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) throw std::runtime_error("Cannot open input file: " + path);
    std::ostringstream buf;
    buf << in.rdbuf();
    return buf.str();
}

void write_file(std::string const& path, std::string const& content) {
    std::ofstream out(path, std::ios::binary);
    if (!out) throw std::runtime_error("Cannot open output file: " + path);
    out << content;
    if (!out) throw std::runtime_error("Write failed: " + path);
}

void write_json(std::string const& path, json const& j) {
    write_file(path, j.dump(2) + "\n");
}

std::string rewrite_pd_delimiters(std::string_view pd_string,
                                  char param_delimiter,
                                  char record_delimiter) {
    if (param_delimiter == ',' && record_delimiter == ';') {
        return std::string(pd_string);
    }

    std::string out;
    out.reserve(pd_string.size());
    for (std::size_t i = 0; i < pd_string.size();) {
        if (std::isdigit(static_cast<unsigned char>(pd_string[i])) != 0) {
            std::size_t scan = i;
            while (scan < pd_string.size() &&
                   std::isdigit(static_cast<unsigned char>(pd_string[scan])) != 0) {
                ++scan;
            }
            if (scan < pd_string.size() &&
                (pd_string[scan] == 'H' || pd_string[scan] == 'h')) {
                auto count = std::stoul(std::string(pd_string.substr(i, scan - i)));
                auto end = std::min(pd_string.size(), scan + 1 + count);
                out.append(pd_string.substr(i, end - i));
                i = end;
                continue;
            }
        }

        char ch = pd_string[i];
        if (ch == ',') out += param_delimiter;
        else if (ch == ';') out += record_delimiter;
        else out += ch;
        ++i;
    }
    return out;
}

std::expected<iges::IgesFile, json> read_and_validate_iges(
    std::string const& path
) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        return std::unexpected(make_error("Cannot open input file: " + path, "§1"));
    }
    auto parsed = iges::read_iges_file(in);
    if (!parsed) {
        return std::unexpected(error_from_diagnostics(parsed.error()));
    }
    auto diags = iges::validate(*parsed);
    if (!diags.empty()) {
        return std::unexpected(error_from_diagnostics(diags));
    }
    return *parsed;
}

// ── Parse → canonical JSON ───────────────────────────────────

// Build the canonical IGES-JSON document described in §2 from a parsed
// iges::IgesFile (Start + Global + vector<RawEntity>).
std::expected<json, json> build_canonical_json(iges::IgesFile const& file) {
    json j;
    j["start_lines"] = file.start_lines;
    j["global"] = file.global;

    json entities = json::array();
    int idx = 1;
    for (auto const& raw : file.entities) {
        int type = raw.de.entity_type.value;
        int form = raw.de.form.value;
        iges::ParamTokenizer tok(raw.pd_string,
                                 file.global.param_delimiter,
                                 file.global.record_delimiter);
        auto parsed = iges::parse_entity_dispatch(type, form, tok);
        if (!parsed) {
            auto const& d = parsed.error();
            return std::unexpected(make_error(
                d.message, d.spec_ref, d.line,
                d.section == iges::SectionKind::Parameter ? "parameter" : "directory",
                json::array({diag_to_json(d)})));
        }

        int de_index = 2 * (idx - 1) + 1;  // 1, 3, 5, ...

        json entity = {
            {"de_index", de_index},
            {"directory_entry", raw.de},
            {"entity", {
                {"type", type},
                {"form", form},
                {"data", *parsed},
            }},
        };
        entities.push_back(std::move(entity));
        ++idx;
    }
    j["entities"] = std::move(entities);
    return j;
}

// ── Write — canonical JSON → IGES file ──────────────────────

std::expected<std::string, json> canonical_json_to_iges(json const& j) {
    try {
        std::vector<std::string> start_lines = j.at("start_lines").get<std::vector<std::string>>();
        iges::GlobalSection global = j.at("global").get<iges::GlobalSection>();

        std::vector<iges::WritableEntity> entities;
        auto const& arr = j.at("entities");
        if (!arr.is_array()) {
            return std::unexpected(make_error(
                "'entities' must be an array", "§2.1"));
        }
        for (auto const& e : arr) {
            iges::WritableEntity w;
            w.de = e.at("directory_entry").get<iges::DirectoryEntry>();
            int type = e.at("entity").at("type").get<int>();
            int form = e.at("entity").at("form").get<int>();
            // DE must be self-consistent with entity.type / entity.form
            w.de.entity_type = iges::EntityType{type};
            w.de.form = iges::FormNumber{form};

            auto const& data = e.at("entity").at("data");
            auto pd = iges::write_entity_dispatch(type, form, data);
            if (!pd) {
                auto const& d = pd.error();
                return std::unexpected(make_error(
                    d.message, d.spec_ref, d.line, "parameter",
                    json::array({diag_to_json(d)})));
            }
            w.pd_string = rewrite_pd_delimiters(
                *pd, global.param_delimiter, global.record_delimiter);
            entities.push_back(std::move(w));
        }

        // Structural validation on the write path (TR §1.2). Uses the
        // `validate_write_input` variant which shares the entity-type
        // sign and DE cross-reference checks (view, xform_matrix,
        // label_display) with the parse path, plus the Global field
        // positivity checks, but skips param_line_count and
        // pd_string.empty() — those are re-derived / built by the
        // writer and would trigger spurious rejections here. Symmetric
        // enforcement ensures `iges write` cannot produce an .iges
        // file that `iges parse` would immediately reject.
        //
        // WritableEntity and RawEntity are structurally identical
        // ({DirectoryEntry, std::string}); copy fields into a
        // validation stub to call the shared validator.
        iges::IgesFile validation_stub;
        validation_stub.global = global;
        validation_stub.entities.reserve(entities.size());
        for (auto const& w : entities) {
            iges::RawEntity r;
            r.de = w.de;
            r.pd_string = w.pd_string;
            validation_stub.entities.push_back(std::move(r));
        }
        auto diags = iges::validate_write_input(validation_stub);
        if (!diags.empty()) {
            return std::unexpected(error_from_diagnostics(diags));
        }

        return iges::write_iges_file(start_lines, global, entities);
    } catch (nlohmann::json::exception const& ex) {
        return std::unexpected(make_error(
            std::string{"JSON shape violation: "} + ex.what(), "§2"));
    }
}

// ── Subcommands ──────────────────────────────────────────────

int cmd_parse(Args const& a) {
    if (a.input.empty() || a.output.empty()) {
        auto err = make_error("parse requires --input and --output", "§1");
        write_json(a.output.empty() ? "/dev/stderr" : a.output, err);
        std::cerr << err.dump() << std::endl;
        return 1;
    }
    auto parsed = read_and_validate_iges(a.input);
    if (!parsed) {
        write_json(a.output, parsed.error());
        return 1;
    }
    auto canonical = build_canonical_json(*parsed);
    if (!canonical) {
        write_json(a.output, canonical.error());
        return 1;
    }
    write_json(a.output, *canonical);
    return 0;
}

int cmd_write(Args const& a) {
    if (a.input.empty() || a.output.empty()) {
        std::cerr << make_error("write requires --input and --output", "§1").dump() << std::endl;
        return 1;
    }
    std::string raw;
    try { raw = read_file(a.input); } catch (std::exception const& ex) {
        std::cerr << make_error(ex.what(), "§1").dump() << std::endl;
        return 1;
    }
    json j;
    try { j = json::parse(raw); } catch (nlohmann::json::exception const& ex) {
        std::cerr << make_error(std::string{"JSON parse error: "} + ex.what(), "§2").dump() << std::endl;
        return 1;
    }
    auto out = canonical_json_to_iges(j);
    if (!out) {
        std::cerr << out.error().dump() << std::endl;
        return 1;
    }
    write_file(a.output, *out);
    return 0;
}

int cmd_roundtrip(Args const& a) {
    if (a.input.empty() || a.output.empty()) {
        std::cerr << make_error("roundtrip requires --input and --output", "§1").dump() << std::endl;
        return 1;
    }
    auto parsed = read_and_validate_iges(a.input);
    if (!parsed) {
        std::cerr << parsed.error().dump() << std::endl;
        return 1;
    }
    // Roundtrip at the raw-entity level — no re-parsing of PD data.
    std::vector<iges::WritableEntity> ents;
    for (auto const& r : parsed->entities) {
        ents.push_back({r.de, r.pd_string});
    }
    auto out = iges::write_iges_file(parsed->start_lines, parsed->global, ents);
    write_file(a.output, out);
    return 0;
}

// Map DE index (1-based, odd) to position in entities[] (0-based).
std::optional<std::size_t> de_to_position(int de_index, std::size_t count) {
    if (de_index < 1 || (de_index % 2) == 0) return std::nullopt;
    std::size_t pos = static_cast<std::size_t>((de_index - 1) / 2);
    if (pos >= count) return std::nullopt;
    return pos;
}

int cmd_query(Args const& a) {
    if (a.input.empty() || a.output.empty() || !a.de.has_value()) {
        std::cerr << make_error("query requires --input, --output, --de", "§1").dump() << std::endl;
        return 1;
    }
    auto parsed = read_and_validate_iges(a.input);
    if (!parsed) {
        write_json(a.output, parsed.error());
        return 1;
    }
    auto pos = de_to_position(*a.de, parsed->entities.size());
    if (!pos) {
        auto err = make_error(
            std::string{"DE index out of range or not odd: "} + std::to_string(*a.de),
            "§1");
        write_json(a.output, err);
        return 1;
    }
    auto const& raw = parsed->entities[*pos];
    int type = raw.de.entity_type.value;
    int form = raw.de.form.value;
    iges::ParamTokenizer tok(raw.pd_string,
                             parsed->global.param_delimiter,
                             parsed->global.record_delimiter);
    auto data = iges::parse_entity_dispatch(type, form, tok);
    if (!data) {
        auto const& d = data.error();
        auto err = make_error(d.message, d.spec_ref, d.line, "parameter",
                              json::array({diag_to_json(d)}));
        write_json(a.output, err);
        return 1;
    }
    json out = {
        {"de_index", *a.de},
        {"directory_entry", raw.de},
        {"entity", {
            {"type", type},
            {"form", form},
            {"data", *data},
        }},
    };
    write_json(a.output, out);
    return 0;
}

int cmd_eval(Args const& a) {
    if (a.input.empty() || a.output.empty() || !a.de.has_value() || !a.t.has_value()) {
        std::cerr << make_error("eval requires --input, --output, --de, --t", "§1").dump() << std::endl;
        return 1;
    }
    auto parsed = read_and_validate_iges(a.input);
    if (!parsed) {
        write_json(a.output, parsed.error());
        return 1;
    }
    auto pos = de_to_position(*a.de, parsed->entities.size());
    if (!pos) {
        write_json(a.output, make_error(
            std::string{"DE index out of range or not odd: "} + std::to_string(*a.de), "§1"));
        return 1;
    }
    auto const& raw = parsed->entities[*pos];
    int type = raw.de.entity_type.value;
    int form = raw.de.form.value;
    iges::ParamTokenizer tok(raw.pd_string,
                             parsed->global.param_delimiter,
                             parsed->global.record_delimiter);
    auto data = iges::parse_entity_dispatch(type, form, tok);
    if (!data) {
        auto const& d = data.error();
        write_json(a.output, make_error(d.message, d.spec_ref, d.line, "parameter",
                                        json::array({diag_to_json(d)})));
        return 1;
    }
    // Resolver used by pointer-bearing evaluators (Composite Curve,
    // Offset Curve, Ruled Surface, etc.) to look up constituent
    // entities by DE index. Parses on demand; a file with one
    // malformed non-target entity still succeeds for eval on the
    // target if the target's constituents are all valid.
    iges::EntityResolver resolver =
        [&parsed](int de) -> std::expected<iges::ResolvedEntity, iges::Diagnostic> {
        auto pos = de_to_position(de, parsed->entities.size());
        if (!pos) return std::unexpected(iges::Diagnostic{
            iges::Diagnostic::Severity::Error, 0, iges::SectionKind::Parameter,
            std::string{"DE index out of range or not odd: "} + std::to_string(de),
            "§1"});
        auto const& ref = parsed->entities[*pos];
        iges::ParamTokenizer rt(ref.pd_string,
                                 parsed->global.param_delimiter,
                                 parsed->global.record_delimiter);
        auto rd = iges::parse_entity_dispatch(
            ref.de.entity_type.value, ref.de.form.value, rt);
        if (!rd) return std::unexpected(rd.error());
        return iges::ResolvedEntity{
            ref.de.entity_type.value, ref.de.form.value,
            ref.de.xform_matrix.value, *rd};
    };
    auto result = iges::evaluate_entity_dispatch(
        type, form, raw.de.xform_matrix.value, *data, *a.t, a.s, resolver);
    if (!result) {
        auto const& d = result.error();
        write_json(a.output, make_error(d.message, d.spec_ref, d.line, "parameter"));
        return 1;
    }
    json out = {
        {"ok", true},
        {"point", json::array({result->point.x, result->point.y, result->point.z})},
        {"tangent", result->tangent.has_value()
            ? json(json::array({result->tangent->x, result->tangent->y, result->tangent->z}))
            : json(nullptr)},
        {"normal", result->normal.has_value()
            ? json(json::array({result->normal->x, result->normal->y, result->normal->z}))
            : json(nullptr)},
        {"error", nullptr},
    };
    write_json(a.output, out);
    return 0;
}

}  // namespace

int main(int argc, char** argv) {
    auto a = parse_args(argc, argv);
    if (!a) {
        std::cerr << "Usage: iges <parse|write|query|eval|roundtrip> [options]"
                  << std::endl;
        return 1;
    }

    try {
        if (a->subcommand == "parse")     return cmd_parse(*a);
        if (a->subcommand == "write")     return cmd_write(*a);
        if (a->subcommand == "query")     return cmd_query(*a);
        if (a->subcommand == "eval")      return cmd_eval(*a);
        if (a->subcommand == "roundtrip") return cmd_roundtrip(*a);

        std::cerr << make_error(
            std::string{"Unknown subcommand: "} + a->subcommand, "§1").dump()
                  << std::endl;
        return 1;
    } catch (std::exception const& ex) {
        std::cerr << make_error(
            std::string{"Internal error: "} + ex.what(), "§0").dump()
                  << std::endl;
        return 2;
    }
}
