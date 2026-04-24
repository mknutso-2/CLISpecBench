#include "bibtex.hpp"

#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

struct Args {
    std::string bib;
    std::string style;
    std::string cites;
    std::string aux;
    std::string output;
    std::string log;
};

int parse_args(int argc, char** argv, Args& out) {
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        auto next = [&](const char* flag) -> std::string {
            if (i + 1 >= argc) {
                std::fprintf(stderr, "error: %s requires an argument\n", flag);
                std::exit(1);
            }
            return std::string(argv[++i]);
        };
        if (a == "--bib") out.bib = next("--bib");
        else if (a == "--style") out.style = next("--style");
        else if (a == "--cites") out.cites = next("--cites");
        else if (a == "--aux") out.aux = next("--aux");
        else if (a == "--output") out.output = next("--output");
        else if (a == "--log") out.log = next("--log");
        else {
            std::fprintf(stderr, "error: unknown argument %s\n", a.c_str());
            return 1;
        }
    }
    if (out.bib.empty() || out.style.empty() || out.output.empty()
        || (out.cites.empty() && out.aux.empty())) {
        std::fprintf(stderr, "error: --bib, --style, --output, and one of --cites / --aux are required\n");
        return 1;
    }
    return 0;
}

bool read_file(const std::string& path, std::string& contents) {
    std::ifstream in(path, std::ios::binary);
    if (!in) return false;
    std::ostringstream ss;
    ss << in.rdbuf();
    contents = ss.str();
    return true;
}

std::vector<std::string> parse_cites(const std::string& text) {
    std::vector<std::string> out;
    std::string cur;
    auto flush = [&]() {
        std::size_t a = 0, b = cur.size();
        while (a < b && (cur[a] == ' ' || cur[a] == '\t' || cur[a] == '\r')) a++;
        while (b > a && (cur[b - 1] == ' ' || cur[b - 1] == '\t' || cur[b - 1] == '\r')) b--;
        std::string t = cur.substr(a, b - a);
        cur.clear();
        if (t.empty() || t[0] == '#') return;
        out.push_back(std::move(t));
    };
    for (char c : text) {
        if (c == '\n') { flush(); continue; }
        cur.push_back(c);
    }
    flush();
    return out;
}

// Extract cite keys from a LaTeX .aux file's \citation{key1,key2,...} commands.
// Multiple \citation{} commands accumulate; commas separate keys inside one.
// Whitespace around keys is stripped.
std::vector<std::string> parse_aux(const std::string& text) {
    std::vector<std::string> out;
    const std::string marker = "\\citation{";
    std::size_t pos = 0;
    while (pos < text.size()) {
        auto start = text.find(marker, pos);
        if (start == std::string::npos) break;
        std::size_t arg_start = start + marker.size();
        auto end = text.find('}', arg_start);
        if (end == std::string::npos) break;
        std::string arg = text.substr(arg_start, end - arg_start);
        // Split on comma.
        std::string cur;
        auto flush = [&]() {
            std::size_t a = 0, b = cur.size();
            while (a < b && (cur[a] == ' ' || cur[a] == '\t' || cur[a] == '\r' || cur[a] == '\n')) a++;
            while (b > a && (cur[b - 1] == ' ' || cur[b - 1] == '\t' || cur[b - 1] == '\r' || cur[b - 1] == '\n')) b--;
            std::string t = cur.substr(a, b - a);
            cur.clear();
            if (!t.empty()) out.push_back(std::move(t));
        };
        for (char c : arg) {
            if (c == ',') { flush(); continue; }
            cur.push_back(c);
        }
        flush();
        pos = end + 1;
    }
    return out;
}

bool write_file(const std::string& path, const std::string& contents) {
    std::ofstream out(path, std::ios::binary);
    if (!out) return false;
    out.write(contents.data(), static_cast<std::streamsize>(contents.size()));
    return static_cast<bool>(out);
}

} // namespace

int main(int argc, char** argv) try {
    Args args;
    if (int rc = parse_args(argc, argv, args); rc != 0) return rc;

    std::string bib_src, bst_src;
    if (!read_file(args.bib, bib_src)) {
        bibtex::ParseError err{"bib", 0, 0, "cannot read --bib file " + args.bib};
        write_file(args.output, bibtex::emit_error_json(err, {}));
        return 1;
    }
    if (!read_file(args.style, bst_src)) {
        bibtex::ParseError err{"bst", 0, 0, "cannot read --style file " + args.style};
        write_file(args.output, bibtex::emit_error_json(err, {}));
        return 1;
    }
    std::vector<std::string> cites;
    if (!args.cites.empty()) {
        std::string cites_src;
        if (!read_file(args.cites, cites_src)) {
            bibtex::ParseError err{"runtime", 0, 0, "cannot read --cites file " + args.cites};
            write_file(args.output, bibtex::emit_error_json(err, {}));
            return 1;
        }
        cites = parse_cites(cites_src);
    }
    if (!args.aux.empty()) {
        std::string aux_src;
        if (!read_file(args.aux, aux_src)) {
            bibtex::ParseError err{"runtime", 0, 0, "cannot read --aux file " + args.aux};
            write_file(args.output, bibtex::emit_error_json(err, {}));
            return 1;
        }
        auto aux_keys = parse_aux(aux_src);
        for (auto& k : aux_keys) cites.push_back(std::move(k));
    }

    bibtex::Database db;
    {
        bibtex::Parser parser(bib_src, db);
        if (auto err = parser.parse(); err) {
            write_file(args.output, bibtex::emit_error_json(*err, db.warnings));
            return 1;
        }
    }
    bibtex::resolve_crossrefs(db);
    bibtex::parse_name_fields(db);

    bibtex::BstProgram prog;
    if (auto err = bibtex::parse_bst(bst_src, prog); err) {
        write_file(args.output, bibtex::emit_error_json(*err, db.warnings));
        return 1;
    }

    bibtex::BstResult result;
    result.warnings = db.warnings;  // carry parse warnings forward

    if (auto err = bibtex::execute_bst(prog, db, cites, result); err) {
        write_file(args.output, bibtex::emit_error_json(*err, result.warnings));
        return 1;
    }

    if (!write_file(args.output, result.bbl_output)) return 2;
    if (!args.log.empty()) {
        if (!write_file(args.log, bibtex::emit_log_json(result))) return 2;
    }
    return 0;
} catch (const std::exception& e) {
    std::fprintf(stderr, "internal error: %s\n", e.what());
    return 2;
} catch (...) {
    std::fprintf(stderr, "internal error: unknown exception\n");
    return 2;
}
