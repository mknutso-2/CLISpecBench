#include "bibtex.hpp"

#include <cstdio>
#include <sstream>
#include <string>

namespace bibtex {

namespace {

void jstr(std::ostringstream& o, std::string_view s) {
    o << '"';
    for (unsigned char c : s) {
        switch (c) {
            case '"':  o << "\\\""; break;
            case '\\': o << "\\\\"; break;
            case '\b': o << "\\b";  break;
            case '\f': o << "\\f";  break;
            case '\n': o << "\\n";  break;
            case '\r': o << "\\r";  break;
            case '\t': o << "\\t";  break;
            default:
                if (c < 0x20) {
                    char buf[8];
                    std::snprintf(buf, sizeof(buf), "\\u%04x", c);
                    o << buf;
                } else {
                    o << static_cast<char>(c);
                }
        }
    }
    o << '"';
}

void emit_warning(std::ostringstream& o, const Warning& w) {
    o << '{';
    o << "\"kind\":"; jstr(o, w.kind);
    o << ",\"message\":"; jstr(o, w.message);
    if (w.key.has_value()) { o << ",\"key\":"; jstr(o, *w.key); }
    if (w.field.has_value()) { o << ",\"field\":"; jstr(o, *w.field); }
    o << '}';
}

} // namespace

std::string emit_error_json(const ParseError& err, const std::vector<Warning>& warnings) {
    std::ostringstream o;
    o << "{\"error\":{";
    o << "\"source\":"; jstr(o, err.source);
    o << ",\"line\":" << err.line;
    o << ",\"column\":" << err.column;
    o << ",\"message\":"; jstr(o, err.message);
    o << "},\"warnings\":[";
    for (std::size_t i = 0; i < warnings.size(); ++i) {
        if (i) o << ',';
        emit_warning(o, warnings[i]);
    }
    o << "]}";
    return o.str();
}

std::string emit_log_json(const BstResult& result) {
    std::ostringstream o;
    o << '{';
    o << "\"entries_read\":" << result.log.entries_read;
    o << ",\"entries_cited_found\":" << result.log.entries_cited_found;
    o << ",\"entries_cited_missing\":[";
    for (std::size_t i = 0; i < result.log.entries_cited_missing.size(); ++i) {
        if (i) o << ',';
        jstr(o, result.log.entries_cited_missing[i]);
    }
    o << "],\"functions_defined\":" << result.log.functions_defined;
    o << ",\"macros_defined\":[";
    for (std::size_t i = 0; i < result.log.macros_defined.size(); ++i) {
        if (i) o << ',';
        jstr(o, result.log.macros_defined[i]);
    }
    o << "],\"iterations\":" << result.log.iterations;
    o << ",\"sorts\":" << result.log.sorts;
    o << ",\"reverse_iterations\":" << result.log.reverse_iterations;
    o << ",\"execute_calls\":" << result.log.execute_calls;
    o << ",\"warnings\":[";
    for (std::size_t i = 0; i < result.warnings.size(); ++i) {
        if (i) o << ',';
        emit_warning(o, result.warnings[i]);
    }
    o << "]}";
    return o.str();
}

} // namespace bibtex
