#include "bibtex.hpp"

#include <cctype>
#include <string>

namespace bibtex {

namespace {

bool is_ident_start(char c) {
    if (std::isspace(static_cast<unsigned char>(c))) return false;
    switch (c) {
        case '@': case '{': case '}': case '(': case ')':
        case ',': case '=': case '#': case '"':
            return false;
        default: return true;
    }
}

bool is_digit(char c) { return c >= '0' && c <= '9'; }

} // namespace

Lexer::Lexer(std::string_view source) : src_(source) {}

char Lexer::peek() const {
    return pos_ < src_.size() ? src_[pos_] : '\0';
}

void Lexer::advance_char() {
    if (pos_ >= src_.size()) return;
    char c = src_[pos_++];
    if (c == '\n') { line_++; column_ = 1; }
    else            { column_++; }
}

void Lexer::skip_ws() {
    while (!eof() && std::isspace(static_cast<unsigned char>(peek()))) advance_char();
}

bool Lexer::find_next_at() {
    while (!eof()) {
        if (peek() == '@') {
            advance_char();
            return true;
        }
        advance_char();
    }
    return false;
}

Token Lexer::lex_ident() {
    Token tok;
    tok.kind = TokenKind::Ident;
    tok.line = line_;
    tok.column = column_;
    std::string s;
    while (!eof() && is_ident_start(peek())) {
        s.push_back(peek());
        advance_char();
    }
    bool all_digits = !s.empty();
    for (char c : s) if (!is_digit(c)) { all_digits = false; break; }
    if (all_digits) tok.kind = TokenKind::Number;
    tok.text = std::move(s);
    return tok;
}

Token Lexer::lex_braced_string() {
    Token tok;
    tok.kind = TokenKind::String;
    tok.line = line_;
    tok.column = column_;
    advance_char(); // consume '{'
    std::string s;
    int depth = 1;
    while (!eof() && depth > 0) {
        char c = peek();
        if (c == '{') {
            depth++;
            s.push_back(c);
            advance_char();
        } else if (c == '}') {
            depth--;
            if (depth == 0) { advance_char(); break; }
            s.push_back(c);
            advance_char();
        } else {
            s.push_back(c);
            advance_char();
        }
    }
    if (depth > 0) { tok.kind = TokenKind::Eof; tok.text.clear(); return tok; }
    tok.text = std::move(s);
    return tok;
}

Token Lexer::lex_quoted_string() {
    Token tok;
    tok.kind = TokenKind::String;
    tok.line = line_;
    tok.column = column_;
    advance_char(); // consume '"'
    std::string s;
    int depth = 0;
    while (!eof()) {
        char c = peek();
        if (c == '"' && depth == 0) {
            advance_char();
            tok.text = std::move(s);
            return tok;
        }
        if (c == '{') depth++;
        else if (c == '}' && depth > 0) depth--;
        s.push_back(c);
        advance_char();
    }
    tok.kind = TokenKind::Eof;
    tok.text.clear();
    return tok;
}

Token Lexer::lex_ident_at_current() {
    skip_ws();
    if (eof()) {
        Token tok; tok.kind = TokenKind::Eof; tok.line = line_; tok.column = column_;
        return tok;
    }
    return lex_ident();
}

Token Lexer::next_open_delim() {
    skip_ws();
    if (eof()) {
        Token tok; tok.kind = TokenKind::Eof; tok.line = line_; tok.column = column_;
        return tok;
    }
    std::size_t sl = line_, sc = column_;
    char c = peek();
    Token tok;
    tok.line = sl; tok.column = sc;
    if (c == '{') {
        tok.kind = TokenKind::OpenBrace;
        advance_char();
        return tok;
    }
    if (c == '(') {
        tok.kind = TokenKind::OpenParen;
        advance_char();
        return tok;
    }
    tok.kind = TokenKind::Eof;
    return tok;
}

Token Lexer::next_inside() {
    skip_ws();
    if (eof()) {
        Token tok; tok.kind = TokenKind::Eof; tok.line = line_; tok.column = column_;
        return tok;
    }
    char c = peek();
    std::size_t sl = line_, sc = column_;
    Token tok;
    tok.line = sl; tok.column = sc;
    switch (c) {
        case '}': tok.kind = TokenKind::CloseBrace; advance_char(); return tok;
        case ')': tok.kind = TokenKind::CloseParen; advance_char(); return tok;
        case ',': tok.kind = TokenKind::Comma;      advance_char(); return tok;
        case '=': tok.kind = TokenKind::Equals;     advance_char(); return tok;
        case '#': tok.kind = TokenKind::Hash;       advance_char(); return tok;
        case '"': { Token t = lex_quoted_string(); t.line = sl; t.column = sc; return t; }
        case '{': { Token t = lex_braced_string();  t.line = sl; t.column = sc; return t; }
        default:
            if (is_ident_start(c)) {
                Token t = lex_ident();
                return t;
            }
            // Unrecognized char — consume and return a single-char ident for error reporting.
            tok.kind = TokenKind::Ident;
            tok.text.push_back(c);
            advance_char();
            return tok;
    }
}

// --- Utilities ---

std::string to_lower(std::string_view s) {
    std::string out;
    out.reserve(s.size());
    for (char c : s) {
        out.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));
    }
    return out;
}

std::string whitespace_normalize(std::string_view s) {
    std::string out;
    out.reserve(s.size());
    int depth = 0;
    bool pending_space = false;
    bool have_content = false;
    for (char c : s) {
        if (c == '{') {
            if (pending_space) { out.push_back(' '); pending_space = false; }
            depth++;
            out.push_back(c);
            have_content = true;
            continue;
        }
        if (c == '}') {
            if (pending_space) { out.push_back(' '); pending_space = false; }
            if (depth > 0) depth--;
            out.push_back(c);
            have_content = true;
            continue;
        }
        if (depth > 0) {
            out.push_back(c);
            have_content = true;
            continue;
        }
        if (c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\f' || c == '\v') {
            if (have_content) pending_space = true;
            continue;
        }
        if (pending_space) {
            out.push_back(' ');
            pending_space = false;
        }
        out.push_back(c);
        have_content = true;
    }
    return out;
}

} // namespace bibtex
