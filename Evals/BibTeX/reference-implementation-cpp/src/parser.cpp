#include "bibtex.hpp"

#include <cctype>
#include <string>

namespace bibtex {

namespace {

void seed_month_macros(Database& db) {
    static constexpr std::pair<const char*, const char*> MONTHS[] = {
        {"jan", "January"}, {"feb", "February"}, {"mar", "March"}, {"apr", "April"},
        {"may", "May"},     {"jun", "June"},     {"jul", "July"},  {"aug", "August"},
        {"sep", "September"},{"oct", "October"}, {"nov", "November"},{"dec", "December"}
    };
    for (const auto& [name, expansion] : MONTHS) {
        db.strings.emplace(name, expansion);
    }
}

} // namespace

Parser::Parser(std::string_view source, Database& db)
    : lexer_(source), db_(db) {
    seed_month_macros(db_);
}

void Parser::add_warning(Warning w) {
    db_.warnings.push_back(std::move(w));
}

Token Parser::next_inside() {
    if (has_pending_) {
        has_pending_ = false;
        return pending_;
    }
    return lexer_.next_inside();
}

void Parser::push_back(Token t) {
    pending_ = std::move(t);
    has_pending_ = true;
}

std::optional<ParseError> Parser::parse() {
    while (true) {
        if (!lexer_.find_next_at()) return std::nullopt;
        Token type_tok = lexer_.lex_ident_at_current();
        if (type_tok.kind != TokenKind::Ident && type_tok.kind != TokenKind::Number) {
            continue;
        }
        std::string type_lower = to_lower(type_tok.text);
        std::optional<ParseError> err;
        if (type_lower == "string") err = parse_string_entry();
        else if (type_lower == "preamble") err = parse_preamble_entry();
        else if (type_lower == "comment") err = drain_comment_entry();
        else err = parse_entry(type_lower);
        if (err) return err;
    }
}

std::optional<ParseError> Parser::parse_string_entry() {
    Token open = lexer_.next_open_delim();
    TokenKind close;
    if (open.kind == TokenKind::OpenBrace) close = TokenKind::CloseBrace;
    else if (open.kind == TokenKind::OpenParen) close = TokenKind::CloseParen;
    else return ParseError{"bib", open.line, open.column, "expected '{' or '(' after @string"};

    Token name_tok = next_inside();
    if (name_tok.kind != TokenKind::Ident) {
        return ParseError{"bib", name_tok.line, name_tok.column, "expected macro name after @string{"};
    }
    Token eq = next_inside();
    if (eq.kind != TokenKind::Equals) {
        return ParseError{"bib", eq.line, eq.column, "expected '=' after macro name"};
    }
    std::string value;
    auto verr = read_field_value(value);
    if (verr) return verr;

    Token close_tok = next_inside();
    if (close_tok.kind != close) {
        return ParseError{"bib", close_tok.line, close_tok.column, "expected closing delimiter for @string"};
    }
    // Store the raw (unnormalized) value so downstream concatenation preserves
    // internal whitespace. Normalization happens only when the macro's
    // expansion ends up in a field value or preamble (spec §1.4).
    db_.strings[to_lower(name_tok.text)] = value;
    return std::nullopt;
}

std::optional<ParseError> Parser::parse_preamble_entry() {
    Token open = lexer_.next_open_delim();
    TokenKind close;
    if (open.kind == TokenKind::OpenBrace) close = TokenKind::CloseBrace;
    else if (open.kind == TokenKind::OpenParen) close = TokenKind::CloseParen;
    else return ParseError{"bib", open.line, open.column, "expected '{' or '(' after @preamble"};

    std::string value;
    auto verr = read_field_value(value);
    if (verr) return verr;

    Token close_tok = next_inside();
    if (close_tok.kind != close) {
        return ParseError{"bib", close_tok.line, close_tok.column, "expected closing delimiter for @preamble"};
    }
    if (!db_.preamble.empty()) db_.preamble.push_back(' ');
    db_.preamble += whitespace_normalize(value);
    return std::nullopt;
}

std::optional<ParseError> Parser::drain_comment_entry() {
    Token open = lexer_.next_open_delim();
    if (open.kind != TokenKind::OpenBrace && open.kind != TokenKind::OpenParen) {
        // @comment with no body is a no-op
        return std::nullopt;
    }
    TokenKind close = (open.kind == TokenKind::OpenBrace) ? TokenKind::CloseBrace : TokenKind::CloseParen;
    int depth = 1;
    while (depth > 0) {
        Token t = next_inside();
        if (t.kind == TokenKind::Eof) {
            return ParseError{"bib", t.line, t.column, "unterminated @comment"};
        }
        if (t.kind == close) depth--;
    }
    return std::nullopt;
}

std::optional<ParseError> Parser::parse_entry(std::string_view type_lower) {
    Token open = lexer_.next_open_delim();
    TokenKind close;
    if (open.kind == TokenKind::OpenBrace) close = TokenKind::CloseBrace;
    else if (open.kind == TokenKind::OpenParen) close = TokenKind::CloseParen;
    else return ParseError{"bib", open.line, open.column, "expected '{' or '(' after entry type"};

    Token key_tok = next_inside();
    if (key_tok.kind != TokenKind::Ident && key_tok.kind != TokenKind::Number) {
        return ParseError{"bib", key_tok.line, key_tok.column, "expected citation key after entry opening"};
    }
    std::string key = key_tok.text;

    Entry entry;
    entry.key = key;
    entry.type = std::string(type_lower);
    entry.source_index = db_.entries.size();

    while (true) {
        Token sep = next_inside();
        if (sep.kind == close) break;
        if (sep.kind == TokenKind::Eof) {
            return ParseError{"bib", sep.line, sep.column, "unterminated entry"};
        }
        if (sep.kind != TokenKind::Comma) {
            return ParseError{"bib", sep.line, sep.column, "expected ',' or closing delimiter inside entry"};
        }
        Token field_name = next_inside();
        if (field_name.kind == close) break;
        if (field_name.kind != TokenKind::Ident) {
            return ParseError{"bib", field_name.line, field_name.column, "expected field name"};
        }
        Token eq = next_inside();
        if (eq.kind != TokenKind::Equals) {
            return ParseError{"bib", eq.line, eq.column, "expected '=' after field name"};
        }
        std::string value;
        auto verr = read_field_value(value);
        if (verr) return verr;

        std::string fname_lower = to_lower(field_name.text);
        std::string norm = whitespace_normalize(value);

        if (fname_lower == "crossref") {
            entry.has_crossref = true;
            entry.crossref_resolved = norm;
        }
        bool replaced = false;
        for (auto& f : entry.fields) {
            if (f.name == fname_lower) { f.value = norm; replaced = true; break; }
        }
        if (!replaced) entry.fields.push_back(Field{fname_lower, norm});
    }

    std::string lkey = to_lower(key);
    if (db_.key_index.count(lkey)) {
        Warning w;
        w.kind = "duplicate_key";
        w.message = "citation key '" + key + "' is already defined; second definition ignored";
        w.key = key;
        add_warning(std::move(w));
        return std::nullopt;
    }
    db_.entries.push_back(std::move(entry));
    db_.key_index[lkey] = db_.entries.size() - 1;
    return std::nullopt;
}

std::optional<ParseError> Parser::read_field_value(std::string& out) {
    out.clear();
    bool expect_operand = true;
    while (true) {
        Token t = next_inside();
        if (expect_operand) {
            if (t.kind == TokenKind::Number || t.kind == TokenKind::String) {
                out += t.text;
                expect_operand = false;
            } else if (t.kind == TokenKind::Ident) {
                std::string lname = to_lower(t.text);
                bool found = false;
                std::string expansion = resolve_macro(lname, found);
                if (!found) {
                    Warning w;
                    w.kind = "unresolved_macro";
                    w.message = "macro '" + t.text + "' is not defined";
                    w.field = t.text;
                    add_warning(std::move(w));
                    expansion.clear();
                }
                out += expansion;
                expect_operand = false;
            } else if (t.kind == TokenKind::Eof) {
                return ParseError{"bib", t.line, t.column, "unexpected EOF in field value"};
            } else {
                return ParseError{"bib", t.line, t.column, "expected field value"};
            }
        } else {
            if (t.kind == TokenKind::Hash) {
                expect_operand = true;
            } else if (t.kind == TokenKind::Comma
                       || t.kind == TokenKind::CloseBrace
                       || t.kind == TokenKind::CloseParen) {
                push_back(t);
                return std::nullopt;
            } else if (t.kind == TokenKind::Eof) {
                return ParseError{"bib", t.line, t.column, "unexpected EOF after value"};
            } else {
                return ParseError{"bib", t.line, t.column, "expected '#' or terminator in field value"};
            }
        }
    }
}

std::string Parser::resolve_macro(const std::string& lower_name, bool& found) const {
    auto it = db_.strings.find(lower_name);
    if (it == db_.strings.end()) { found = false; return {}; }
    found = true;
    return it->second;
}

// --- Post-parse resolution ---

void resolve_crossrefs(Database& db) {
    for (auto& entry : db.entries) {
        if (!entry.has_crossref) continue;
        std::string target_raw = entry.crossref_resolved.value();
        std::string target_lower = to_lower(target_raw);
        auto it = db.key_index.find(target_lower);
        if (it == db.key_index.end()) {
            Warning w;
            w.kind = "unresolved_crossref";
            w.message = "crossref target '" + target_raw + "' was not found in the database";
            w.key = entry.key;
            db.warnings.push_back(std::move(w));
            continue;
        }
        const auto& parent = db.entries[it->second];
        if (parent.has_crossref) {
            std::string ploweref = to_lower(parent.crossref_resolved.value());
            if (ploweref == to_lower(entry.key)) {
                Warning w;
                w.kind = "crossref_cycle";
                w.message = "crossref cycle involving '" + entry.key + "' and '" + parent.key + "'";
                w.key = entry.key;
                db.warnings.push_back(std::move(w));
                entry.crossref_resolved = target_raw;
                continue;
            }
        }
        entry.crossref_resolved = parent.key;
        for (const auto& pf : parent.fields) {
            if (pf.name == "crossref") continue;
            bool have = false;
            for (const auto& cf : entry.fields) {
                if (cf.name == pf.name) { have = true; break; }
            }
            if (!have) entry.fields.push_back(pf);
        }
    }
}

void parse_name_fields(Database& db) {
    for (auto& entry : db.entries) {
        for (const auto& f : entry.fields) {
            if (f.name == "author" || f.name == "editor") {
                entry.names[f.name] = parse_name_list(f.value);
            }
        }
    }
}

} // namespace bibtex
