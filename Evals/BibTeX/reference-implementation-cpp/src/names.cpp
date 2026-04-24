#include "bibtex.hpp"

#include <cctype>
#include <string>
#include <vector>

namespace bibtex {

namespace {

// Tokenize a name string into whitespace-separated tokens, respecting brace depth.
// A tie character `~` is treated as whitespace for segmentation but preserved in the literal
// via the caller. Brace groups are atomic tokens (the braces are kept).
std::vector<std::string> tokenize_name(std::string_view s) {
    std::vector<std::string> tokens;
    std::string cur;
    int depth = 0;
    auto flush = [&]() {
        if (!cur.empty()) {
            tokens.push_back(std::move(cur));
            cur.clear();
        }
    };
    for (char c : s) {
        if (depth == 0) {
            if (c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\f' || c == '\v' || c == '~') {
                flush();
                continue;
            }
            if (c == '{') depth++;
            cur.push_back(c);
        } else {
            if (c == '{') depth++;
            else if (c == '}') depth--;
            cur.push_back(c);
        }
    }
    flush();
    return tokens;
}

// Classify a token as "lowercase" per spec §4.6. The interior of brace groups is
// opaque; tokens starting with `{` (including `{\...}`) are uppercase for v0.1.
bool token_is_lowercase(const std::string& tok) {
    if (tok.empty()) return false;
    if (tok[0] == '{') return false; // brace-protected opaque
    if (std::isalpha(static_cast<unsigned char>(tok[0]))) {
        return std::islower(static_cast<unsigned char>(tok[0])) != 0;
    }
    return false; // non-alpha first char → uppercase per spec §4.6
}

std::string join_tokens(const std::vector<std::string>& toks, std::size_t begin, std::size_t end) {
    std::string out;
    for (std::size_t i = begin; i < end; ++i) {
        if (!out.empty()) out.push_back(' ');
        out += toks[i];
    }
    return out;
}

// Apply Form 1 (no commas) decomposition to a pre-tokenized slice [begin, end).
// Writes into first/von/last by the spec §4.1 rule.
void decompose_form1_slice(const std::vector<std::string>& toks,
                           std::size_t begin, std::size_t end,
                           std::string& first, std::string& von, std::string& last) {
    if (end <= begin) return;
    std::size_t n = end - begin;
    if (n == 1) {
        last = toks[begin];
        return;
    }
    // Find the last lowercase token in the range. If none, all caps: first = all but last, last = last token.
    std::size_t last_lower = end;
    for (std::size_t i = begin; i < end; ++i) {
        if (token_is_lowercase(toks[i])) last_lower = i;
    }
    if (last_lower == end) {
        // No lowercase token — all uppercase. First = toks[begin..end-1], Last = toks[end-1].
        last = toks[end - 1];
        if (end - 1 > begin) first = join_tokens(toks, begin, end - 1);
        return;
    }
    // von spans from the first lowercase token onwards up to and including last_lower.
    // Find the first lowercase token in the range.
    std::size_t first_lower = begin;
    while (first_lower < end && !token_is_lowercase(toks[first_lower])) first_lower++;

    // First = tokens[begin..first_lower)
    if (first_lower > begin) first = join_tokens(toks, begin, first_lower);
    // von = tokens[first_lower..last_lower+1)
    von = join_tokens(toks, first_lower, last_lower + 1);
    // Last = tokens[last_lower+1..end)
    if (last_lower + 1 < end) {
        last = join_tokens(toks, last_lower + 1, end);
    } else {
        // Edge case: lowercase tokens run all the way to the end with no trailing uppercase.
        // Per spec example `"van de"` -> First=``, von=``, Last=`van de`.
        // Pull the von back: Last gets everything from first_lower onwards, von is empty.
        last = join_tokens(toks, first_lower, end);
        von.clear();
    }
}

} // namespace

NamePart decompose_name(std::string_view value) {
    NamePart np;
    np.literal = std::string(value);

    // Split on commas at depth 0.
    std::vector<std::string> segments;
    std::string cur;
    int depth = 0;
    for (char c : value) {
        if (depth == 0 && c == ',') {
            segments.push_back(std::move(cur));
            cur.clear();
            continue;
        }
        if (c == '{') depth++;
        else if (c == '}' && depth > 0) depth--;
        cur.push_back(c);
    }
    segments.push_back(std::move(cur));

    auto trim = [](std::string& s) {
        std::size_t a = 0, b = s.size();
        while (a < b && std::isspace(static_cast<unsigned char>(s[a]))) a++;
        while (b > a && std::isspace(static_cast<unsigned char>(s[b - 1]))) b--;
        s = s.substr(a, b - a);
    };
    for (auto& seg : segments) trim(seg);

    if (segments.size() == 1) {
        auto toks = tokenize_name(segments[0]);
        decompose_form1_slice(toks, 0, toks.size(), np.first, np.von, np.last);
        return np;
    }

    // Helper: decompose a head slice (Form 2/3) into von/Last per spec §4.2.
    auto decompose_head = [](const std::vector<std::string>& toks,
                             std::string& von, std::string& last) {
        von.clear();
        last.clear();
        if (toks.empty()) return;
        std::size_t n = toks.size();
        std::size_t last_lower = n;
        for (std::size_t i = 0; i < n; ++i) {
            if (token_is_lowercase(toks[i])) last_lower = i;
        }
        if (last_lower == n) {
            last = join_tokens(toks, 0, n);
            return;
        }
        std::size_t first_lower = 0;
        while (first_lower < n && !token_is_lowercase(toks[first_lower])) first_lower++;
        if (last_lower + 1 < n) {
            // Leading caps (if any) before first_lower prepend to Last.
            std::string prefix = join_tokens(toks, 0, first_lower);
            std::string suffix = join_tokens(toks, last_lower + 1, n);
            if (prefix.empty()) last = suffix;
            else if (suffix.empty()) last = prefix;
            else last = prefix + " " + suffix;
            von = join_tokens(toks, first_lower, last_lower + 1);
        } else {
            // Head ends on a lowercase token: no trailing-caps Last.
            // Spec §4.2 invariant: Last is non-empty; promote everything from first_lower to Last.
            // Leading caps (if any) still prepend.
            std::string prefix = join_tokens(toks, 0, first_lower);
            std::string rest = join_tokens(toks, first_lower, n);
            last = prefix.empty() ? rest : prefix + " " + rest;
            von.clear();
        }
    };

    if (segments.size() == 2) {
        auto head_toks = tokenize_name(segments[0]);
        decompose_head(head_toks, np.von, np.last);
        np.first = segments[1];
        return np;
    }

    if (segments.size() == 3) {
        auto head_toks = tokenize_name(segments[0]);
        decompose_head(head_toks, np.von, np.last);
        np.jr = segments[1];
        np.first = segments[2];
        return np;
    }

    // 4+ segments: use first two commas as structural, join rest into First.
    auto head_toks = tokenize_name(segments[0]);
    decompose_head(head_toks, np.von, np.last);
    np.jr = segments[1];
    std::string first;
    for (std::size_t i = 2; i < segments.size(); ++i) {
        if (!first.empty()) first += ", ";
        first += segments[i];
    }
    np.first = first;
    return np;
}

std::vector<NamePart> parse_name_list(std::string_view value) {
    // Split on `and` keyword at brace depth 0, word-bounded with surrounding whitespace.
    std::vector<std::string> pieces;
    std::string cur;
    int depth = 0;
    std::size_t i = 0;
    const std::size_t n = value.size();
    while (i < n) {
        char c = value[i];
        if (c == '{') { depth++; cur.push_back(c); i++; continue; }
        if (c == '}' && depth > 0) { depth--; cur.push_back(c); i++; continue; }
        if (depth == 0) {
            bool at_space_before =
                (i == 0) || (i > 0 && (value[i - 1] == ' ' || value[i - 1] == '\t' ||
                                        value[i - 1] == '\n' || value[i - 1] == '\r'));
            if (at_space_before && i + 3 <= n) {
                char a = value[i], b = value[i + 1], d = value[i + 2];
                bool is_and = (a == 'a' || a == 'A') && (b == 'n' || b == 'N') && (d == 'd' || d == 'D');
                bool space_after = (i + 3 == n) ||
                                   value[i + 3] == ' ' || value[i + 3] == '\t' ||
                                   value[i + 3] == '\n' || value[i + 3] == '\r';
                if (is_and && space_after) {
                    // Trim trailing whitespace from cur
                    std::size_t end = cur.size();
                    while (end > 0 && std::isspace(static_cast<unsigned char>(cur[end - 1]))) end--;
                    cur.resize(end);
                    pieces.push_back(std::move(cur));
                    cur.clear();
                    i += 3;
                    while (i < n && std::isspace(static_cast<unsigned char>(value[i]))) i++;
                    continue;
                }
            }
        }
        cur.push_back(c);
        i++;
    }
    // Trim trailing whitespace on last piece
    {
        std::size_t end = cur.size();
        while (end > 0 && std::isspace(static_cast<unsigned char>(cur[end - 1]))) end--;
        cur.resize(end);
    }
    pieces.push_back(std::move(cur));

    // Trim leading whitespace on each piece before decomposing.
    std::vector<NamePart> out;
    for (auto& piece : pieces) {
        std::size_t start = 0;
        while (start < piece.size() && std::isspace(static_cast<unsigned char>(piece[start]))) start++;
        std::string trimmed = piece.substr(start);
        out.push_back(decompose_name(trimmed));
    }
    return out;
}

} // namespace bibtex
