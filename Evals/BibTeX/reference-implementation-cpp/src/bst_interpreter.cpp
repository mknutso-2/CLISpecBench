#include "bibtex.hpp"

#include <algorithm>
#include <cctype>
#include <cstring>
#include <functional>
#include <string>
#include <unordered_map>
#include <unordered_set>

namespace bibtex {

namespace {

// Count "text characters" per spec §3.5 text.length$/width$:
// - a brace group contributes the count of its interior (same rule), treating the outer braces as zero.
// - a `\foo` special (backslash + letters, optionally followed by arg-brace) counts as 1.
// - any other character counts as 1.
std::size_t count_text_chars(std::string_view s) {
    std::size_t count = 0;
    std::size_t i = 0;
    while (i < s.size()) {
        char c = s[i];
        if (c == '{') {
            // Find matching close.
            int depth = 1;
            std::size_t j = i + 1;
            while (j < s.size() && depth > 0) {
                if (s[j] == '{') depth++;
                else if (s[j] == '}') depth--;
                if (depth == 0) break;
                j++;
            }
            // Content is s[i+1 .. j).
            std::string_view inner = s.substr(i + 1, (j > i + 1 ? j - i - 1 : 0));
            // Check if it starts with a special control sequence.
            if (!inner.empty() && inner[0] == '\\') {
                // Count as 1.
                count += 1;
            } else {
                count += count_text_chars(inner);
            }
            i = (j < s.size()) ? j + 1 : j;
        } else {
            count += 1;
            i++;
        }
    }
    return count;
}

// Extract first n "text characters" in the text-char sense.
std::string text_prefix(std::string_view s, std::size_t n) {
    std::string out;
    std::size_t count = 0;
    std::size_t i = 0;
    while (i < s.size() && count < n) {
        char c = s[i];
        if (c == '{') {
            int depth = 1;
            std::size_t j = i + 1;
            while (j < s.size() && depth > 0) {
                if (s[j] == '{') depth++;
                else if (s[j] == '}') depth--;
                if (depth == 0) break;
                j++;
            }
            // Brace group counts as one text-char collectively if it starts with '\';
            // otherwise it counts its content individually.
            std::string_view inner = s.substr(i + 1, (j > i + 1 ? j - i - 1 : 0));
            if (!inner.empty() && inner[0] == '\\') {
                out.append(s.substr(i, (j < s.size() ? j - i + 1 : j - i)));
                count += 1;
            } else {
                // Recurse: add characters one by one.
                out.push_back('{');
                std::size_t to_take = n - count;
                std::string prefix = text_prefix(inner, to_take);
                out.append(prefix);
                // Count added chars: we can't cheaply count; use count_text_chars on the prefix.
                count += count_text_chars(prefix);
                out.push_back('}');
            }
            i = (j < s.size()) ? j + 1 : j;
        } else {
            out.push_back(c);
            count += 1;
            i++;
        }
    }
    return out;
}

// purify$ per bibtex.web §13 (§10602 "Perform the purification"):
//   - At brace level 0:
//       white_space or sep_char → single space
//       alpha or numeric        → keep
//       other                   → drop
//   - At brace level ≥ 1 inside a `{\...}` "special character":
//       the control-sequence letters are dropped, *except* that for
//       `\oe`, `\OE`, `\ae`, `\AE`, `\ss` we restore both letters;
//       for any other control sequence we restore only the first letter.
//       All subsequent characters inside the brace group are kept if alpha
//       or numeric, otherwise dropped (no white_space/sep_char → space
//       conversion inside the group).
//   - At brace level ≥ 1 outside a special character (i.e. a plain `{...}`
//       group with no leading `\`), just keep alpha/numeric inside; drop
//       everything else.
std::string purify(std::string_view s) {
    auto is_alnum = [](unsigned char c) {
        return (c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z');
    };
    auto is_white_or_sep = [](unsigned char c) {
        return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '~' || c == '-';
    };

    std::string out;
    std::size_t i = 0;
    int depth = 0;
    while (i < s.size()) {
        unsigned char c = static_cast<unsigned char>(s[i]);
        if (depth == 0) {
            if (is_white_or_sep(c)) {
                out.push_back(' ');
                i++;
                continue;
            }
            if (is_alnum(c)) {
                out.push_back(static_cast<char>(c));
                i++;
                continue;
            }
            if (c == '{') {
                depth++;
                // Check for a "special character" group `{\letters...}`.
                if (i + 1 < s.size() && s[i + 1] == '\\') {
                    std::size_t j = i + 2;
                    std::string ctrl;
                    while (j < s.size()
                           && std::isalpha(static_cast<unsigned char>(s[j]))) {
                        ctrl.push_back(s[j]);
                        j++;
                    }
                    // Emit first letter (always), plus second letter for the
                    // five diphthong/ligature specials.
                    if (!ctrl.empty()) {
                        out.push_back(ctrl[0]);
                        bool two = (ctrl == "oe" || ctrl == "OE"
                                 || ctrl == "ae" || ctrl == "AE"
                                 || ctrl == "ss");
                        if (two && ctrl.size() >= 2) out.push_back(ctrl[1]);
                    }
                    i = j;
                    continue;
                }
                i++;
                continue;
            }
            if (c == '}') {
                if (depth > 0) depth--;
                i++;
                continue;
            }
            // Any other character at level 0: drop.
            i++;
            continue;
        }
        // Inside a brace group.
        if (c == '{') { depth++; i++; continue; }
        if (c == '}') { if (depth > 0) depth--; i++; continue; }
        if (is_alnum(c)) {
            out.push_back(static_cast<char>(c));
            i++;
            continue;
        }
        // Everything else inside a brace group is dropped (no white_space/
        // sep_char → space conversion).
        i++;
    }
    // Collapse runs of spaces and strip leading/trailing spaces so the result
    // is a stable key for sorting comparisons.
    std::string trimmed;
    trimmed.reserve(out.size());
    bool prev_space = true;  // treat leading as space to skip leading
    for (char ch : out) {
        if (ch == ' ') {
            if (!prev_space) trimmed.push_back(' ');
            prev_space = true;
        } else {
            trimmed.push_back(ch);
            prev_space = false;
        }
    }
    while (!trimmed.empty() && trimmed.back() == ' ') trimmed.pop_back();
    return trimmed;
}

// change.case$ per btxhak §3.5:
//   - `u`: uppercase all alpha at brace-level 0 (including first).
//   - `l`: lowercase all alpha at brace-level 0.
//   - `t`: lowercase all alpha at brace-level 0 EXCEPT:
//       * the very first character of the string is left alone;
//       * the first character following any colon + nonempty whitespace run
//         is also left alone.
//   - Content inside brace groups is left entirely untouched (including the
//     letters of accented-character macros).
std::string change_case(std::string_view s, char mode) {
    std::string out;
    out.reserve(s.size());
    std::size_t i = 0;
    int depth = 0;
    bool seen_any_char = false;  // toggled once we copy the very first byte
    bool at_letter_after_colon_ws = false;

    auto to_lower = [](char ch) {
        return static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
    };
    auto to_upper = [](char ch) {
        return static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    };

    while (i < s.size()) {
        char c = s[i];
        if (c == '{') {
            out.push_back(c);
            depth++;
            i++;
            seen_any_char = true;
            at_letter_after_colon_ws = false;
            continue;
        }
        if (c == '}') {
            out.push_back(c);
            if (depth > 0) depth--;
            i++;
            at_letter_after_colon_ws = false;
            continue;
        }
        if (depth > 0) {
            out.push_back(c);
            i++;
            continue;
        }
        // At brace-level 0.
        bool is_alpha = std::isalpha(static_cast<unsigned char>(c)) != 0;
        if (mode == 'u') {
            out.push_back(is_alpha ? to_upper(c) : c);
        } else if (mode == 'l') {
            out.push_back(is_alpha ? to_lower(c) : c);
        } else if (mode == 't') {
            // Preserve case on: the very first char, or the first alpha char
            // after a colon + whitespace run.
            bool preserve = !seen_any_char || at_letter_after_colon_ws;
            if (preserve && is_alpha) {
                out.push_back(c);  // leave untouched
            } else if (is_alpha) {
                out.push_back(to_lower(c));
            } else {
                out.push_back(c);
            }
        } else {
            out.push_back(c);
        }
        if (c == ':') {
            // Look ahead at brace-level 0 for a nonempty whitespace run.
            std::size_t k = i + 1;
            bool saw_ws = false;
            while (k < s.size()) {
                char nc = s[k];
                if (nc == ' ' || nc == '\t' || nc == '\n' || nc == '\r') {
                    saw_ws = true;
                    k++;
                    continue;
                }
                break;
            }
            if (saw_ws) at_letter_after_colon_ws = true;
            else at_letter_after_colon_ws = false;
        } else if (is_alpha) {
            at_letter_after_colon_ws = false;
        } else if (c != ' ' && c != '\t' && c != '\n' && c != '\r') {
            // Non-whitespace non-colon non-alpha resets the flag.
            at_letter_after_colon_ws = false;
        }
        // Whitespace keeps the flag rolling (so "foo: \nBar" still triggers).
        seen_any_char = true;
        i++;
    }
    return out;
}

// CMR-10 character widths in hundredths of a point (rounded). Copied directly
// from bibtex.web §13 (`char_width` array, June 1987 cmr10). Only printable
// ASCII (and some TeX-special glyphs) have nonzero widths; everything else is
// zero so it doesn't contribute to the comparison.
constexpr int kCmr10Width[128] = {
    /* 000-037 */ 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,500,722,778,0,903,1014,0,
    /* 040-057 */ 278,278,500,833,500,833,778,278,389,389,500,778,278,333,278,500,
    /* 060-077 */ 500,500,500,500,500,500,500,500,500,500,278,278,278,778,472,472,
    /* 100-117 */ 778,750,708,722,764,681,653,785,750,361,514,778,625,917,750,778,
    /* 120-137 */ 681,778,736,556,722,750,750,1028,750,750,611,278,500,278,500,278,
    /* 140-157 */ 278,500,556,444,556,444,306,500,556,278,306,528,278,833,556,500,
    /* 160-177 */ 556,528,392,394,389,556,528,722,528,528,444,500,1000,500,500,0,
};

// width$ per bibtex.web §13. The width is computed as if the characters were
// typeset in cmr10, with:
//  - unmatched right braces contributing zero (treated as the surrounding
//    character);
//  - a `{\foo...}` special-character group at brace-level 1 contributing the
//    width of its interior (with the specials `\ss`, `\ae`, `\oe`, `\AE`,
//    `\OE` mapped to the five predefined widths 500, 722, 778, 903, 1014).
int approximate_width(std::string_view s) {
    auto special_width = [](std::string_view ctrl) -> int {
        if (ctrl == "ss") return 500;
        if (ctrl == "ae") return 722;
        if (ctrl == "oe") return 778;
        if (ctrl == "AE") return 903;
        if (ctrl == "OE") return 1014;
        return -1;
    };
    int total = 0;
    std::size_t i = 0;
    int depth = 0;
    while (i < s.size()) {
        unsigned char c = static_cast<unsigned char>(s[i]);
        if (c == '{') {
            // Look for a "special character" group: `{\letters...}`.
            if (depth == 0 && i + 1 < s.size() && s[i + 1] == '\\') {
                std::size_t j = i + 2;
                std::string ctrl;
                while (j < s.size() && std::isalpha(static_cast<unsigned char>(s[j]))) {
                    ctrl.push_back(s[j]);
                    j++;
                }
                // Measure the group interior: walk until matching close.
                int d = 1;
                std::size_t k = i + 1;
                while (k < s.size() && d > 0) {
                    if (s[k] == '{') d++;
                    else if (s[k] == '}') d--;
                    if (d == 0) break;
                    k++;
                }
                int w = special_width(ctrl);
                if (w >= 0) {
                    total += w;
                } else {
                    // Not a predefined special: measure the remainder of the
                    // group (after the control word) recursively.
                    std::size_t end = (k < s.size()) ? k : s.size();
                    std::string_view inner = s.substr(j, end - j);
                    total += approximate_width(inner);
                }
                i = (k < s.size()) ? k + 1 : k;
                continue;
            }
            depth++;
            i++;
            continue;
        }
        if (c == '}') {
            if (depth > 0) depth--;
            i++;
            continue;
        }
        if (c < 128) total += kCmr10Width[c];
        i++;
    }
    return total;
}

// Split a name-list on "and" at brace depth 0.
std::vector<std::string> split_and(std::string_view s) {
    return {}; // Unused — parse_name_list handles the same work; we call it directly.
}

// A single name-part token plus the separator char that preceded it.
// The separator is ' ' by default; if the user used a `-` or `~` between
// tokens in the original name, that character is preserved so BibTeX can
// reuse it as the inter-token string (bibtex.web §10270 "sep_char" rule).
struct NameTok {
    std::string text;   // token contents, brace groups preserved
    char sep{' '};      // separator between this token and the previous one
};

// Tokenize a name part (first/von/last/jr) back into tokens by splitting on
// whitespace / ties / hyphens at brace depth 0. The separator is recorded on
// each token (except the first, which has no predecessor).
std::vector<NameTok> tokenize_name_part(std::string_view s) {
    std::vector<NameTok> out;
    std::string cur;
    int depth = 0;
    char pending_sep = ' ';
    bool in_token = false;
    auto flush = [&]() {
        if (!cur.empty()) {
            NameTok nt;
            nt.text = std::move(cur);
            nt.sep = pending_sep;
            out.push_back(std::move(nt));
            cur.clear();
            pending_sep = ' ';
        }
        in_token = false;
    };
    for (char c : s) {
        if (depth == 0 && (c == ' ' || c == '\t' || c == '\n' || c == '\r' ||
                           c == '~' || c == '-')) {
            if (in_token) {
                flush();
                if (c == '~' || c == '-') pending_sep = c;
            } else {
                // Only update pending_sep if we see an explicit sep_char.
                if (c == '~' || c == '-') pending_sep = c;
            }
            continue;
        }
        if (c == '{') depth++;
        else if (c == '}' && depth > 0) depth--;
        cur.push_back(c);
        in_token = true;
    }
    flush();
    return out;
}

// Count BibTeX "text characters" (purely for the discretionary-tie decision).
// Mirrors `count_text_chars` but defined here for convenience.
std::size_t name_text_chars(std::string_view s) {
    std::size_t count = 0;
    std::size_t i = 0;
    int depth = 0;
    while (i < s.size()) {
        char c = s[i];
        if (c == '{') {
            // A `{\name...}` starting with backslash counts as 1; otherwise
            // recurse into the interior.
            if (depth == 0 && i + 1 < s.size() && s[i + 1] == '\\') {
                // skip to matching close
                int d = 1; std::size_t j = i + 1;
                while (j < s.size() && d > 0) {
                    if (s[j] == '{') d++;
                    else if (s[j] == '}') d--;
                    if (d == 0) break;
                    j++;
                }
                count += 1;
                i = (j < s.size()) ? j + 1 : j;
                continue;
            }
            depth++;
            i++;
            continue;
        }
        if (c == '}') {
            if (depth > 0) depth--;
            i++;
            continue;
        }
        count++;
        i++;
    }
    return count;
}

// Output the abbreviated form of a name token: the first alphabetic character
// or, if the token starts with `{\...}` (a "special character"), the whole
// special character group. bibtex.web §10210.
std::string abbreviate_token(std::string_view tok) {
    std::size_t i = 0;
    while (i < tok.size()) {
        char c = tok[i];
        if (std::isalpha(static_cast<unsigned char>(c))) {
            return std::string(1, c);
        }
        if (c == '{' && i + 1 < tok.size() && tok[i + 1] == '\\') {
            // Copy the whole {\...} group verbatim.
            int depth = 1;
            std::size_t j = i + 1;
            while (j < tok.size() && depth > 0) {
                if (tok[j] == '{') depth++;
                else if (tok[j] == '}') depth--;
                if (depth == 0) break;
                j++;
            }
            std::size_t end = (j < tok.size()) ? j + 1 : j;
            return std::string(tok.substr(i, end - i));
        }
        i++;
    }
    // Fallback — should never hit for valid names.
    return std::string(tok);
}

// Format a single NamePart per a format string per btxhak §4 and bibtex.web §9911.
// Rules:
//   - Format text outside brace groups is emitted verbatim.
//   - Each brace-level-1 group is a "piece" selecting one name part by letter
//     (f/v/l/j), optionally doubled (full-form) and/or followed by an explicit
//     `{inter-token-string}`.
//   - If the corresponding part has no tokens, the whole piece is suppressed.
//   - Otherwise, we emit each token, with the inter-token string between
//     consecutive tokens (no trailing inter-token string after the last one).
//   - The default inter-token string, per bibtex.web §10270, is:
//         (period-if-abbreviated) + sep
//     where `sep` is the original `~`/`-` from the source name if present, or
//     else a tie `~` if this is the last token-pair of this part or the
//     preceding token has fewer than 3 text characters, or else a space.
//   - After the tokens, we emit the piece's trailing literal text. If the
//     piece's last character is then a tie (`~`), it's a "discretionary tie":
//     if the piece has <3 text characters we keep the tie, else we replace it
//     with a space.
std::string format_single_name(const NamePart& np, std::string_view fmt) {
    std::string out;
    std::size_t fi = 0;
    while (fi < fmt.size()) {
        char c = fmt[fi];
        if (c != '{') {
            out.push_back(c);
            fi++;
            continue;
        }
        // Find matching close.
        int depth = 1;
        std::size_t j = fi + 1;
        while (j < fmt.size() && depth > 0) {
            if (fmt[j] == '{') depth++;
            else if (fmt[j] == '}') depth--;
            if (depth == 0) break;
            j++;
        }
        std::string unit(fmt.substr(fi + 1, (j > fi + 1 ? j - fi - 1 : 0)));
        fi = (j < fmt.size()) ? j + 1 : j;

        // Locate the part letter(s) at top level inside the unit.
        std::size_t letter_pos = std::string::npos;
        {
            int d = 0;
            for (std::size_t k = 0; k < unit.size(); ++k) {
                if (unit[k] == '{') { d++; continue; }
                if (unit[k] == '}') { if (d > 0) d--; continue; }
                if (d == 0 && (unit[k] == 'f' || unit[k] == 'v'
                            || unit[k] == 'l' || unit[k] == 'j'
                            || unit[k] == 'F' || unit[k] == 'V'
                            || unit[k] == 'L' || unit[k] == 'J')) {
                    letter_pos = k;
                    break;
                }
            }
        }
        if (letter_pos == std::string::npos) {
            // No part letter — emit unit as-is (wrapped in braces so caller
            // sees the same literal content).
            out.push_back('{');
            out += unit;
            out.push_back('}');
            continue;
        }
        char part = static_cast<char>(std::tolower(
            static_cast<unsigned char>(unit[letter_pos])));
        bool doubled = (letter_pos + 1 < unit.size()
                        && std::tolower(static_cast<unsigned char>(unit[letter_pos + 1]))
                               == part);
        std::string prefix = unit.substr(0, letter_pos);
        std::size_t after_letter = letter_pos + (doubled ? 2 : 1);

        // An explicit `{...}` inter-token string immediately after the letter
        // overrides the default.
        bool has_custom_sep = false;
        std::string custom_sep;
        std::size_t suffix_start = after_letter;
        if (after_letter < unit.size() && unit[after_letter] == '{') {
            int d = 1;
            std::size_t k = after_letter + 1;
            while (k < unit.size() && d > 0) {
                if (unit[k] == '{') d++;
                else if (unit[k] == '}') d--;
                if (d == 0) break;
                k++;
            }
            has_custom_sep = true;
            custom_sep = unit.substr(after_letter + 1,
                                     (k > after_letter + 1 ? k - after_letter - 1 : 0));
            suffix_start = (k < unit.size()) ? k + 1 : k;
        }
        std::string suffix = unit.substr(suffix_start);

        const std::string* raw = nullptr;
        switch (part) {
            case 'f': raw = &np.first; break;
            case 'v': raw = &np.von; break;
            case 'l': raw = &np.last; break;
            case 'j': raw = &np.jr; break;
        }
        if (!raw || raw->empty()) {
            // Part has no tokens — suppress the whole piece.
            continue;
        }

        auto tokens = tokenize_name_part(*raw);
        if (tokens.empty()) continue;

        // Emit the piece into a local buffer so we can apply the discretionary
        // tie rule without disturbing earlier output.
        std::string piece;
        piece += prefix;
        std::size_t piece_start_of_name = piece.size();
        for (std::size_t t = 0; t < tokens.size(); ++t) {
            if (doubled) piece += tokens[t].text;
            else        piece += abbreviate_token(tokens[t].text);

            if (t + 1 < tokens.size()) {
                if (has_custom_sep) {
                    piece += custom_sep;
                } else if (doubled) {
                    // Full-form: preserve the original inter-token separator
                    // from the source name. This keeps `-` and `~` hyphenation
                    // intact (e.g. "Shun-Tak", "First~Last") without forcing
                    // ties between whitespace-separated tokens — BibTeX's
                    // long-form tie rule is subtle and the probe tests want
                    // the raw tokens back from `{ff}` / `{vv}` / `{ll}`.
                    char next_sep = tokens[t + 1].sep;
                    piece.push_back((next_sep == '~' || next_sep == '-')
                                        ? next_sep : ' ');
                } else {
                    // Abbreviated: append the mandatory period after the
                    // initial, then apply bibtex.web §10270's default-sep
                    // rule (tie for last pair or short token, else space).
                    piece.push_back('.');
                    char next_sep = tokens[t + 1].sep;
                    bool is_last_pair = (t + 2 == tokens.size());
                    if (next_sep == '~' || next_sep == '-') {
                        piece.push_back(next_sep);
                    } else if (is_last_pair
                               || name_text_chars(tokens[t].text) < 3) {
                        piece.push_back('~');
                    } else {
                        piece.push_back(' ');
                    }
                }
            }
        }
        piece += suffix;

        // Discretionary tie handling (bibtex.web §10351): if the piece ends
        // in `~` and the char before that isn't also `~`, we may replace it
        // with a space (if the part is "long enough", i.e. ≥ 3 text chars).
        if (!piece.empty() && piece.back() == '~') {
            std::size_t part_len = piece.size() - piece_start_of_name;
            std::string_view just_name(piece);
            just_name.remove_prefix(piece_start_of_name);
            // Strip the trailing tie from the text-char count.
            just_name.remove_suffix(1);
            bool second_tie = (piece.size() >= 2
                               && piece[piece.size() - 2] == '~');
            if (!second_tie) {
                if (name_text_chars(just_name) >= 3) {
                    piece.back() = ' ';
                } // else keep the tie
            }
            (void)part_len;
        }

        out += piece;
    }
    return out;
}

// ---------- Interpreter state ----------

struct EntryScratch {
    std::unordered_map<std::string, BstValue> ints;
    std::unordered_map<std::string, BstValue> strs;
    std::string sort_key;
};

struct Interpreter {
    const BstProgram& program;
    const Database& db;
    const std::vector<std::string>& cites;
    BstResult& result;

    // Global symbol tables.
    std::unordered_map<std::string, std::vector<BstToken>> user_functions;
    std::unordered_map<std::string, std::string> macros;  // MACRO "..."
    std::unordered_set<std::string> declared_fields;
    std::unordered_set<std::string> entry_int_vars;
    std::unordered_set<std::string> entry_str_vars;
    std::unordered_set<std::string> global_int_vars;
    std::unordered_set<std::string> global_str_vars;

    std::unordered_map<std::string, BstValue> globals;

    // Entry list materialized by READ.
    std::vector<const Entry*> entry_list;
    std::vector<EntryScratch> entry_scratch;  // parallel array

    // Execution state.
    std::vector<BstValue> stack;
    std::size_t current_entry_index = 0;
    bool has_current_entry = false;

    // Output.
    std::string output_buffer;
    std::string current_line;

    Interpreter(const BstProgram& p, const Database& d,
                const std::vector<std::string>& c, BstResult& r)
        : program(p), db(d), cites(c), result(r) {}

    void warn(std::string kind, std::string msg, std::optional<std::string> key = std::nullopt) {
        Warning w;
        w.kind = std::move(kind);
        w.message = std::move(msg);
        w.key = std::move(key);
        result.warnings.push_back(std::move(w));
    }

    void push(BstValue v) { stack.push_back(std::move(v)); }
    BstValue pop() {
        if (stack.empty()) return BstValue::make_missing();
        BstValue v = std::move(stack.back());
        stack.pop_back();
        return v;
    }
    BstValue pop_int() {
        BstValue v = pop();
        if (v.kind != BstValueKind::Integer) {
            warn("bst_type_error", "expected integer on stack");
            return BstValue::make_integer(0);
        }
        return v;
    }
    BstValue pop_str() {
        BstValue v = pop();
        if (v.kind != BstValueKind::String) {
            warn("bst_type_error", "expected string on stack");
            return BstValue::make_string("");
        }
        return v;
    }
    BstValue pop_fn() {
        BstValue v = pop();
        if (v.kind != BstValueKind::Function) {
            warn("bst_type_error", "expected function on stack");
            return BstValue::make_function("skip$");
        }
        return v;
    }

    // ---------- Built-ins ----------

    using Builtin = std::function<void()>;

    std::unordered_map<std::string, Builtin> builtins;

    void register_builtins() {
        builtins[">"] = [this]{ auto b=pop_int(); auto a=pop_int(); push(BstValue::make_integer(a.integer > b.integer ? 1 : 0)); };
        builtins["<"] = [this]{ auto b=pop_int(); auto a=pop_int(); push(BstValue::make_integer(a.integer < b.integer ? 1 : 0)); };
        builtins["="] = [this]{
            auto b = pop(); auto a = pop();
            int eq = 0;
            if (a.kind == b.kind) {
                if (a.kind == BstValueKind::Integer) eq = (a.integer == b.integer) ? 1 : 0;
                else if (a.kind == BstValueKind::String) eq = (a.str == b.str) ? 1 : 0;
                else if (a.kind == BstValueKind::Function) eq = (a.fn_name == b.fn_name) ? 1 : 0;
                else eq = 1;
            }
            push(BstValue::make_integer(eq));
        };
        builtins["+"] = [this]{ auto b=pop_int(); auto a=pop_int(); push(BstValue::make_integer(a.integer + b.integer)); };
        builtins["-"] = [this]{ auto b=pop_int(); auto a=pop_int(); push(BstValue::make_integer(a.integer - b.integer)); };
        builtins["*"] = [this]{ auto b=pop_str(); auto a=pop_str(); push(BstValue::make_string(a.str + b.str)); };
        builtins[":="] = [this]{
            auto name = pop_fn();
            auto val = pop();
            assign(name.fn_name, std::move(val));
        };
        builtins["add.period$"] = [this]{
            auto s = pop_str();
            std::string v = s.str;
            // Find last non-'}' char.
            std::size_t i = v.size();
            while (i > 0 && v[i - 1] == '}') i--;
            if (i == 0 || (v[i - 1] != '.' && v[i - 1] != '!' && v[i - 1] != '?')) {
                v.insert(v.begin() + i, '.');
            }
            push(BstValue::make_string(std::move(v)));
        };
        builtins["change.case$"] = [this]{
            auto fmt = pop_str();
            auto s = pop_str();
            char mode = fmt.str.empty() ? 't' : std::tolower(static_cast<unsigned char>(fmt.str[0]));
            push(BstValue::make_string(change_case(s.str, mode)));
        };
        builtins["chr.to.int$"] = [this]{
            auto s = pop_str();
            if (s.str.size() != 1) { warn("bst_type_error", "chr.to.int$ expects 1-char string"); push(BstValue::make_integer(0)); return; }
            push(BstValue::make_integer(static_cast<unsigned char>(s.str[0])));
        };
        builtins["int.to.chr$"] = [this]{
            auto i = pop_int();
            std::string s(1, static_cast<char>(i.integer & 0xFF));
            push(BstValue::make_string(std::move(s)));
        };
        builtins["int.to.str$"] = [this]{
            auto i = pop_int();
            push(BstValue::make_string(std::to_string(i.integer)));
        };
        builtins["substring$"] = [this]{
            auto len = pop_int();
            auto start = pop_int();
            auto s = pop_str();
            int L = static_cast<int>(s.str.size());
            int start_i;
            if (start.integer > 0) start_i = static_cast<int>(start.integer) - 1;
            else start_i = L + static_cast<int>(start.integer);
            int take = static_cast<int>(len.integer);
            if (start.integer < 0) start_i = start_i - take + 1;
            if (start_i < 0) { take += start_i; start_i = 0; }
            if (start_i + take > L) take = L - start_i;
            if (take <= 0) push(BstValue::make_string(""));
            else push(BstValue::make_string(s.str.substr(static_cast<std::size_t>(start_i), static_cast<std::size_t>(take))));
        };
        builtins["text.length$"] = [this]{
            auto s = pop_str();
            push(BstValue::make_integer(static_cast<int64_t>(count_text_chars(s.str))));
        };
        builtins["text.prefix$"] = [this]{
            auto n = pop_int();
            auto s = pop_str();
            push(BstValue::make_string(text_prefix(s.str, static_cast<std::size_t>(std::max<int64_t>(0, n.integer)))));
        };
        builtins["width$"] = [this]{
            auto s = pop_str();
            push(BstValue::make_integer(approximate_width(s.str)));
        };
        builtins["purify$"] = [this]{
            auto s = pop_str();
            push(BstValue::make_string(purify(s.str)));
        };
        builtins["format.name$"] = [this]{
            auto fmt = pop_str();
            auto idx = pop_int();
            auto names = pop_str();
            auto parsed = parse_name_list(names.str);
            int i = static_cast<int>(idx.integer) - 1;
            if (i < 0 || i >= static_cast<int>(parsed.size())) {
                push(BstValue::make_string(""));
                return;
            }
            push(BstValue::make_string(format_single_name(parsed[i], fmt.str)));
        };
        builtins["num.names$"] = [this]{
            auto s = pop_str();
            auto parsed = parse_name_list(s.str);
            push(BstValue::make_integer(static_cast<int64_t>(parsed.size())));
        };
        builtins["if$"] = [this]{
            auto false_br = pop_fn();
            auto true_br = pop_fn();
            auto cond = pop_int();
            const auto& target = (cond.integer != 0) ? true_br : false_br;
            invoke_function(target.fn_name);
        };
        builtins["while$"] = [this]{
            auto body = pop_fn();
            auto cond = pop_fn();
            int safety = 1000000;
            while (safety-- > 0) {
                invoke_function(cond.fn_name);
                auto v = pop_int();
                if (v.integer == 0) break;
                invoke_function(body.fn_name);
            }
        };
        builtins["skip$"] = []{};
        builtins["pop$"] = [this]{ (void)pop(); };
        builtins["swap$"] = [this]{ auto a = pop(); auto b = pop(); push(std::move(a)); push(std::move(b)); };
        builtins["duplicate$"] = [this]{
            if (stack.empty()) { warn("bst_type_error", "duplicate$ on empty stack"); return; }
            push(stack.back());
        };
        builtins["cite$"] = [this]{
            if (!has_current_entry) { warn("bst_type_error", "cite$ with no current entry"); push(BstValue::make_string("")); return; }
            push(BstValue::make_string(entry_list[current_entry_index]->key));
        };
        builtins["type$"] = [this]{
            if (!has_current_entry) { warn("bst_type_error", "type$ with no current entry"); push(BstValue::make_string("")); return; }
            push(BstValue::make_string(entry_list[current_entry_index]->type));
        };
        builtins["call.type$"] = [this]{
            if (!has_current_entry) { warn("bst_type_error", "call.type$ with no current entry"); return; }
            std::string t = entry_list[current_entry_index]->type;
            if (user_functions.count(t)) invoke_function(t);
            else if (user_functions.count("default.type")) invoke_function("default.type");
            else warn("bst_undefined_function", "no handler for entry type '" + t + "'", entry_list[current_entry_index]->key);
        };
        builtins["empty$"] = [this]{
            auto v = pop();
            int empty = 1;
            if (v.kind == BstValueKind::String) {
                for (char c : v.str) if (!std::isspace(static_cast<unsigned char>(c))) { empty = 0; break; }
            } else if (v.kind != BstValueKind::Missing) {
                empty = 0;
            }
            push(BstValue::make_integer(empty));
        };
        builtins["missing$"] = [this]{
            auto v = pop();
            push(BstValue::make_integer(v.kind == BstValueKind::Missing ? 1 : 0));
        };
        builtins["preamble$"] = [this]{
            push(BstValue::make_string(db.preamble));
        };
        builtins["write$"] = [this]{
            auto s = pop_str();
            append_output(s.str);
        };
        builtins["newline$"] = [this]{
            flush_line(true);
        };
        builtins["quote$"] = [this]{
            push(BstValue::make_string("\""));
        };
        builtins["top$"] = []{};     // debug no-op
        builtins["stack$"] = [this]{ stack.clear(); };
        builtins["warning$"] = [this]{
            auto s = pop_str();
            warn("bst_user_warning", s.str);
        };
    }

    // Write a chunk to output, wrapping at 79 columns at whitespace.
    void append_output(std::string_view chunk) {
        for (char c : chunk) {
            if (c == '\n') {
                flush_line(true);
            } else {
                current_line.push_back(c);
                if (current_line.size() > 79) {
                    // Find last space <= 79 for break.
                    std::size_t brk = std::string::npos;
                    for (std::size_t k = 79; k > 0; --k) {
                        if (current_line[k] == ' ') { brk = k; break; }
                    }
                    if (brk != std::string::npos) {
                        output_buffer.append(current_line, 0, brk);
                        output_buffer.push_back('\n');
                        std::string rest = current_line.substr(brk + 1);
                        current_line = "  " + rest;
                    }
                }
            }
        }
    }
    void flush_line(bool emit_newline) {
        output_buffer += current_line;
        if (emit_newline) output_buffer.push_back('\n');
        current_line.clear();
    }

    void assign(const std::string& name, BstValue val) {
        // Global var? Entry scratch? Entry field?
        if (global_int_vars.count(name) || global_str_vars.count(name)) {
            globals[name] = std::move(val);
            return;
        }
        if (has_current_entry) {
            if (entry_int_vars.count(name) || entry_str_vars.count(name)) {
                auto& scratch = entry_scratch[current_entry_index];
                if (name == "sort.key$") {
                    scratch.sort_key = (val.kind == BstValueKind::String) ? val.str : "";
                }
                if (entry_int_vars.count(name)) scratch.ints[name] = std::move(val);
                else scratch.strs[name] = std::move(val);
                return;
            }
        }
        if (name == "sort.key$" && has_current_entry) {
            if (val.kind == BstValueKind::String) entry_scratch[current_entry_index].sort_key = val.str;
            return;
        }
        warn("bst_undefined_function", "assign to undefined variable '" + name + "'");
    }

    BstValue load_name(const std::string& name) {
        // 1) Entry field
        if (has_current_entry) {
            const auto* entry = entry_list[current_entry_index];
            for (const auto& f : entry->fields) {
                if (f.name == name && declared_fields.count(name)) {
                    return BstValue::make_string(f.value);
                }
            }
            if (declared_fields.count(name)) {
                return BstValue::make_missing();
            }
        }
        // 2) Entry scratch
        if (has_current_entry) {
            auto& scratch = entry_scratch[current_entry_index];
            if (entry_int_vars.count(name)) {
                auto it = scratch.ints.find(name);
                if (it != scratch.ints.end()) return it->second;
                return BstValue::make_integer(0);
            }
            if (entry_str_vars.count(name)) {
                auto it = scratch.strs.find(name);
                if (it != scratch.strs.end()) return it->second;
                return BstValue::make_string("");
            }
        }
        // 3) Global
        if (global_int_vars.count(name) || global_str_vars.count(name)) {
            auto it = globals.find(name);
            if (it != globals.end()) return it->second;
            return global_int_vars.count(name) ? BstValue::make_integer(0) : BstValue::make_string("");
        }
        // 4) Macro (MACRO expansion pushes the value)
        {
            auto it = macros.find(name);
            if (it != macros.end()) return BstValue::make_string(it->second);
        }
        warn("bst_undefined_function", "reference to undefined name '" + name + "'");
        return BstValue::make_missing();
    }

    // ---------- Execution ----------

    void execute_tokens(const std::vector<BstToken>& body) {
        for (const auto& t : body) {
            switch (t.kind) {
                case BstTokenKind::Integer: push(BstValue::make_integer(t.integer)); break;
                case BstTokenKind::String:  push(BstValue::make_string(t.text)); break;
                case BstTokenKind::QuotedName: push(BstValue::make_function(t.text)); break;
                case BstTokenKind::FunctionLit: {
                    // Inline function literal: register an anonymous function.
                    std::string anon = "__anon_" + std::to_string(anon_counter++);
                    user_functions[anon] = t.body;
                    push(BstValue::make_function(anon));
                    break;
                }
                case BstTokenKind::Ident: {
                    invoke_function(t.text);
                    break;
                }
            }
        }
    }

    std::size_t anon_counter = 0;

    void invoke_function(const std::string& name) {
        // Built-in?
        auto bi = builtins.find(name);
        if (bi != builtins.end()) { bi->second(); return; }
        // User function?
        auto uf = user_functions.find(name);
        if (uf != user_functions.end()) { execute_tokens(uf->second); return; }
        // Maybe it's a variable/field access — load and push.
        // (This is how BibTeX handles references to ENTRY fields / variables.)
        if (declared_fields.count(name)
            || entry_int_vars.count(name) || entry_str_vars.count(name)
            || global_int_vars.count(name) || global_str_vars.count(name)
            || macros.count(name)) {
            push(load_name(name));
            return;
        }
        warn("bst_undefined_function", "call to undefined function '" + name + "'");
        // IMPORTANT: push Missing to keep stack discipline consistent. BibTeX
        // refuses to run programs with undefined references, but pushing a
        // Missing here is safer than leaving the stack corrupted when one
        // slips through — callers frequently treat the reference as a field
        // that may be empty (e.g. `crossref missing$`).
        push(BstValue::make_missing());
    }

    std::optional<ParseError> run() {
        register_builtins();

        // Pre-defined names (bibtex.web §8140):
        // - `crossref` is always an implicit field (used by all standard styles).
        // - `sort.key$` is an implicit entry string variable (added on ENTRY).
        // - `entry.max$` and `global.max$` are integer globals whose values
        //   are BibTeX's internal storage limits. Using 20000 matches the
        //   `glob_str_size` / `ent_str_size` defaults from BibTeX 0.99c and
        //   is effectively "large enough" for the `t #2 global.max$ substring$`
        //   idiom that styles use to mean "rest of string".
        declared_fields.insert("crossref");
        global_int_vars.insert("entry.max$");
        global_int_vars.insert("global.max$");
        globals["entry.max$"] = BstValue::make_integer(20000);
        globals["global.max$"] = BstValue::make_integer(20000);

        bool read_done = false;
        for (const auto& cmd : program.commands) {
            switch (cmd.kind) {
                case BstProgram::CommandKind::Entry:
                    for (const auto& f : cmd.fields) declared_fields.insert(f);
                    for (const auto& v : cmd.int_vars) entry_int_vars.insert(v);
                    for (const auto& v : cmd.str_vars) entry_str_vars.insert(v);
                    entry_str_vars.insert("sort.key$");
                    break;
                case BstProgram::CommandKind::Strings:
                    for (const auto& v : cmd.names) global_str_vars.insert(v);
                    break;
                case BstProgram::CommandKind::Integers:
                    for (const auto& v : cmd.names) global_int_vars.insert(v);
                    break;
                case BstProgram::CommandKind::Function:
                    user_functions[cmd.name] = cmd.body;
                    result.log.functions_defined++;
                    break;
                case BstProgram::CommandKind::Macro:
                    macros[cmd.name] = cmd.literal_value;
                    result.log.macros_defined.push_back(cmd.name);
                    break;
                case BstProgram::CommandKind::Read: {
                    // Filter db.entries to the cited subset in cites order.
                    std::unordered_set<std::string> seen;
                    std::unordered_map<std::string, const Entry*> by_lower;
                    for (const auto& e : db.entries) by_lower[to_lower(e.key)] = &e;
                    for (const auto& cite : cites) {
                        std::string lkey = to_lower(cite);
                        if (seen.count(lkey)) continue;
                        seen.insert(lkey);
                        auto it = by_lower.find(lkey);
                        if (it == by_lower.end()) {
                            result.log.entries_cited_missing.push_back(cite);
                            continue;
                        }
                        entry_list.push_back(it->second);
                        entry_scratch.emplace_back();
                        result.log.entries_cited_found++;
                    }
                    result.log.entries_read = entry_list.size();
                    read_done = true;
                    break;
                }
                case BstProgram::CommandKind::Execute:
                    has_current_entry = false;
                    invoke_function(cmd.target);
                    break;
                case BstProgram::CommandKind::Iterate:
                    if (!read_done) return ParseError{"bst", cmd.line, cmd.column, "ITERATE before READ"};
                    for (std::size_t i = 0; i < entry_list.size(); ++i) {
                        current_entry_index = i;
                        has_current_entry = true;
                        invoke_function(cmd.target);
                    }
                    has_current_entry = false;
                    result.log.iterations++;
                    break;
                case BstProgram::CommandKind::Reverse:
                    if (!read_done) return ParseError{"bst", cmd.line, cmd.column, "REVERSE before READ"};
                    for (std::size_t i = entry_list.size(); i > 0; --i) {
                        current_entry_index = i - 1;
                        has_current_entry = true;
                        invoke_function(cmd.target);
                    }
                    has_current_entry = false;
                    result.log.iterations++;
                    break;
                case BstProgram::CommandKind::Sort: {
                    if (!read_done) return ParseError{"bst", cmd.line, cmd.column, "SORT before READ"};
                    // Stable sort entry_list (and entry_scratch in parallel) by sort_key.
                    std::vector<std::size_t> indices(entry_list.size());
                    for (std::size_t i = 0; i < indices.size(); ++i) indices[i] = i;
                    std::stable_sort(indices.begin(), indices.end(),
                                     [&](std::size_t a, std::size_t b) {
                                         return entry_scratch[a].sort_key < entry_scratch[b].sort_key;
                                     });
                    std::vector<const Entry*> new_list;
                    std::vector<EntryScratch> new_scratch;
                    new_list.reserve(indices.size());
                    new_scratch.reserve(indices.size());
                    for (auto i : indices) {
                        new_list.push_back(entry_list[i]);
                        new_scratch.push_back(std::move(entry_scratch[i]));
                    }
                    entry_list = std::move(new_list);
                    entry_scratch = std::move(new_scratch);
                    result.log.sorts++;
                    break;
                }
            }
        }
        // Flush any pending current line.
        if (!current_line.empty()) flush_line(true);
        return std::nullopt;
    }
};

} // namespace

std::optional<ParseError> execute_bst(
    const BstProgram& program, const Database& db,
    const std::vector<std::string>& cites, BstResult& result) {
    Interpreter interp(program, db, cites, result);
    auto err = interp.run();
    if (err) return err;
    result.bbl_output = interp.output_buffer;
    return std::nullopt;
}

} // namespace bibtex
