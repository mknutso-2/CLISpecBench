#pragma once
// iges::ParamTokenizer — Free-format parameter field tokenizer.
//
// Implements the parsing rules from IGES 5.3 §2.2.2 and §2.2.3.
// Consumes a string of free-formatted IGES data and produces typed
// field values on demand.

#include "../types.hpp"
#include <string>
#include <string_view>
#include <expected>
#include <variant>
#include <vector>

namespace iges {

// ── Token types ──────────────────────────────────────────────

// A parsed parameter field value.  "Defaulted" means the field was
// empty (two consecutive delimiters or delimiter + record delimiter).
struct DefaultedField {};

using FieldValue = std::variant<
    DefaultedField,
    int,            // integer
    Real,           // real (float)
    std::string,    // Hollerith string
    bool            // logical
>;

// ── ParamTokenizer ───────────────────────────────────────────

class ParamTokenizer {
public:
    // Construct a tokenizer over one or more concatenated PD lines.
    // `data` is columns 1-64 of each PD line concatenated (with line
    // breaks stripped).  `param_delim` and `record_delim` come from
    // Global fields 1-2.
    explicit ParamTokenizer(std::string_view data,
                            char param_delim  = ',',
                            char record_delim = ';');

    // Are there more fields in the current record?
    bool has_next() const;

    // Is the current record terminated (record delimiter encountered)?
    bool at_record_end() const;

    // Read the next field as a generic FieldValue.
    std::expected<FieldValue, Diagnostic> next_field();

    // Typed accessors — read next field and convert.
    std::expected<int, Diagnostic>         next_integer();
    std::expected<Real, Diagnostic>        next_real();
    std::expected<std::string, Diagnostic> next_string();
    std::expected<DEIndex, Diagnostic>     next_pointer();
    std::expected<bool, Diagnostic>        next_logical();

    // Read next field; if defaulted, return the given default.
    std::expected<int, Diagnostic>         next_integer_or(int def);
    std::expected<Real, Diagnostic>        next_real_or(Real def);
    std::expected<std::string, Diagnostic> next_string_or(std::string def);
    std::expected<bool, Diagnostic>        next_logical_or(bool def);

    // Current 0-based position within the data stream (for diagnostics).
    int position() const;

private:
    std::string_view data_;
    std::size_t      pos_ = 0;
    char             pd_;
    char             rd_;
    bool             record_ended_ = false;

    // Skip whitespace (but not delimiters).
    void skip_blanks();

    // Parse a Hollerith string: nH...
    std::expected<std::string, Diagnostic> parse_hollerith();

    // Parse a numeric token (integer or real).
    std::expected<FieldValue, Diagnostic> parse_numeric();
};

// ── Free-standing parse helpers ──────────────────────────────

// Parse an integer from a raw string (§2.2.2.1 rules).
std::expected<int, Diagnostic> parse_integer(std::string_view s);

// Parse a real from a raw string (§2.2.2.2 rules).
std::expected<Real, Diagnostic> parse_real(std::string_view s);

// Parse a Hollerith string from `nH...` (§2.2.2.3 rules).
// Returns the string content (not including the nH prefix).
std::expected<std::string, Diagnostic> parse_hollerith_string(std::string_view s);

// Validate that a character is legal as a parameter or record delimiter
// (§2.2.3.1 prohibited character rules).
bool is_valid_delimiter(char c);

// Parse a timestamp from IGES format (§2.2.4.3.18).
std::expected<Timestamp, Diagnostic> parse_timestamp(std::string_view s);

} // namespace iges
