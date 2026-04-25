#pragma once

#include <cstddef>
#include <cstdint>
#include <functional>
#include <map>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <variant>
#include <vector>

namespace bibtex {

struct Warning {
    std::string kind;
    std::string message;
    std::optional<std::string> key;
    std::optional<std::string> field;
};

struct ParseError {
    std::string source;   // "bib" | "bst" | "runtime"
    std::size_t line{};
    std::size_t column{};
    std::string message;
};

struct NamePart {
    std::string first;
    std::string von;
    std::string last;
    std::string jr;
    std::string literal;
};

struct Field {
    std::string name;
    std::string value;
};

struct Entry {
    std::string key;
    std::string type;
    std::vector<Field> fields;
    std::unordered_map<std::string, std::vector<NamePart>> names;
    std::optional<std::string> crossref_resolved;
    bool has_crossref{false};
    std::size_t source_index{0};
};

struct Database {
    std::vector<Entry> entries;
    std::unordered_map<std::string, std::size_t> key_index;
    std::unordered_map<std::string, std::string> strings;
    std::string preamble;
    std::vector<Warning> warnings;
};

// --- .bib Lexer / Parser (as before; full-spec preserved) ---

enum class TokenKind {
    OpenBrace, CloseBrace, OpenParen, CloseParen,
    Comma, Equals, Hash,
    Ident, Number, String, Eof,
};

struct Token {
    TokenKind kind{TokenKind::Eof};
    std::string text;
    std::size_t line{1};
    std::size_t column{1};
};

class Lexer {
public:
    explicit Lexer(std::string_view source);
    bool find_next_at();
    Token lex_ident_at_current();
    Token next_open_delim();
    Token next_inside();

    std::size_t line() const { return line_; }
    std::size_t column() const { return column_; }

private:
    std::string_view src_;
    std::size_t pos_{0};
    std::size_t line_{1};
    std::size_t column_{1};
    void advance_char();
    char peek() const;
    bool eof() const { return pos_ >= src_.size(); }
    void skip_ws();
    Token lex_ident();
    Token lex_braced_string();
    Token lex_quoted_string();
};

class Parser {
public:
    Parser(std::string_view source, Database& db);
    std::optional<ParseError> parse();

private:
    Lexer lexer_;
    Database& db_;
    Token pending_;
    bool has_pending_{false};

    Token next_inside();
    void push_back(Token t);

    std::optional<ParseError> parse_entry(std::string_view type_lower);
    std::optional<ParseError> parse_string_entry();
    std::optional<ParseError> parse_preamble_entry();
    std::optional<ParseError> drain_comment_entry();
    std::optional<ParseError> read_field_value(std::string& out);
    std::string resolve_macro(const std::string& lower_name, bool& found) const;
    void add_warning(Warning w);
};

void resolve_crossrefs(Database& db);
void parse_name_fields(Database& db);

std::vector<NamePart> parse_name_list(std::string_view value);
NamePart decompose_name(std::string_view value);

std::string to_lower(std::string_view s);
std::string whitespace_normalize(std::string_view s);

// --- .bst types ---

enum class BstValueKind { Integer, String, Function, Missing };

struct BstValue {
    BstValueKind kind{BstValueKind::Missing};
    int64_t integer{0};
    std::string str;
    std::string fn_name;  // only for Kind::Function (quoted name reference)

    static BstValue make_integer(int64_t v) {
        BstValue x; x.kind = BstValueKind::Integer; x.integer = v; return x;
    }
    static BstValue make_string(std::string v) {
        BstValue x; x.kind = BstValueKind::String; x.str = std::move(v); return x;
    }
    static BstValue make_function(std::string name) {
        BstValue x; x.kind = BstValueKind::Function; x.fn_name = std::move(name); return x;
    }
    static BstValue make_missing() {
        BstValue x; x.kind = BstValueKind::Missing; return x;
    }
};

enum class BstTokenKind {
    Ident,        // bare identifier (function call or entry-field/variable reference)
    Integer,      // #<int>
    String,       // "..."
    FunctionLit,  // { ... } — executable function
    QuotedName,   // 'NAME — pushes NAME as function reference
};

struct BstToken {
    BstTokenKind kind{BstTokenKind::Ident};
    std::string text;                  // ident name, string content, quoted name
    int64_t integer{0};                // for Integer
    std::vector<BstToken> body;        // for FunctionLit
    std::size_t line{1};
    std::size_t column{1};
};

struct BstFunction {
    bool is_builtin{false};
    // For user functions:
    std::vector<BstToken> body;
    // For builtins: handler is looked up by name in the interpreter.
};

struct BstProgram {
    // In declaration order — we execute commands as they appear.
    enum class CommandKind {
        Entry, Strings, Integers, Function, Macro,
        Read, Execute, Iterate, Reverse, Sort
    };
    struct Command {
        CommandKind kind;
        // For Function / Macro: name of the defined thing + body.
        std::string name;
        std::vector<BstToken> body;
        std::string literal_value;       // for Macro "..."
        // For Execute / Iterate / Reverse: target function name.
        std::string target;
        // For Entry: field list, integers list, strings list.
        std::vector<std::string> fields;
        std::vector<std::string> int_vars;
        std::vector<std::string> str_vars;
        // For Strings / Integers (global declarations):
        std::vector<std::string> names;
        std::size_t line{1};
        std::size_t column{1};
    };
    std::vector<Command> commands;
};

std::optional<ParseError> parse_bst(std::string_view source, BstProgram& out);

// --- Interpreter ---

struct LogInfo {
    std::size_t entries_read{0};
    std::size_t entries_cited_found{0};
    std::vector<std::string> entries_cited_missing;
    std::size_t functions_defined{0};
    std::vector<std::string> macros_defined;
    std::size_t iterations{0};
    std::size_t sorts{0};
    std::size_t reverse_iterations{0};
    std::size_t execute_calls{0};
};

struct BstResult {
    std::string bbl_output;
    std::vector<Warning> warnings;
    LogInfo log;
};

std::optional<ParseError> execute_bst(
    const BstProgram& program,
    const Database& db,
    const std::vector<std::string>& cites,
    BstResult& result
);

// --- JSON writers ---

std::string emit_error_json(const ParseError& err, const std::vector<Warning>& warnings);
std::string emit_log_json(const BstResult& result);

} // namespace bibtex
