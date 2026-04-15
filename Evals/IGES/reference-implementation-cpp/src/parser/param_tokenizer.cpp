// iges::ParamTokenizer — Full implementation.
// Implements §2.2.2 (data types) and §2.2.3 (free-format rules).

#include "param_tokenizer.hpp"
#include <algorithm>
#include <cctype>
#include <charconv>
#include <cmath>
#include <cstring>

namespace iges {

// ── Free-standing parse helpers ─────────────────────────────────

static Diagnostic make_diag(std::string msg, std::string spec_ref) {
    return Diagnostic{Diagnostic::Severity::Error, 0,
                      SectionKind::Parameter, std::move(msg), std::move(spec_ref)};
}

// §2.2.3.1 — Prohibited delimiter characters
bool is_valid_delimiter(char c) {
    // Control characters (0x00-0x1F, 0x7F)
    if (c >= '\x00' && c <= '\x1F') return false;
    if (c == '\x7F') return false;
    // Space
    if (c == ' ') return false;
    // Digits 0-9
    if (c >= '0' && c <= '9') return false;
    // Sign and decimal point
    if (c == '+' || c == '-' || c == '.') return false;
    // Letters used in numeric notation
    if (c == 'D' || c == 'E' || c == 'H') return false;
    return true;
}

// §2.2.2.1 — Integer parsing
std::expected<int, Diagnostic> parse_integer(std::string_view s) {
    // Trim leading and trailing spaces
    auto start = s.find_first_not_of(' ');
    if (start == std::string_view::npos) {
        // All blanks = defaulted (caller decides)
        return std::unexpected(make_diag("blank field", "§2.2.2.1"));
    }
    auto end = s.find_last_not_of(' ');
    auto trimmed = s.substr(start, end - start + 1);

    // Handle optional leading sign
    int sign = 1;
    std::size_t i = 0;
    if (trimmed[0] == '+') { sign = 1; i = 1; }
    else if (trimmed[0] == '-') { sign = -1; i = 1; }

    // Skip leading zeros
    while (i < trimmed.size() && trimmed[i] == '0') ++i;

    if (i == trimmed.size()) return 0; // all zeros

    // Parse remaining digits
    long long val = 0;
    for (; i < trimmed.size(); ++i) {
        if (trimmed[i] < '0' || trimmed[i] > '9') {
            return std::unexpected(make_diag(
                std::string("invalid integer character: ") + trimmed[i], "§2.2.2.1"));
        }
        val = val * 10 + (trimmed[i] - '0');
    }
    return static_cast<int>(sign * val);
}

// §2.2.2.2 — Real parsing (supports E and D exponents)
std::expected<Real, Diagnostic> parse_real(std::string_view s) {
    auto start = s.find_first_not_of(' ');
    if (start == std::string_view::npos) {
        return std::unexpected(make_diag("blank field", "§2.2.2.2"));
    }
    auto end = s.find_last_not_of(' ');
    auto trimmed = s.substr(start, end - start + 1);

    // Replace 'D' exponent with 'E' for standard parsing
    std::string buf(trimmed);
    for (auto& c : buf) {
        if (c == 'D' || c == 'd') c = 'E';
    }

    // Parse using strtod for robust handling of all forms
    char* endptr = nullptr;
    double val = std::strtod(buf.c_str(), &endptr);
    if (endptr == buf.c_str() || (*endptr != '\0' && *endptr != ' ')) {
        return std::unexpected(make_diag(
            "invalid real: " + std::string(trimmed), "§2.2.2.2"));
    }
    return val;
}

// §2.2.2.3 — Hollerith string parsing (nH...)
std::expected<std::string, Diagnostic> parse_hollerith_string(std::string_view s) {
    // Find 'H' or 'h'
    auto h_pos = s.find('H');
    if (h_pos == std::string_view::npos) h_pos = s.find('h');
    if (h_pos == std::string_view::npos || h_pos == 0) {
        return std::unexpected(make_diag("missing Hollerith prefix", "§2.2.2.3"));
    }

    // Parse character count
    auto count_str = s.substr(0, h_pos);
    auto count_result = parse_integer(count_str);
    if (!count_result.has_value()) {
        return std::unexpected(make_diag("invalid Hollerith count", "§2.2.2.3"));
    }
    int count = count_result.value();
    if (count < 0) {
        return std::unexpected(make_diag("negative Hollerith count", "§2.2.2.3"));
    }
    if (count == 0) {
        return std::unexpected(make_diag("zero Hollerith count", "§2.2.2.3"));
    }

    // Extract the string content
    auto content_start = h_pos + 1;
    if (content_start + static_cast<std::size_t>(count) > s.size()) {
        return std::unexpected(make_diag("Hollerith string overflows", "§2.2.2.3"));
    }

    auto content = s.substr(content_start, count);

    // Check for control characters (§2.2.2.3 valid char constraint)
    for (char c : content) {
        if ((c >= '\x00' && c <= '\x1F') || c == '\x7F') {
            return std::unexpected(make_diag("control char in Hollerith", "§2.2.2.3"));
        }
    }

    return std::string(content);
}

// §2.2.4.3.18 — Timestamp parsing
std::expected<Timestamp, Diagnostic> parse_timestamp(std::string_view s) {
    Timestamp ts;
    // Format: YYYYMMDD.HHNNSS (15 chars) or YYMMDD.HHNNSS (13 chars)
    auto dot_pos = s.find('.');
    if (dot_pos == std::string_view::npos) {
        return std::unexpected(make_diag("missing dot in timestamp", "§2.2.4.3.18"));
    }

    auto date_part = s.substr(0, dot_pos);
    auto time_part = s.substr(dot_pos + 1);

    if (time_part.size() < 6) {
        return std::unexpected(make_diag("time part too short", "§2.2.4.3.18"));
    }

    // Parse time
    auto parse_2digit = [](std::string_view sv) -> int {
        return (sv[0] - '0') * 10 + (sv[1] - '0');
    };
    ts.hour   = parse_2digit(time_part.substr(0, 2));
    ts.minute = parse_2digit(time_part.substr(2, 2));
    ts.second = parse_2digit(time_part.substr(4, 2));

    // Parse date
    if (date_part.size() == 8) {
        // YYYYMMDD
        ts.year  = (date_part[0] - '0') * 1000 + (date_part[1] - '0') * 100 +
                   (date_part[2] - '0') * 10 + (date_part[3] - '0');
        ts.month = parse_2digit(date_part.substr(4, 2));
        ts.day   = parse_2digit(date_part.substr(6, 2));
    } else if (date_part.size() == 6) {
        // YYMMDD — "YY is assumed to be prefixed by '19'"
        ts.year  = 1900 + parse_2digit(date_part.substr(0, 2));
        ts.month = parse_2digit(date_part.substr(2, 2));
        ts.day   = parse_2digit(date_part.substr(4, 2));
    } else {
        return std::unexpected(make_diag("invalid date length", "§2.2.4.3.18"));
    }

    return ts;
}

// ── ParamTokenizer ──────────────────────────────────────────────

ParamTokenizer::ParamTokenizer(std::string_view data,
                               char param_delim,
                               char record_delim)
    : data_(data), pd_(param_delim), rd_(record_delim) {}

void ParamTokenizer::skip_blanks() {
    while (pos_ < data_.size() && data_[pos_] == ' ') ++pos_;
}

bool ParamTokenizer::has_next() const {
    if (record_ended_) return false;
    return pos_ < data_.size();
}

bool ParamTokenizer::at_record_end() const {
    return record_ended_;
}

int ParamTokenizer::position() const {
    return static_cast<int>(pos_);
}

std::expected<FieldValue, Diagnostic> ParamTokenizer::next_field() {
    if (record_ended_) {
        return std::unexpected(make_diag("past record end", "§2.2.3"));
    }

    skip_blanks();

    if (pos_ >= data_.size()) {
        record_ended_ = true;
        return std::unexpected(make_diag("past end of data", "§2.2.3"));
    }

    char c = data_[pos_];

    // Check for immediate delimiter → defaulted field
    if (c == pd_) {
        ++pos_;
        return FieldValue{DefaultedField{}};
    }
    if (c == rd_) {
        ++pos_;
        record_ended_ = true;
        return FieldValue{DefaultedField{}};
    }

    // Check for Hollerith string: digit(s) followed by H
    // But distinguish from plain integers by looking for 'H' after digits
    {
        // Look ahead to see if this is nH...
        std::size_t scan = pos_;
        while (scan < data_.size() && data_[scan] >= '0' && data_[scan] <= '9') ++scan;
        if (scan > pos_ && scan < data_.size() && (data_[scan] == 'H' || data_[scan] == 'h')) {
            // It's a Hollerith string
            auto result = parse_hollerith();
            if (!result.has_value()) return std::unexpected(result.error());
            // Consume trailing delimiter
            if (pos_ < data_.size()) {
                if (data_[pos_] == pd_) ++pos_;
                else if (data_[pos_] == rd_) { ++pos_; record_ended_ = true; }
            }
            return FieldValue{result.value()};
        }
    }

    // Otherwise it's a numeric token (integer, real, or logical)
    return parse_numeric();
}

std::expected<std::string, Diagnostic> ParamTokenizer::parse_hollerith() {
    // pos_ points to first digit of count
    std::size_t count_start = pos_;
    while (pos_ < data_.size() && data_[pos_] >= '0' && data_[pos_] <= '9') ++pos_;

    if (pos_ >= data_.size() || (data_[pos_] != 'H' && data_[pos_] != 'h')) {
        return std::unexpected(make_diag("expected H", "§2.2.2.3"));
    }

    auto count_str = data_.substr(count_start, pos_ - count_start);
    auto count_result = parse_integer(count_str);
    if (!count_result.has_value()) {
        return std::unexpected(make_diag("invalid Hollerith count", "§2.2.2.3"));
    }
    int count = count_result.value();
    if (count <= 0) {
        return std::unexpected(make_diag("non-positive Hollerith count", "§2.2.2.3"));
    }

    ++pos_; // skip 'H'

    if (pos_ + static_cast<std::size_t>(count) > data_.size()) {
        return std::unexpected(make_diag("Hollerith overflows data", "§2.2.2.3"));
    }

    auto content = data_.substr(pos_, count);
    pos_ += count;

    // Check for control characters
    for (char ch : content) {
        if ((ch >= '\x00' && ch <= '\x1F') || ch == '\x7F') {
            return std::unexpected(make_diag("control char in Hollerith", "§2.2.2.3"));
        }
    }

    return std::string(content);
}

std::expected<FieldValue, Diagnostic> ParamTokenizer::parse_numeric() {
    // Extract token up to next delimiter
    std::size_t token_start = pos_;
    while (pos_ < data_.size() && data_[pos_] != pd_ && data_[pos_] != rd_) ++pos_;

    auto token = data_.substr(token_start, pos_ - token_start);

    // Consume delimiter
    if (pos_ < data_.size()) {
        if (data_[pos_] == pd_) ++pos_;
        else if (data_[pos_] == rd_) { ++pos_; record_ended_ = true; }
    }

    // Trim trailing spaces from token
    auto last_nonspace = token.find_last_not_of(' ');
    if (last_nonspace != std::string_view::npos) {
        token = token.substr(0, last_nonspace + 1);
    }

    // Trim leading spaces
    auto first_nonspace = token.find_first_not_of(' ');
    if (first_nonspace == std::string_view::npos) {
        // All spaces → defaulted
        return FieldValue{DefaultedField{}};
    }
    token = token.substr(first_nonspace);

    // Check if it contains a decimal point or exponent → real
    bool has_dot = false;
    bool has_exp = false;
    for (char ch : token) {
        if (ch == '.') has_dot = true;
        if (ch == 'E' || ch == 'e' || ch == 'D' || ch == 'd') has_exp = true;
    }

    if (has_dot || has_exp) {
        auto r = parse_real(token);
        if (!r.has_value()) return std::unexpected(r.error());
        return FieldValue{r.value()};
    }

    // Otherwise integer
    auto r = parse_integer(token);
    if (!r.has_value()) return std::unexpected(r.error());
    return FieldValue{r.value()};
}

// ── Typed accessors ─────────────────────────────────────────────

std::expected<int, Diagnostic> ParamTokenizer::next_integer() {
    auto field = next_field();
    if (!field.has_value()) return std::unexpected(field.error());

    if (std::holds_alternative<int>(field.value())) {
        return std::get<int>(field.value());
    }
    if (std::holds_alternative<DefaultedField>(field.value())) {
        return std::unexpected(make_diag("expected integer, got default", "§2.2.2.1"));
    }
    return std::unexpected(make_diag("expected integer", "§2.2.2.1"));
}

std::expected<Real, Diagnostic> ParamTokenizer::next_real() {
    auto field = next_field();
    if (!field.has_value()) return std::unexpected(field.error());

    if (std::holds_alternative<Real>(field.value())) {
        return std::get<Real>(field.value());
    }
    if (std::holds_alternative<int>(field.value())) {
        // Integer is promotable to real
        return static_cast<Real>(std::get<int>(field.value()));
    }
    if (std::holds_alternative<DefaultedField>(field.value())) {
        return std::unexpected(make_diag("expected real, got default", "§2.2.2.2"));
    }
    return std::unexpected(make_diag("expected real", "§2.2.2.2"));
}

std::expected<std::string, Diagnostic> ParamTokenizer::next_string() {
    auto field = next_field();
    if (!field.has_value()) return std::unexpected(field.error());

    if (std::holds_alternative<std::string>(field.value())) {
        return std::get<std::string>(field.value());
    }
    if (std::holds_alternative<DefaultedField>(field.value())) {
        return std::unexpected(make_diag("expected string, got default", "§2.2.2.3"));
    }
    return std::unexpected(make_diag("expected string", "§2.2.2.3"));
}

std::expected<DEIndex, Diagnostic> ParamTokenizer::next_pointer() {
    auto field = next_field();
    if (!field.has_value()) return std::unexpected(field.error());

    if (std::holds_alternative<int>(field.value())) {
        return DEIndex{std::get<int>(field.value())};
    }
    if (std::holds_alternative<DefaultedField>(field.value())) {
        return DEIndex{0}; // null pointer default
    }
    return std::unexpected(make_diag("expected pointer", "§2.2.2.4"));
}

std::expected<bool, Diagnostic> ParamTokenizer::next_logical() {
    auto field = next_field();
    if (!field.has_value()) return std::unexpected(field.error());

    if (std::holds_alternative<int>(field.value())) {
        int v = std::get<int>(field.value());
        if (v == 0) return false;
        if (v == 1) return true;
        return std::unexpected(make_diag("logical must be 0 or 1", "§2.2.2.6"));
    }
    if (std::holds_alternative<DefaultedField>(field.value())) {
        return std::unexpected(make_diag("expected logical, got default", "§2.2.2.6"));
    }
    return std::unexpected(make_diag("expected logical", "§2.2.2.6"));
}

// ── Default-providing accessors ─────────────────────────────────

std::expected<int, Diagnostic> ParamTokenizer::next_integer_or(int def) {
    if (record_ended_) return def;

    auto field = next_field();
    if (!field.has_value()) return def;

    if (std::holds_alternative<int>(field.value())) {
        return std::get<int>(field.value());
    }
    if (std::holds_alternative<DefaultedField>(field.value())) {
        return def;
    }
    return std::unexpected(make_diag("expected integer", "§2.2.2.1"));
}

std::expected<Real, Diagnostic> ParamTokenizer::next_real_or(Real def) {
    if (record_ended_) return def;

    auto field = next_field();
    if (!field.has_value()) return def;

    if (std::holds_alternative<Real>(field.value())) {
        return std::get<Real>(field.value());
    }
    if (std::holds_alternative<int>(field.value())) {
        return static_cast<Real>(std::get<int>(field.value()));
    }
    if (std::holds_alternative<DefaultedField>(field.value())) {
        return def;
    }
    return std::unexpected(make_diag("expected real", "§2.2.2.2"));
}

std::expected<std::string, Diagnostic> ParamTokenizer::next_string_or(std::string def) {
    if (record_ended_) return def;

    auto field = next_field();
    if (!field.has_value()) return def;

    if (std::holds_alternative<std::string>(field.value())) {
        return std::get<std::string>(field.value());
    }
    if (std::holds_alternative<DefaultedField>(field.value())) {
        return def;
    }
    return std::unexpected(make_diag("expected string", "§2.2.2.3"));
}

std::expected<bool, Diagnostic> ParamTokenizer::next_logical_or(bool def) {
    if (record_ended_) return def;

    auto field = next_field();
    if (!field.has_value()) return def;

    if (std::holds_alternative<int>(field.value())) {
        int v = std::get<int>(field.value());
        if (v == 0) return false;
        if (v == 1) return true;
        return std::unexpected(make_diag("logical must be 0 or 1", "§2.2.2.6"));
    }
    if (std::holds_alternative<DefaultedField>(field.value())) {
        return def;
    }
    return std::unexpected(make_diag("expected logical", "§2.2.2.6"));
}

} // namespace iges
