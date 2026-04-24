#include "bibtex.hpp"

#include <cctype>
#include <string>

namespace bibtex {

namespace {

bool is_bst_id_start(char c) {
    return std::isalpha(static_cast<unsigned char>(c)) || c == '_' || c == '.' || c == '/';
}
bool is_bst_id_cont(char c) {
    return std::isalnum(static_cast<unsigned char>(c))
        || c == '_' || c == '.' || c == '$' || c == '-' || c == '/';
}

struct BstLex {
    std::string_view src;
    std::size_t pos{0};
    std::size_t line{1};
    std::size_t col{1};

    char peek() const { return pos < src.size() ? src[pos] : '\0'; }
    bool eof() const { return pos >= src.size(); }
    void advance() {
        if (pos >= src.size()) return;
        if (src[pos] == '\n') { line++; col = 1; }
        else col++;
        pos++;
    }
    void skip_ws_comments() {
        while (!eof()) {
            char c = peek();
            if (std::isspace(static_cast<unsigned char>(c))) { advance(); continue; }
            if (c == '%') {
                while (!eof() && peek() != '\n') advance();
                continue;
            }
            break;
        }
    }

    // Read a single token (which may be a FunctionLit containing many tokens).
    std::optional<ParseError> next(std::optional<BstToken>& out) {
        skip_ws_comments();
        if (eof()) { out.reset(); return std::nullopt; }
        std::size_t sl = line, sc = col;
        char c = peek();

        if (c == '#') {
            advance();
            // Integer: optional sign, digits.
            int64_t sign = 1;
            if (peek() == '-') { sign = -1; advance(); }
            else if (peek() == '+') { advance(); }
            int64_t v = 0;
            bool any = false;
            while (std::isdigit(static_cast<unsigned char>(peek()))) {
                v = v * 10 + (peek() - '0');
                advance();
                any = true;
            }
            if (!any) return ParseError{"bst", sl, sc, "expected digits after '#'"};
            BstToken t;
            t.kind = BstTokenKind::Integer;
            t.integer = sign * v;
            t.line = sl; t.column = sc;
            out = std::move(t);
            return std::nullopt;
        }
        if (c == '"') {
            advance();
            std::string s;
            while (!eof() && peek() != '"') {
                s.push_back(peek());
                advance();
            }
            if (eof()) return ParseError{"bst", sl, sc, "unterminated string literal"};
            advance(); // consume closing "
            BstToken t;
            t.kind = BstTokenKind::String;
            t.text = std::move(s);
            t.line = sl; t.column = sc;
            out = std::move(t);
            return std::nullopt;
        }
        if (c == '{') {
            advance();
            // FunctionLit — a sequence of tokens terminated by matching '}'.
            BstToken t;
            t.kind = BstTokenKind::FunctionLit;
            t.line = sl; t.column = sc;
            while (true) {
                skip_ws_comments();
                if (eof()) return ParseError{"bst", sl, sc, "unterminated function literal"};
                if (peek() == '}') { advance(); break; }
                std::optional<BstToken> inner;
                auto err = next(inner);
                if (err) return err;
                if (!inner) return ParseError{"bst", line, col, "unterminated function literal"};
                t.body.push_back(std::move(*inner));
            }
            out = std::move(t);
            return std::nullopt;
        }
        if (c == '\'') {
            advance();
            std::string s;
            while (!eof() && !std::isspace(static_cast<unsigned char>(peek()))
                   && peek() != '}' && peek() != '{') {
                s.push_back(peek());
                advance();
            }
            if (s.empty()) return ParseError{"bst", sl, sc, "expected name after \"'\""};
            BstToken t;
            t.kind = BstTokenKind::QuotedName;
            t.text = std::move(s);
            t.line = sl; t.column = sc;
            out = std::move(t);
            return std::nullopt;
        }
        if (is_bst_id_start(c)
            || c == '>' || c == '<' || c == '=' || c == '+' || c == '-' || c == '*' || c == ':') {
            // Identifier or operator (operators are single/double-char ids like `>`, `<`, `=`, `+`, `-`, `*`, `:=`).
            std::string s;
            s.push_back(c);
            advance();
            // `:=` is a 2-char token.
            if (c == ':' && peek() == '=') { s.push_back('='); advance(); }
            else if (c == '>' || c == '<' || c == '=' || c == '+' || c == '-' || c == '*') {
                // Single char ops. Nothing else to read.
            } else {
                while (!eof() && is_bst_id_cont(peek())) {
                    s.push_back(peek());
                    advance();
                }
            }
            BstToken t;
            t.kind = BstTokenKind::Ident;
            t.text = std::move(s);
            t.line = sl; t.column = sc;
            out = std::move(t);
            return std::nullopt;
        }
        return ParseError{"bst", sl, sc, std::string("unexpected character '") + c + "'"};
    }
};

bool expect_brace_names(BstLex& lex, std::vector<std::string>& out, ParseError& err) {
    std::optional<BstToken> tok;
    auto e = lex.next(tok);
    if (e) { err = *e; return false; }
    if (!tok || tok->kind != BstTokenKind::FunctionLit) {
        err = ParseError{"bst", lex.line, lex.col, "expected '{ ... }' name list"};
        return false;
    }
    for (const auto& inner : tok->body) {
        if (inner.kind != BstTokenKind::Ident) {
            err = ParseError{"bst", inner.line, inner.column, "expected identifier inside name list"};
            return false;
        }
        out.push_back(inner.text);
    }
    return true;
}

} // namespace

std::optional<ParseError> parse_bst(std::string_view source, BstProgram& out) {
    BstLex lex;
    lex.src = source;
    while (true) {
        lex.skip_ws_comments();
        if (lex.eof()) break;
        std::optional<BstToken> head_opt;
        auto err = lex.next(head_opt);
        if (err) return err;
        if (!head_opt) break;
        BstToken head = *head_opt;
        if (head.kind != BstTokenKind::Ident) {
            return ParseError{"bst", head.line, head.column, "expected top-level command"};
        }
        BstProgram::Command cmd;
        cmd.line = head.line; cmd.column = head.column;
        std::string cmd_name = head.text;
        // Case-insensitive command matching.
        std::string lower = to_lower(cmd_name);

        auto expect_single_ident_in_braces = [&](std::string& out_name) -> std::optional<ParseError> {
            std::optional<BstToken> tok;
            auto e = lex.next(tok);
            if (e) return e;
            if (!tok || tok->kind != BstTokenKind::FunctionLit || tok->body.size() != 1
                || tok->body[0].kind != BstTokenKind::Ident) {
                return ParseError{"bst", lex.line, lex.col, "expected '{ name }'"};
            }
            out_name = tok->body[0].text;
            return std::nullopt;
        };

        auto expect_body_braces = [&](std::vector<BstToken>& out_body) -> std::optional<ParseError> {
            std::optional<BstToken> tok;
            auto e = lex.next(tok);
            if (e) return e;
            if (!tok || tok->kind != BstTokenKind::FunctionLit) {
                return ParseError{"bst", lex.line, lex.col, "expected '{ ... }' body"};
            }
            out_body = std::move(tok->body);
            return std::nullopt;
        };

        if (lower == "entry") {
            cmd.kind = BstProgram::CommandKind::Entry;
            ParseError pe{"bst", 0, 0, ""};
            if (!expect_brace_names(lex, cmd.fields, pe)) return pe;
            if (!expect_brace_names(lex, cmd.int_vars, pe)) return pe;
            if (!expect_brace_names(lex, cmd.str_vars, pe)) return pe;
        } else if (lower == "strings") {
            cmd.kind = BstProgram::CommandKind::Strings;
            ParseError pe{"bst", 0, 0, ""};
            if (!expect_brace_names(lex, cmd.names, pe)) return pe;
        } else if (lower == "integers") {
            cmd.kind = BstProgram::CommandKind::Integers;
            ParseError pe{"bst", 0, 0, ""};
            if (!expect_brace_names(lex, cmd.names, pe)) return pe;
        } else if (lower == "function") {
            cmd.kind = BstProgram::CommandKind::Function;
            if (auto e = expect_single_ident_in_braces(cmd.name); e) return e;
            if (auto e = expect_body_braces(cmd.body); e) return e;
        } else if (lower == "macro") {
            cmd.kind = BstProgram::CommandKind::Macro;
            if (auto e = expect_single_ident_in_braces(cmd.name); e) return e;
            // Macro body is `{ "value" }`.
            std::optional<BstToken> body_tok;
            if (auto e = lex.next(body_tok); e) return e;
            if (!body_tok || body_tok->kind != BstTokenKind::FunctionLit || body_tok->body.size() != 1
                || body_tok->body[0].kind != BstTokenKind::String) {
                return ParseError{"bst", lex.line, lex.col, "expected '{ \"value\" }' for MACRO"};
            }
            cmd.literal_value = body_tok->body[0].text;
        } else if (lower == "read") {
            cmd.kind = BstProgram::CommandKind::Read;
        } else if (lower == "execute") {
            cmd.kind = BstProgram::CommandKind::Execute;
            if (auto e = expect_single_ident_in_braces(cmd.target); e) return e;
        } else if (lower == "iterate") {
            cmd.kind = BstProgram::CommandKind::Iterate;
            if (auto e = expect_single_ident_in_braces(cmd.target); e) return e;
        } else if (lower == "reverse") {
            cmd.kind = BstProgram::CommandKind::Reverse;
            if (auto e = expect_single_ident_in_braces(cmd.target); e) return e;
        } else if (lower == "sort") {
            cmd.kind = BstProgram::CommandKind::Sort;
        } else {
            return ParseError{"bst", head.line, head.column,
                              std::string("unknown top-level command '") + cmd_name + "'"};
        }
        out.commands.push_back(std::move(cmd));
    }
    return std::nullopt;
}

} // namespace bibtex
