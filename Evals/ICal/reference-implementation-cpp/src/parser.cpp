#include "ical.hpp"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <set>
#include <sstream>
#include <string>
#include <unordered_map>

namespace ical {

namespace {

// --- Line unfolding (byte-based per RFC 5545 §3.1) ---

struct LineRecord {
    std::string text;
    std::size_t line_number{1};
    bool was_folded{false};  // true iff this logical line was assembled from >1 physical line
};

std::vector<LineRecord> unfold_lines(std::string_view src) {
    std::vector<LineRecord> out;
    std::string cur;
    std::size_t start_line = 1;
    std::size_t cur_line = 1;
    bool have_cur = false;
    bool cur_was_folded = false;
    auto flush = [&](std::size_t ln) {
        if (have_cur) {
            out.push_back(LineRecord{std::move(cur), start_line, cur_was_folded});
            cur.clear();
            have_cur = false;
            cur_was_folded = false;
        }
        start_line = ln;
    };
    std::size_t i = 0;
    while (i < src.size()) {
        std::size_t eol = i;
        while (eol < src.size() && src[eol] != '\n') eol++;
        std::string line_text(src.substr(i, eol - i));
        if (!line_text.empty() && line_text.back() == '\r') line_text.pop_back();
        bool is_continuation = have_cur && !line_text.empty()
                               && (line_text[0] == ' ' || line_text[0] == '\t');
        if (is_continuation) {
            cur += line_text.substr(1);
            cur_was_folded = true;
        } else {
            flush(cur_line);
            cur = line_text;
            start_line = cur_line;
            have_cur = true;
            cur_was_folded = false;
        }
        cur_line++;
        i = (eol < src.size()) ? eol + 1 : eol;
    }
    flush(cur_line);
    return out;
}

// --- RFC 6868 unescape (parameter values only) ---
// ^n -> LF, ^' -> ", ^^ -> ^, anything else kept literally
std::string rfc6868_unescape(std::string_view s) {
    std::string out;
    out.reserve(s.size());
    for (std::size_t i = 0; i < s.size(); ++i) {
        char c = s[i];
        if (c == '^' && i + 1 < s.size()) {
            char n = s[i + 1];
            if (n == 'n') { out.push_back('\n'); i++; continue; }
            if (n == '\'') { out.push_back('"'); i++; continue; }
            if (n == '^') { out.push_back('^'); i++; continue; }
            // Unknown ^X sequence: keep both literally.
            out.push_back('^');
            continue;
        }
        out.push_back(c);
    }
    return out;
}

std::optional<Property> parse_property_line(const std::string& line, std::size_t line_number) {
    std::size_t colon = std::string::npos;
    bool in_quote = false;
    for (std::size_t i = 0; i < line.size(); ++i) {
        char c = line[i];
        if (c == '"') in_quote = !in_quote;
        else if (c == ':' && !in_quote) { colon = i; break; }
    }
    if (colon == std::string::npos) return std::nullopt;

    std::string name_and_params = line.substr(0, colon);
    std::string value = line.substr(colon + 1);

    Property p;
    p.line = line_number;
    std::vector<std::string> segs;
    {
        std::string cur;
        bool iq = false;
        for (char c : name_and_params) {
            if (c == '"') { iq = !iq; cur.push_back(c); continue; }
            if (c == ';' && !iq) { segs.push_back(std::move(cur)); cur.clear(); continue; }
            cur.push_back(c);
        }
        segs.push_back(std::move(cur));
    }
    if (segs.empty()) return std::nullopt;
    p.name = to_upper(segs[0]);
    for (std::size_t i = 1; i < segs.size(); ++i) {
        const auto& s = segs[i];
        auto eq = s.find('=');
        if (eq == std::string::npos) {
            p.params[to_upper(s)] = "";
        } else {
            std::string key = to_upper(s.substr(0, eq));
            std::string val = s.substr(eq + 1);
            // Strip outer quotes if the value is a single quoted string.
            // Note: for multi-value params (e.g. MEMBER="a","b"), the full
            // quoted-list text is stored as-is; caller handles list splitting.
            if (val.size() >= 2 && val.front() == '"' && val.back() == '"'
                && val.find('"', 1) == val.size() - 1) {
                val = val.substr(1, val.size() - 2);
            }
            // RFC 6868 unescape on the decoded value.
            val = rfc6868_unescape(val);
            p.params[key] = val;
        }
    }
    p.value = value;
    return p;
}

// --- Quoted list split: "a","b",c -> ["a", "b", "c"] ---
// Splits at commas outside double-quotes, strips surrounding quotes, applies
// RFC 6868 unescape.
std::vector<std::string> split_quoted_list(std::string_view s) {
    std::vector<std::string> out;
    std::string cur;
    bool iq = false;
    for (std::size_t i = 0; i < s.size(); ++i) {
        char c = s[i];
        if (c == '"') { iq = !iq; cur.push_back(c); continue; }
        if (c == ',' && !iq) {
            out.push_back(std::move(cur));
            cur.clear();
            continue;
        }
        cur.push_back(c);
    }
    out.push_back(std::move(cur));
    // Strip surrounding quotes from each element and apply 6868 unescape.
    for (auto& elem : out) {
        if (elem.size() >= 2 && elem.front() == '"' && elem.back() == '"') {
            elem = elem.substr(1, elem.size() - 2);
        }
        elem = rfc6868_unescape(elem);
    }
    return out;
}

// Needed for params where we stored the raw (possibly quoted-list) string and
// want to re-split it.  Since `parse_property_line` already strips a single
// pair of outer quotes if the *entire* value is quoted, multi-element values
// keep their internal quotes and we can split here.
// But single-element quoted values will arrive stripped; that's fine, the
// split yields the single element.
std::vector<std::string> split_param_list(const std::string& raw) {
    // Re-split at commas outside quotes.
    return split_quoted_list(raw);
}

Freq parse_freq(std::string_view s) {
    std::string u = to_upper(s);
    if (u == "SECONDLY") return Freq::Secondly;
    if (u == "MINUTELY") return Freq::Minutely;
    if (u == "HOURLY") return Freq::Hourly;
    if (u == "DAILY") return Freq::Daily;
    if (u == "WEEKLY") return Freq::Weekly;
    if (u == "MONTHLY") return Freq::Monthly;
    if (u == "YEARLY") return Freq::Yearly;
    return Freq::Daily;
}

std::optional<Weekday> parse_weekday_abbrev(std::string_view s) {
    std::string u = to_upper(s);
    if (u == "SU") return Weekday::Sunday;
    if (u == "MO") return Weekday::Monday;
    if (u == "TU") return Weekday::Tuesday;
    if (u == "WE") return Weekday::Wednesday;
    if (u == "TH") return Weekday::Thursday;
    if (u == "FR") return Weekday::Friday;
    if (u == "SA") return Weekday::Saturday;
    return std::nullopt;
}

std::vector<std::string> split(std::string_view s, char sep) {
    std::vector<std::string> out;
    std::string cur;
    for (char c : s) {
        if (c == sep) { out.push_back(std::move(cur)); cur.clear(); }
        else cur.push_back(c);
    }
    out.push_back(std::move(cur));
    return out;
}

std::vector<int> parse_int_list(std::string_view s) {
    std::vector<int> out;
    for (const auto& tok : split(s, ',')) {
        try { out.push_back(std::stoi(tok)); } catch (...) {}
    }
    return out;
}

ByDayEntry parse_byday_entry(std::string_view s) {
    ByDayEntry e;
    std::size_t i = 0;
    int sign = 1;
    if (i < s.size() && (s[i] == '+' || s[i] == '-')) {
        if (s[i] == '-') sign = -1;
        i++;
    }
    std::size_t digit_start = i;
    while (i < s.size() && std::isdigit(static_cast<unsigned char>(s[i]))) i++;
    if (i > digit_start) {
        int v = 0;
        for (std::size_t k = digit_start; k < i; ++k) v = v * 10 + (s[k] - '0');
        e.ordinal = sign * v;
    }
    if (i + 2 == s.size()) {
        auto wd = parse_weekday_abbrev(s.substr(i));
        if (wd) e.weekday = *wd;
    }
    return e;
}

RRule parse_rrule(std::string_view value) {
    RRule r;
    for (const auto& part : split(value, ';')) {
        auto eq = part.find('=');
        if (eq == std::string::npos) continue;
        std::string key = to_upper(part.substr(0, eq));
        std::string v = part.substr(eq + 1);
        if (key == "FREQ") r.freq = parse_freq(v);
        else if (key == "INTERVAL") { try { r.interval = std::stoi(v); } catch (...) {} if (r.interval < 1) r.interval = 1; }
        else if (key == "COUNT") { try { r.count = std::stoi(v); } catch (...) {} }
        else if (key == "UNTIL") {
            r.until = parse_ical_datetime(v);
            if (!r.until) {
                if (auto d = parse_ical_date(v); d) r.until = DateTime{*d, 0, 0, 0, TimeKind::Floating, {}};
            }
        }
        else if (key == "BYMONTH") r.bymonth = parse_int_list(v);
        else if (key == "BYMONTHDAY") r.bymonthday = parse_int_list(v);
        else if (key == "BYDAY") {
            for (const auto& tok : split(v, ',')) r.byday.push_back(parse_byday_entry(tok));
        }
        else if (key == "BYSETPOS") r.bysetpos = parse_int_list(v);
        else if (key == "WKST") { if (auto wd = parse_weekday_abbrev(v); wd) r.wkst = *wd; }
        else if (key == "BYSECOND") r.bysecond = parse_int_list(v);
        else if (key == "BYMINUTE") r.byminute = parse_int_list(v);
        else if (key == "BYHOUR") r.byhour = parse_int_list(v);
        else if (key == "BYYEARDAY") r.byyearday = parse_int_list(v);
        else if (key == "BYWEEKNO") r.byweekno = parse_int_list(v);
        else if (key == "RSCALE") r.rscale = to_upper(v);
        else if (key == "SKIP") r.skip = to_upper(v);
    }
    return r;
}

std::optional<DateOrDateTime> parse_dodt(
    const std::string& raw, const std::map<std::string, std::string>& params,
    std::vector<Warning>& /*warnings*/, const std::string& /*uid*/) {
    DateOrDateTime out;
    auto tzid_it = params.find("TZID");
    if (tzid_it != params.end()) out.tzid = tzid_it->second;
    auto value_it = params.find("VALUE");
    bool is_date = (value_it != params.end() && to_upper(value_it->second) == "DATE");
    if (is_date || raw.size() == 8) {
        if (auto d = parse_ical_date(raw); d) { out.date = *d; return out; }
    }
    if (auto dt = parse_ical_datetime(raw); dt) {
        if (out.tzid) {
            dt->kind = TimeKind::Zoned;
            dt->tzid = *out.tzid;
        }
        out.datetime = *dt;
        return out;
    }
    return std::nullopt;
}

std::vector<DateOrDateTime> parse_date_list(
    const std::string& raw, const std::map<std::string, std::string>& params,
    std::vector<Warning>& warnings, const std::string& uid) {
    std::vector<DateOrDateTime> out;
    for (const auto& tok : split(raw, ',')) {
        if (auto d = parse_dodt(tok, params, warnings, uid); d) out.push_back(*d);
    }
    return out;
}

// Is `s` a valid ISO-8601 duration starting with P or -P / +P?
bool looks_like_duration(std::string_view s) {
    if (s.empty()) return false;
    std::size_t i = 0;
    if (s[i] == '+' || s[i] == '-') i++;
    if (i >= s.size() || s[i] != 'P') return false;
    return true;
}

// Parse one period-value token "start/end" or "start/duration" into Period.
// Returns nullopt on invalid input (caller emits malformed_value).
std::optional<Period> parse_period_token(
    std::string_view tok, const std::map<std::string, std::string>& params,
    std::vector<Warning>& warnings, const std::string& uid) {
    auto slash = tok.find('/');
    if (slash == std::string_view::npos) return std::nullopt;
    std::string left(tok.substr(0, slash));
    std::string right(tok.substr(slash + 1));
    // Build params without VALUE=PERIOD so parse_dodt treats the left/right
    // as DATE-TIME.
    std::map<std::string, std::string> dt_params;
    for (const auto& [k, v] : params) {
        if (k == "VALUE") continue;
        dt_params[k] = v;
    }
    auto start = parse_dodt(left, dt_params, warnings, uid);
    if (!start) return std::nullopt;
    Period p;
    p.start = *start;
    if (looks_like_duration(right)) {
        p.duration = right;
        return p;
    }
    auto endv = parse_dodt(right, dt_params, warnings, uid);
    if (!endv) return std::nullopt;
    // RFC 5545 §3.3.9: start MUST be before end.
    if (compare(*start, *endv) >= 0) {
        Warning w;
        w.kind = "malformed_value";
        w.message = "period end is not after start";
        if (!uid.empty()) w.uid = uid;
        w.value = std::string(tok);
        warnings.push_back(std::move(w));
        return std::nullopt;
    }
    p.end = *endv;
    return p;
}

// Parse an RDATE value into a list of RDateEntry. Entries may be plain
// DATE-TIMEs, DATE, or periods (when VALUE=PERIOD).
std::vector<RDateEntry> parse_rdate_list(
    const std::string& raw, const std::map<std::string, std::string>& params,
    std::vector<Warning>& warnings, const std::string& uid) {
    std::vector<RDateEntry> out;
    auto vit = params.find("VALUE");
    bool is_period = (vit != params.end() && to_upper(vit->second) == "PERIOD");
    for (const auto& tok : split(raw, ',')) {
        if (is_period) {
            if (auto p = parse_period_token(tok, params, warnings, uid); p) {
                RDateEntry e;
                e.period = *p;
                out.push_back(std::move(e));
            }
        } else {
            if (auto d = parse_dodt(tok, params, warnings, uid); d) {
                RDateEntry e;
                e.dt = *d;
                out.push_back(std::move(e));
            }
        }
    }
    return out;
}

std::string unescape_text(std::string_view s) {
    std::string out;
    out.reserve(s.size());
    for (std::size_t i = 0; i < s.size(); ++i) {
        char c = s[i];
        if (c == '\\' && i + 1 < s.size()) {
            char n = s[i + 1];
            if (n == '\\' || n == ';' || n == ',') { out.push_back(n); i++; continue; }
            if (n == 'n' || n == 'N') { out.push_back('\n'); i++; continue; }
        }
        out.push_back(c);
    }
    return out;
}

// --- Cal-address parsing (ATTENDEE / ORGANIZER) per RFC 5545 §3.2.* ---

CalAddress parse_cal_address(const Property& p) {
    CalAddress a;
    a.value = p.value;
    auto get = [&](const char* k) -> std::optional<std::string> {
        auto it = p.params.find(k);
        if (it == p.params.end()) return std::nullopt;
        return it->second;
    };
    if (auto v = get("CN"); v) a.cn = *v;
    if (auto v = get("CUTYPE"); v) a.cutype = *v;
    if (auto v = get("ROLE"); v) a.role = *v;
    if (auto v = get("PARTSTAT"); v) a.partstat = *v;
    if (auto v = get("RSVP"); v) {
        std::string up = to_upper(*v);
        if (up == "TRUE") a.rsvp = true;
        else if (up == "FALSE") a.rsvp = false;
    }
    if (auto v = get("MEMBER"); v) a.member = split_param_list(*v);
    if (auto v = get("DELEGATED-FROM"); v) a.delegated_from = split_param_list(*v);
    if (auto v = get("DELEGATED-TO"); v) a.delegated_to = split_param_list(*v);
    if (auto v = get("SENT-BY"); v) a.sent_by = *v;
    if (auto v = get("DIR"); v) a.dir = *v;
    if (auto v = get("LANGUAGE"); v) a.language = *v;
    return a;
}

// --- ATTACH parsing (text or binary attach URIs) ---

Attach parse_attach(const Property& p) {
    Attach a;
    a.value = p.value;
    auto fit = p.params.find("FMTTYPE"); if (fit != p.params.end()) a.fmttype = fit->second;
    auto eit = p.params.find("ENCODING"); if (eit != p.params.end()) a.encoding = eit->second;
    auto vit = p.params.find("VALUE"); if (vit != p.params.end()) a.value_type = vit->second;
    return a;
}

void apply_common_prop(VEvent& ev, const Property& p, Calendar& cal) {
    ev.raw_properties.push_back(p);
    if (p.name == "UID") ev.uid = p.value;
    else if (p.name == "DTSTAMP") ev.dtstamp = parse_ical_datetime(p.value);
    else if (p.name == "DTSTART") ev.dtstart = parse_dodt(p.value, p.params, cal.warnings, ev.uid);
    else if (p.name == "DTEND") ev.dtend = parse_dodt(p.value, p.params, cal.warnings, ev.uid);
    else if (p.name == "DURATION") ev.duration = p.value;
    else if (p.name == "SUMMARY") ev.summary = unescape_text(p.value);
    else if (p.name == "DESCRIPTION") ev.description = unescape_text(p.value);
    else if (p.name == "LOCATION") ev.location = unescape_text(p.value);
    else if (p.name == "STATUS") ev.status = p.value;
    else if (p.name == "CLASS") ev.class_ = p.value;
    else if (p.name == "RECURRENCE-ID") {
        ev.recurrence_id = parse_dodt(p.value, p.params, cal.warnings, ev.uid);
        auto rit = p.params.find("RANGE");
        if (rit != p.params.end()) ev.recurrence_id_range = rit->second;
    }
    else if (p.name == "RRULE") {
        ev.rrule = parse_rrule(p.value);
        // RFC 5545 §3.3.10: UNTIL and COUNT MUST NOT occur in the same
        // 'recur' part. We parse both (so the RRULE round-trips in the
        // raw JSON) but surface a malformed_value warning and let the
        // downstream expander apply whichever one fires first.
        if (ev.rrule->count.has_value() && ev.rrule->until.has_value()) {
            Warning w; w.kind = "malformed_value";
            w.message = "RRULE MUST NOT combine COUNT and UNTIL (RFC 5545 §3.3.10)";
            if (!ev.uid.empty()) w.uid = ev.uid;
            w.value = std::string(p.value);
            cal.warnings.push_back(std::move(w));
        }
        // RFC 7529: emit rscale_unsupported when RSCALE is non-Gregorian, or
        // when SKIP is present (we only support SKIP=OMIT which is the default
        // Gregorian behavior).
        if (ev.rrule->rscale.has_value()) {
            const std::string& rs = *ev.rrule->rscale;
            if (rs != "GREGORIAN") {
                Warning w; w.kind = "rscale_unsupported";
                w.message = "RSCALE=" + rs + " is not supported; RRULE preserved in raw_properties";
                if (!ev.uid.empty()) w.uid = ev.uid;
                w.value = rs;
                cal.warnings.push_back(std::move(w));
            } else if (ev.rrule->skip.has_value() && *ev.rrule->skip != "OMIT") {
                Warning w; w.kind = "rscale_unsupported";
                w.message = "RSCALE=GREGORIAN SKIP=" + *ev.rrule->skip
                          + " is not supported; RRULE preserved in raw_properties";
                if (!ev.uid.empty()) w.uid = ev.uid;
                w.value = *ev.rrule->skip;
                cal.warnings.push_back(std::move(w));
            }
        }
    }
    else if (p.name == "EXRULE") {
        ev.exrule = parse_rrule(p.value);
        Warning w; w.kind = "exrule_deprecated";
        w.message = "EXRULE is deprecated (RFC 5545 removed it); applied as subtractive filter";
        w.uid = ev.uid;
        cal.warnings.push_back(std::move(w));
    }
    else if (p.name == "RDATE") {
        auto ds = parse_rdate_list(p.value, p.params, cal.warnings, ev.uid);
        for (auto& d : ds) ev.rdate.push_back(std::move(d));
    }
    else if (p.name == "EXDATE") {
        auto ds = parse_date_list(p.value, p.params, cal.warnings, ev.uid);
        for (auto& d : ds) ev.exdate.push_back(std::move(d));
    }
    else if (p.name == "CATEGORIES") {
        for (const auto& c : split(p.value, ',')) ev.categories.push_back(unescape_text(c));
    }
    else if (p.name == "ORGANIZER") {
        ev.organizer = parse_cal_address(p);
    }
    else if (p.name == "ATTENDEE") {
        ev.attendees.push_back(parse_cal_address(p));
    }
    else if (p.name == "SEQUENCE") {
        try { ev.sequence = std::stoi(p.value); } catch (...) {}
    }
    // RFC 5545 fields previously promised by the schema but unmodeled:
    else if (p.name == "PRIORITY") {
        try { ev.priority = std::stoi(p.value); } catch (...) {}
    }
    else if (p.name == "TRANSP") ev.transp = p.value;
    else if (p.name == "URL") ev.url = p.value;
    else if (p.name == "GEO") {
        // Format: "lat;lon" — two floats separated by semicolon.
        auto semi = p.value.find(';');
        bool ok = false;
        if (semi != std::string::npos) {
            try {
                Geo g;
                g.lat = std::stod(p.value.substr(0, semi));
                g.lon = std::stod(p.value.substr(semi + 1));
                ev.geo = g;
                ok = true;
            } catch (...) {
                // Fall through to warning.
            }
        }
        if (!ok) {
            Warning w; w.kind = "malformed_value";
            w.message = "GEO value is not two floats separated by ';'";
            if (!ev.uid.empty()) w.uid = ev.uid;
            w.value = p.value;
            cal.warnings.push_back(std::move(w));
        }
    }
    else if (p.name == "RESOURCES") {
        for (const auto& r : split(p.value, ',')) ev.resources.push_back(unescape_text(r));
    }
    else if (p.name == "CONTACT") ev.contact = unescape_text(p.value);
    else if (p.name == "CREATED") {
        if (auto dt = parse_ical_datetime(p.value); dt) ev.created = iso_format(*dt);
    }
    else if (p.name == "LAST-MODIFIED") {
        if (auto dt = parse_ical_datetime(p.value); dt) ev.last_modified = iso_format(*dt);
    }
    else if (p.name == "ATTACH") ev.attachments.push_back(parse_attach(p));
    else if (p.name == "RELATED-TO") {              // RFC 5545 §3.8.4.5
        // Surface RELATED-TO on VEVENT / VTODO / VJOURNAL / VFREEBUSY
        // with the same {value, reltype} shape VALARM uses (§3.2.10.1).
        // RFC 9253 GAP is captured via raw_properties — structured GAP
        // surfacing is handled by the separate relationships test path.
        RelatedTo r;
        r.value = p.value;
        auto rit = p.params.find("RELTYPE");
        if (rit != p.params.end()) r.reltype = rit->second;
        ev.related_to.push_back(std::move(r));
    }
    // RFC 7986 on VEVENT:
    else if (p.name == "COLOR") ev.color = p.value;
    else if (p.name == "IMAGE") {
        ImageEntry img;
        img.value = p.value;
        auto f = p.params.find("FMTTYPE"); if (f != p.params.end()) img.fmttype = f->second;
        auto e = p.params.find("ENCODING"); if (e != p.params.end()) img.encoding = e->second;
        auto d = p.params.find("DISPLAY"); if (d != p.params.end()) img.display = d->second;
        ev.images.push_back(std::move(img));
    }
    else if (p.name == "CONFERENCE") {
        ConferenceEntry c;
        c.value = p.value;
        auto f = p.params.find("FEATURE"); if (f != p.params.end()) c.feature = f->second;
        auto l = p.params.find("LABEL"); if (l != p.params.end()) c.label = l->second;
        ev.conferences.push_back(std::move(c));
    }
}

// --- VALARM body parsing ---

void apply_alarm_prop(VAlarm& a, const Property& p, Calendar& cal) {
    a.raw_properties.push_back(p);
    if (p.name == "ACTION") a.action = p.value;
    else if (p.name == "TRIGGER") {
        Trigger t;
        auto vit = p.params.find("VALUE");
        bool is_datetime = (vit != p.params.end() && to_upper(vit->second) == "DATE-TIME");
        if (is_datetime) {
            // Absolute UTC datetime; normalize to ISO-8601 form.
            if (auto dt = parse_ical_datetime(p.value); dt) {
                t.value = iso_format(*dt);
            } else {
                t.value = p.value;
            }
            t.related = std::nullopt;  // MUST NOT have RELATED for absolute
        } else {
            // Duration-valued trigger.
            t.value = p.value;
            auto rit = p.params.find("RELATED");
            if (rit != p.params.end()) t.related = to_upper(rit->second);
            else t.related = std::string("START");
        }
        a.trigger = t;
    }
    else if (p.name == "DURATION") a.duration = p.value;
    else if (p.name == "REPEAT") {
        try { a.repeat = std::stoi(p.value); } catch (...) {}
    }
    else if (p.name == "ATTACH") a.attach.push_back(parse_attach(p));
    else if (p.name == "DESCRIPTION") a.description = unescape_text(p.value);
    else if (p.name == "SUMMARY") a.summary = unescape_text(p.value);
    else if (p.name == "ATTENDEE") a.attendees.push_back(parse_cal_address(p));
    else if (p.name == "ACKNOWLEDGED") {
        if (auto dt = parse_ical_datetime(p.value); dt) a.acknowledged = iso_format(*dt);
    }
    else if (p.name == "UID") a.uid = p.value;           // RFC 9074 §4
    else if (p.name == "PROXIMITY") a.proximity = p.value;  // RFC 9074 §8
    else if (p.name == "RELATED-TO") {                   // RFC 9074 §9
        RelatedTo r;
        r.value = p.value;
        auto rit = p.params.find("RELTYPE");
        if (rit != p.params.end()) r.reltype = rit->second;
        a.related_to.push_back(std::move(r));
    }
    (void)cal;
}

// --- iTIP method-specific validation (RFC 5546 §3.2) ---
// Emits `itip_missing_property` warnings on `cal` for any component that
// fails the METHOD's requirements.
void validate_itip(Calendar& cal) {
    if (!cal.method) return;
    std::string m = to_upper(*cal.method);

    auto emit = [&](const std::string& uid, const std::string& msg) {
        Warning w; w.kind = "itip_missing_property"; w.message = msg;
        if (!uid.empty()) w.uid = uid;
        cal.warnings.push_back(std::move(w));
    };

    // Per-method, per-component iTIP validation derived from the RFC 5546
    // constraint tables. Each of §3.2 (VEVENT) / §3.3 (VFREEBUSY) /
    // §3.4 (VTODO) / §3.5 (VJOURNAL) defines its own matrix. VJOURNAL and
    // VFREEBUSY support a strict subset of methods; invoking any other
    // method on them is an RFC violation and we warn.
    //
    // UID and DTSTAMP are "1" (required) in every table including PUBLISH.
    auto check_vevent = [&](const VEvent& e) {
        // VEVENT §3.2.x tables — enforced row-by-row for every "1"
        // (required) row. "0 or 1" rows are permitted-but-optional;
        // "0" rows are MUST NOT and we warn on presence.
        //
        // Messages start with the METHOD name so test message-content
        // discrimination works uniformly. (VEVENT rules don't include
        // "VEVENT" in the message text — VEVENT is the default
        // component per the warning-contract §.)
        if (e.uid.empty()) emit("", m + " requires UID");
        if (!e.dtstamp) emit(e.uid, m + " requires DTSTAMP");

        if (m == "PUBLISH") {
            // §3.2.1: DTSTART 1, ORGANIZER 1, SUMMARY 1, UID 1, DTSTAMP 1;
            // ATTENDEE 0 (MUST NOT). SEQUENCE is 0 or 1.
            if (!e.dtstart) emit(e.uid, "PUBLISH requires DTSTART");
            if (!e.organizer) emit(e.uid, "PUBLISH requires ORGANIZER");
            if (!e.summary) emit(e.uid, "PUBLISH requires SUMMARY");
            if (!e.attendees.empty()) emit(e.uid, "PUBLISH MUST NOT include ATTENDEE");
        } else if (m == "REQUEST") {
            // §3.2.2: ATTENDEE 1+, DTSTAMP 1, DTSTART 1, ORGANIZER 1,
            // SUMMARY 1, UID 1. SEQUENCE 0 or 1.
            if (!e.dtstart) emit(e.uid, "REQUEST requires DTSTART");
            if (!e.organizer) emit(e.uid, "REQUEST requires ORGANIZER");
            if (!e.summary) emit(e.uid, "REQUEST requires SUMMARY");
            if (e.attendees.empty()) emit(e.uid, "REQUEST requires ATTENDEE");
        } else if (m == "REPLY") {
            // §3.2.3: ATTENDEE 1 (w/ PARTSTAT), DTSTAMP 1, ORGANIZER 1,
            // UID 1. DTSTART/SUMMARY/etc. are 0 or 1 (optional).
            if (!e.organizer) emit(e.uid, "REPLY requires ORGANIZER");
            if (e.attendees.empty()) {
                emit(e.uid, "REPLY requires ATTENDEE");
            } else {
                bool any_partstat = false;
                for (const auto& a : e.attendees) {
                    if (a.partstat) { any_partstat = true; break; }
                }
                if (!any_partstat) emit(e.uid, "REPLY attendee requires PARTSTAT");
            }
        } else if (m == "ADD") {
            // §3.2.4: DTSTAMP 1, DTSTART 1, ORGANIZER 1, SEQUENCE 1 (>0),
            // SUMMARY 1, UID 1.
            if (!e.dtstart) emit(e.uid, "ADD requires DTSTART");
            if (!e.organizer) emit(e.uid, "ADD requires ORGANIZER");
            if (!e.summary) emit(e.uid, "ADD requires SUMMARY");
            if (!e.sequence) emit(e.uid, "ADD requires SEQUENCE");
            else if (*e.sequence == 0) emit(e.uid, "ADD requires SEQUENCE greater than 0");
        } else if (m == "CANCEL") {
            // §3.2.5: ATTENDEE 0+ (the Organizer may target Attendees to
            // uninvite but it is not required), DTSTAMP 1, ORGANIZER 1,
            // SEQUENCE 1, UID 1. STATUS is 0 or 1; when present on a
            // whole-event cancel, MUST be CANCELLED. The prose of §3.2.5
            // allows METHOD:CANCEL alone to convey cancellation, so we
            // do not warn on STATUS absence.
            if (!e.organizer) emit(e.uid, "CANCEL requires ORGANIZER");
            if (!e.sequence) emit(e.uid, "CANCEL requires SEQUENCE");
            if (e.status) {
                std::string upper_status = to_upper(*e.status);
                if (upper_status != "CANCELLED") {
                    emit(e.uid, "CANCEL STATUS must be CANCELLED");
                }
            }
        } else if (m == "REFRESH") {
            // §3.2.6: ATTENDEE 1, DTSTAMP 1, ORGANIZER 1, UID 1.
            // SEQUENCE 0 — MUST NOT be present.
            if (!e.organizer) emit(e.uid, "REFRESH requires ORGANIZER");
            if (e.attendees.empty()) emit(e.uid, "REFRESH requires ATTENDEE");
            if (e.sequence) emit(e.uid, "REFRESH MUST NOT include SEQUENCE");
        } else if (m == "COUNTER") {
            // §3.2.7: DTSTAMP 1, DTSTART 1, ORGANIZER 1, SEQUENCE 1,
            // SUMMARY 1, UID 1. ATTENDEE 0+ (optional — may propose others).
            if (!e.dtstart) emit(e.uid, "COUNTER requires DTSTART");
            if (!e.organizer) emit(e.uid, "COUNTER requires ORGANIZER");
            if (!e.summary) emit(e.uid, "COUNTER requires SUMMARY");
            if (!e.sequence) emit(e.uid, "COUNTER requires SEQUENCE");
        } else if (m == "DECLINECOUNTER") {
            // §3.2.8: ATTENDEE 1+, DTSTAMP 1, ORGANIZER 1, SEQUENCE 1, UID 1.
            if (!e.organizer) emit(e.uid, "DECLINECOUNTER requires ORGANIZER");
            if (e.attendees.empty()) emit(e.uid, "DECLINECOUNTER requires ATTENDEE");
            if (!e.sequence) emit(e.uid, "DECLINECOUNTER requires SEQUENCE");
        }
    };

    auto check_vtodo = [&](const VEvent& t) {
        // VTODO §3.4.x tables — enforced row-by-row for every "1" row.
        // Differs from VEVENT: PRIORITY is required on PUBLISH/REQUEST/
        // ADD/COUNTER; REFRESH does NOT forbid SEQUENCE (§3.4.6 is 0 or 1,
        // not 0 MUST NOT); DUE replaces DTEND in many tables.
        //
        // All emitted messages start with the adjacent phrase
        // "<METHOD> VTODO" to satisfy the warning-contract adjacency
        // rule for non-VEVENT itip_missing_property warnings.
        if (t.uid.empty()) emit("", m + " VTODO requires UID");
        if (!t.dtstamp) emit(t.uid, m + " VTODO requires DTSTAMP");

        if (m == "PUBLISH") {
            // §3.4.1: DTSTART 1, ORGANIZER 1, PRIORITY 1, SUMMARY 1,
            // UID 1; ATTENDEE 0 (MUST NOT).
            if (!t.dtstart) emit(t.uid, "PUBLISH VTODO requires DTSTART");
            if (!t.organizer) emit(t.uid, "PUBLISH VTODO requires ORGANIZER");
            if (!t.priority) emit(t.uid, "PUBLISH VTODO requires PRIORITY");
            if (!t.summary) emit(t.uid, "PUBLISH VTODO requires SUMMARY");
            if (!t.attendees.empty()) emit(t.uid, "PUBLISH VTODO MUST NOT include ATTENDEE");
        } else if (m == "REQUEST") {
            // §3.4.2: ATTENDEE 1+, DTSTART 1, ORGANIZER 1, PRIORITY 1,
            // SUMMARY 1. SEQUENCE 0 or 1.
            if (!t.dtstart) emit(t.uid, "REQUEST VTODO requires DTSTART");
            if (!t.organizer) emit(t.uid, "REQUEST VTODO requires ORGANIZER");
            if (!t.priority) emit(t.uid, "REQUEST VTODO requires PRIORITY");
            if (!t.summary) emit(t.uid, "REQUEST VTODO requires SUMMARY");
            if (t.attendees.empty()) emit(t.uid, "REQUEST VTODO requires ATTENDEE");
        } else if (m == "REPLY") {
            // §3.4.3: ATTENDEE 1+ (w/ PARTSTAT), ORGANIZER 1, UID 1,
            // DTSTAMP 1. DTSTART/SUMMARY/PRIORITY are 0 or 1.
            if (!t.organizer) emit(t.uid, "REPLY VTODO requires ORGANIZER");
            if (t.attendees.empty()) {
                emit(t.uid, "REPLY VTODO requires ATTENDEE");
            } else {
                bool any_partstat = false;
                for (const auto& a : t.attendees) {
                    if (a.partstat) { any_partstat = true; break; }
                }
                if (!any_partstat) emit(t.uid, "REPLY VTODO attendee requires PARTSTAT");
            }
        } else if (m == "ADD") {
            // §3.4.4: ORGANIZER 1, PRIORITY 1, SEQUENCE 1 (>0), SUMMARY 1.
            if (!t.organizer) emit(t.uid, "ADD VTODO requires ORGANIZER");
            if (!t.priority) emit(t.uid, "ADD VTODO requires PRIORITY");
            if (!t.summary) emit(t.uid, "ADD VTODO requires SUMMARY");
            if (!t.sequence) emit(t.uid, "ADD VTODO requires SEQUENCE");
            else if (*t.sequence == 0) emit(t.uid, "ADD VTODO requires SEQUENCE greater than 0");
        } else if (m == "CANCEL") {
            // §3.4.5: ORGANIZER 1, SEQUENCE 1, UID 1, DTSTAMP 1.
            if (!t.organizer) emit(t.uid, "CANCEL VTODO requires ORGANIZER");
            if (!t.sequence) emit(t.uid, "CANCEL VTODO requires SEQUENCE");
            if (t.status && to_upper(*t.status) != "CANCELLED") {
                emit(t.uid, "CANCEL VTODO STATUS must be CANCELLED");
            }
        } else if (m == "REFRESH") {
            // §3.4.6: ATTENDEE 1, ORGANIZER 1. SEQUENCE is "0 or 1"
            // (optional) — UNLIKE VEVENT REFRESH which forbids SEQUENCE.
            if (!t.organizer) emit(t.uid, "REFRESH VTODO requires ORGANIZER");
            if (t.attendees.empty()) emit(t.uid, "REFRESH VTODO requires ATTENDEE");
        } else if (m == "COUNTER") {
            // §3.4.7: ATTENDEE 1+, ORGANIZER 1, PRIORITY 1, SEQUENCE 0 or 1,
            // SUMMARY 1.
            if (!t.organizer) emit(t.uid, "COUNTER VTODO requires ORGANIZER");
            if (t.attendees.empty()) emit(t.uid, "COUNTER VTODO requires ATTENDEE");
            if (!t.priority) emit(t.uid, "COUNTER VTODO requires PRIORITY");
            if (!t.summary) emit(t.uid, "COUNTER VTODO requires SUMMARY");
        } else if (m == "DECLINECOUNTER") {
            // §3.4.8: ATTENDEE 1+, ORGANIZER 1, SEQUENCE 0 or 1.
            if (!t.organizer) emit(t.uid, "DECLINECOUNTER VTODO requires ORGANIZER");
            if (t.attendees.empty()) emit(t.uid, "DECLINECOUNTER VTODO requires ATTENDEE");
        }
    };

    auto check_vjournal = [&](const VEvent& j) {
        // VJOURNAL §3.5 only defines PUBLISH / ADD / CANCEL. Any other
        // method on a VJOURNAL is an RFC 5546 violation.
        //
        // All emitted messages start with "<METHOD> VJOURNAL" to satisfy
        // the warning-contract adjacency rule for non-VEVENT messages.
        if (j.uid.empty()) emit("", m + " VJOURNAL requires UID");
        if (!j.dtstamp) emit(j.uid, m + " VJOURNAL requires DTSTAMP");

        if (m == "PUBLISH") {
            // §3.5.1: DESCRIPTION 1, DTSTART 1, ORGANIZER 1, UID 1,
            // DTSTAMP 1; ATTENDEE 0 (MUST NOT).
            if (!j.description) emit(j.uid, "PUBLISH VJOURNAL requires DESCRIPTION");
            if (!j.dtstart) emit(j.uid, "PUBLISH VJOURNAL requires DTSTART");
            if (!j.organizer) emit(j.uid, "PUBLISH VJOURNAL requires ORGANIZER");
            if (!j.attendees.empty()) emit(j.uid, "PUBLISH VJOURNAL MUST NOT include ATTENDEE");
        } else if (m == "ADD") {
            // §3.5.2: DESCRIPTION 1, DTSTAMP 1, DTSTART 1, ORGANIZER 1,
            // SEQUENCE 1 (MUST > 0), UID 1; ATTENDEE 0.
            if (!j.description) emit(j.uid, "ADD VJOURNAL requires DESCRIPTION");
            if (!j.dtstart) emit(j.uid, "ADD VJOURNAL requires DTSTART");
            if (!j.organizer) emit(j.uid, "ADD VJOURNAL requires ORGANIZER");
            if (!j.sequence) emit(j.uid, "ADD VJOURNAL requires SEQUENCE");
            else if (*j.sequence == 0) emit(j.uid, "ADD VJOURNAL requires SEQUENCE greater than 0");
        } else if (m == "CANCEL") {
            // §3.5.3: DTSTAMP 1, ORGANIZER 1, SEQUENCE 1, UID 1.
            // RECURRENCE-ID scope (whole-series vs instance) is context-
            // dependent and enforced downstream via orphan_override
            // detection — not at iTIP validation time.
            if (!j.organizer) emit(j.uid, "CANCEL VJOURNAL requires ORGANIZER");
            if (!j.sequence) emit(j.uid, "CANCEL VJOURNAL requires SEQUENCE");
            if (j.status && to_upper(*j.status) != "CANCELLED") {
                emit(j.uid, "CANCEL VJOURNAL STATUS must be CANCELLED");
            }
        } else {
            emit(j.uid, "METHOD " + m + " not defined for VJOURNAL (RFC 5546 §3.5)");
        }
    };

    auto check_vfreebusy = [&](const VFreeBusy& f) {
        // VFREEBUSY §3.3 only defines PUBLISH / REQUEST / REPLY.
        //
        // All emitted messages start with "<METHOD> VFREEBUSY" to satisfy
        // the warning-contract adjacency rule for non-VEVENT messages.
        // Even shared checks (UID/DTSTAMP/ORGANIZER/DTSTART/DTEND) carry
        // the method+component prefix so tests that discriminate by
        // message content can always rely on the adjacent phrase.
        if (f.uid.empty()) emit("", m + " VFREEBUSY requires UID");
        if (!f.dtstamp) emit(f.uid, m + " VFREEBUSY requires DTSTAMP");
        // All three §3.3.x tables require DTSTART, DTEND, and ORGANIZER.
        if (!f.organizer) emit(f.uid, m + " VFREEBUSY requires ORGANIZER");
        if (!f.dtstart) emit(f.uid, m + " VFREEBUSY requires DTSTART");
        if (!f.dtend) emit(f.uid, m + " VFREEBUSY requires DTEND");

        if (m == "PUBLISH") {
            // §3.3.1: ATTENDEE 0.
            if (!f.attendees.empty()) emit(f.uid, "PUBLISH VFREEBUSY MUST NOT include ATTENDEE");
        } else if (m == "REQUEST") {
            // §3.3.2: ATTENDEE 1+.
            if (f.attendees.empty()) emit(f.uid, "REQUEST VFREEBUSY requires ATTENDEE");
        } else if (m == "REPLY") {
            // §3.3.3: ATTENDEE 1+.
            if (f.attendees.empty()) emit(f.uid, "REPLY VFREEBUSY requires ATTENDEE");
        } else {
            emit(f.uid, "METHOD " + m + " not defined for VFREEBUSY (RFC 5546 §3.3)");
        }
    };

    for (const auto& e : cal.events) check_vevent(e);
    for (const auto& t : cal.todos) check_vtodo(t);
    for (const auto& j : cal.journals) check_vjournal(j);
    for (const auto& f : cal.freebusy) check_vfreebusy(f);
}

// Parse-time orphan override detection: each override event (one with
// RECURRENCE-ID) must have a base event (same UID without RECURRENCE-ID) whose
// recurrence set contains the override's recurrence-id value.
// Detect multiple base (non-override) events with the same UID and emit
// `duplicate_uid` warnings per RFC 5545 §3.8.4.7. Overrides (events with
// RECURRENCE-ID) are expected to share UID with their base, so we only
// flag duplicates among non-override events.
void validate_duplicate_uids(Calendar& cal) {
    std::unordered_map<std::string, int> seen;
    for (const auto& e : cal.events) {
        if (e.recurrence_id.has_value()) continue;
        if (e.uid.empty()) continue;
        seen[e.uid]++;
    }
    for (const auto& [uid, count] : seen) {
        if (count > 1) {
            Warning w; w.kind = "duplicate_uid";
            w.message = "UID '" + uid + "' is used by " + std::to_string(count)
                      + " non-override events";
            w.uid = uid;
            cal.warnings.push_back(std::move(w));
        }
    }
}

// Core orphan-override check — factored so we can apply it to
// `events` / `todos` / `journals` uniformly. Takes a list by reference
// and the container's warning sink.
void validate_orphan_overrides_in(
    const std::vector<VEvent>& components, Calendar& cal
) {
    std::unordered_map<std::string, const VEvent*> base_by_uid;
    for (const auto& e : components) {
        if (!e.recurrence_id.has_value()) base_by_uid[e.uid] = &e;
    }
    for (const auto& e : components) {
        if (!e.recurrence_id.has_value()) continue;
        auto it = base_by_uid.find(e.uid);
        if (it == base_by_uid.end()) continue;  // no base; harness handles this elsewhere
        const VEvent* base = it->second;
        if (!base->dtstart) continue;
        DateTime base_seed;
        if (base->dtstart->datetime) base_seed = *base->dtstart->datetime;
        else if (base->dtstart->date) base_seed = DateTime{*base->dtstart->date, 0, 0, 0, TimeKind::Floating, {}};
        DateTime rid_dt;
        if (e.recurrence_id->datetime) rid_dt = *e.recurrence_id->datetime;
        else if (e.recurrence_id->date) rid_dt = DateTime{*e.recurrence_id->date, 0, 0, 0, TimeKind::Floating, {}};
        // If there's no RRULE, the only valid RID is the base DTSTART.
        if (!base->rrule.has_value()) {
            if (compare_datetime(base_seed, rid_dt) != 0) {
                // Check RDATE list.
                bool hit = false;
                for (const auto& rd : base->rdate) {
                    if (rd.dt) {
                        DateTime d;
                        if (rd.dt->datetime) d = *rd.dt->datetime;
                        else if (rd.dt->date) d = DateTime{*rd.dt->date, 0, 0, 0, TimeKind::Floating, {}};
                        if (compare_datetime(d, rid_dt) == 0) { hit = true; break; }
                    } else if (rd.period) {
                        DateTime d;
                        if (rd.period->start.datetime) d = *rd.period->start.datetime;
                        else if (rd.period->start.date) d = DateTime{*rd.period->start.date, 0, 0, 0, TimeKind::Floating, {}};
                        if (compare_datetime(d, rid_dt) == 0) { hit = true; break; }
                    }
                }
                if (!hit) {
                    Warning w; w.kind = "orphan_override";
                    w.message = "RECURRENCE-ID value does not match any base occurrence";
                    w.uid = e.uid;
                    cal.warnings.push_back(std::move(w));
                }
            }
            continue;
        }
        // Skip orphan check when RSCALE is non-Gregorian (unsupported).
        if (base->rrule->rscale.has_value() && *base->rrule->rscale != "GREGORIAN") continue;
        if (!rrule_contains_target(base_seed, *base->rrule, base->rdate, rid_dt)) {
            Warning w; w.kind = "orphan_override";
            w.message = "RECURRENCE-ID value does not match any base occurrence";
            w.uid = e.uid;
            cal.warnings.push_back(std::move(w));
        }
    }
}

void validate_orphan_overrides(Calendar& cal) {
    // Apply to every top-level recurring-component container. RFC 5545
    // §3.8.4.4 RECURRENCE-ID semantics are identical across VEVENT /
    // VTODO / VJOURNAL; scoping the check to events-only silently
    // accepts broken VTODO / VJOURNAL overrides.
    validate_orphan_overrides_in(cal.events, cal);
    // VTodo inherits from VEvent; slice to a VEvent view via a copy.
    std::vector<VEvent> todo_view(cal.todos.begin(), cal.todos.end());
    validate_orphan_overrides_in(todo_view, cal);
    std::vector<VEvent> journal_view(cal.journals.begin(), cal.journals.end());
    validate_orphan_overrides_in(journal_view, cal);
}

} // namespace

std::optional<ParseError> parse_ics(std::string_view source, Calendar& cal) {
    auto lines = unfold_lines(source);

    std::vector<std::string> stack;
    VEvent cur_event;
    VTodo cur_todo;
    VJournal cur_journal;
    VFreeBusy cur_freebusy;
    VTimezone cur_tz;
    Observance cur_obs;
    VAlarm cur_alarm;
    VAvailability cur_availability;
    Available cur_available;
    bool in_vevent = false, in_vtodo = false, in_vjournal = false, in_vfreebusy = false;
    bool in_vtimezone = false, in_observance = false;
    bool in_valarm = false;
    bool in_vavailability = false, in_available = false;
    int skip_depth = 0;  // >0 when inside an unknown sub-component; skip property dispatch
    std::string observance_kind;  // "STANDARD" or "DAYLIGHT"
    // Pointer to the currently-"open" component's alarm list; null if none.
    std::vector<VAlarm>* cur_alarm_owner = nullptr;

    for (const auto& ln : lines) {
        if (ln.text.empty()) continue;
        // RFC 5545 §3.1: "Lines of text SHOULD NOT be longer than 75 octets".
        // After unfolding, if a logical line is still > 75 octets and was
        // NOT split via fold in the source, emit line_too_long.
        // Unfolded `ln.text` here is the post-unfold length; but we only
        // warn when the ORIGINAL line (pre-fold) was >75 AND it was not
        // folded. We approximate this by warning on any unfolded line > 75
        // octets — per-fold is not easily distinguishable post-unfold.
        // A more precise check is to detect whether the logical line was
        // actually split across multiple physical lines (the unfold record
        // doesn't carry that). We warn on output length > 75 as the
        // pragmatic proxy.
        if (ln.text.size() > 75 && !ln.was_folded) {
            Warning w; w.kind = "line_too_long";
            w.message = "content line exceeds 75 octets";
            w.line = ln.line_number;
            cal.warnings.push_back(std::move(w));
        }
        auto pp = parse_property_line(ln.text, ln.line_number);
        if (!pp) return ParseError{ln.line_number, 1, "malformed content line: " + ln.text};
        const Property& p = *pp;

        if (p.name == "BEGIN") {
            std::string name = to_upper(p.value);
            // If we are already inside an unsupported sub-component, treat any
            // nested BEGIN as another unsupported level — do NOT open a
            // known component inside garbage, because its parent is already
            // dropped and the body would silently attach to the wrong scope.
            if (skip_depth > 0) {
                stack.push_back(name);
                skip_depth++;
                continue;
            }
            if (name == "VCALENDAR") {
                stack.push_back(name);
            } else if (stack.empty()) {
                return ParseError{ln.line_number, 1, "BEGIN:" + name + " outside VCALENDAR"};
            } else if (name == "VEVENT") {
                cur_event = VEvent{};
                in_vevent = true;
                cur_alarm_owner = &cur_event.alarms;
                stack.push_back(name);
            } else if (name == "VTODO") {
                cur_todo = VTodo{};
                in_vtodo = true;
                cur_alarm_owner = &cur_todo.alarms;
                stack.push_back(name);
            } else if (name == "VJOURNAL") {
                cur_journal = VJournal{};
                in_vjournal = true;
                stack.push_back(name);
            } else if (name == "VFREEBUSY") {
                cur_freebusy = VFreeBusy{};
                in_vfreebusy = true;
                stack.push_back(name);
            } else if (name == "VAVAILABILITY") {
                cur_availability = VAvailability{};
                in_vavailability = true;
                stack.push_back(name);
            } else if (in_vavailability && name == "AVAILABLE") {
                cur_available = Available{};
                in_available = true;
                stack.push_back(name);
            } else if (name == "VTIMEZONE") {
                cur_tz = VTimezone{};
                in_vtimezone = true;
                stack.push_back(name);
            } else if (in_vtimezone && (name == "STANDARD" || name == "DAYLIGHT")) {
                cur_obs = Observance{};
                observance_kind = name;
                in_observance = true;
                stack.push_back(name);
            } else if ((in_vevent || in_vtodo) && name == "VALARM") {
                cur_alarm = VAlarm{};
                in_valarm = true;
                stack.push_back(name);
            } else {
                // Unknown sub-component — skip all properties until matching END.
                stack.push_back(name);
                skip_depth++;
                Warning w; w.kind = "unsupported_component";
                w.message = "unrecognized component: " + name;
                cal.warnings.push_back(std::move(w));
            }
            continue;
        }
        if (p.name == "END") {
            std::string name = to_upper(p.value);
            if (stack.empty() || stack.back() != name) {
                return ParseError{ln.line_number, 1, "END:" + name + " without matching BEGIN"};
            }
            stack.pop_back();
            // While we are inside an unsupported sub-component, every BEGIN is
            // treated as another unsupported level (see BEGIN dispatch above).
            // Mirror that here: every END decrements skip_depth until we
            // unwind back to the known scope.
            if (skip_depth > 0) {
                skip_depth--;
                continue;
            }
            if (name == "VALARM") {
                in_valarm = false;
                // RFC 5545 §3.6.6: ACTION + TRIGGER are REQUIRED.
                if (!cur_alarm.action || !cur_alarm.trigger) {
                    Warning w;
                    w.kind = "malformed_value";
                    w.message = "VALARM missing required ACTION or TRIGGER";
                    cal.warnings.push_back(std::move(w));
                } else {
                    if (cur_alarm_owner) cur_alarm_owner->push_back(std::move(cur_alarm));
                }
                cur_alarm = VAlarm{};
            }
            else if (name == "VEVENT") {
                in_vevent = false;
                cur_alarm_owner = nullptr;
                cal.events.push_back(std::move(cur_event));
                cur_event = VEvent{};
            }
            else if (name == "VTODO") {
                in_vtodo = false;
                cur_alarm_owner = nullptr;
                cal.todos.push_back(std::move(cur_todo));
                cur_todo = VTodo{};
            }
            else if (name == "VJOURNAL") { in_vjournal = false; cal.journals.push_back(std::move(cur_journal)); cur_journal = VJournal{}; }
            else if (name == "VFREEBUSY") { in_vfreebusy = false; cal.freebusy.push_back(std::move(cur_freebusy)); cur_freebusy = VFreeBusy{}; }
            else if (name == "VTIMEZONE") { in_vtimezone = false; cal.timezones.push_back(std::move(cur_tz)); cur_tz = VTimezone{}; }
            else if (name == "STANDARD" || name == "DAYLIGHT") {
                in_observance = false;
                if (name == "STANDARD") cur_tz.standard.push_back(std::move(cur_obs));
                else cur_tz.daylight.push_back(std::move(cur_obs));
                cur_obs = Observance{};
            }
            else if (name == "VAVAILABILITY") {
                in_vavailability = false;
                cal.availabilities.push_back(std::move(cur_availability));
                cur_availability = VAvailability{};
            }
            else if (name == "AVAILABLE") {
                in_available = false;
                cur_availability.available.push_back(std::move(cur_available));
                cur_available = Available{};
            }
            continue;
        }

        // Inside an unknown sub-component (PARTICIPANT, VLOCATION, VRESOURCE,
        // or anything else we don't model): skip property dispatch so the
        // parent component's fields aren't clobbered.
        if (skip_depth > 0) continue;

        // Inside VALARM
        if (in_valarm) {
            apply_alarm_prop(cur_alarm, p, cal);
            continue;
        }

        // Inside AVAILABLE sub-component (RFC 7953 §3.2)
        if (in_available) {
            cur_available.raw_properties.push_back(p);
            if (p.name == "UID") cur_available.uid = p.value;
            else if (p.name == "DTSTAMP") cur_available.dtstamp = parse_ical_datetime(p.value);
            else if (p.name == "DTSTART") cur_available.dtstart = parse_dodt(p.value, p.params, cal.warnings, cur_available.uid);
            else if (p.name == "DTEND") cur_available.dtend = parse_dodt(p.value, p.params, cal.warnings, cur_available.uid);
            else if (p.name == "DURATION") cur_available.duration = p.value;
            else if (p.name == "SUMMARY") cur_available.summary = unescape_text(p.value);
            else if (p.name == "DESCRIPTION") cur_available.description = unescape_text(p.value);
            else if (p.name == "LOCATION") cur_available.location = unescape_text(p.value);
            else if (p.name == "CONTACT") cur_available.contact = unescape_text(p.value);
            else if (p.name == "CREATED") {
                if (auto dt = parse_ical_datetime(p.value); dt) cur_available.created = iso_format(*dt);
            }
            else if (p.name == "LAST-MODIFIED") {
                if (auto dt = parse_ical_datetime(p.value); dt) cur_available.last_modified = iso_format(*dt);
            }
            else if (p.name == "RECURRENCE-ID") {
                // Per RFC 7953 §3.2, AVAILABLE overrides follow the normal
                // RFC 5545 §3.8.4.4 RECURRENCE-ID semantics, including the
                // optional RANGE=THISANDFUTURE parameter (§3.2.11). TZID is
                // captured inside the DateOrDateTime by parse_dodt.
                cur_available.recurrence_id = parse_dodt(p.value, p.params, cal.warnings, cur_available.uid);
                auto rit = p.params.find("RANGE");
                if (rit != p.params.end()) cur_available.recurrence_id_range = rit->second;
            }
            else if (p.name == "CATEGORIES") {
                for (const auto& c : split(p.value, ',')) {
                    cur_available.categories.push_back(unescape_text(c));
                }
            }
            else if (p.name == "COMMENT") cur_available.comment.push_back(unescape_text(p.value));
            else if (p.name == "RRULE") cur_available.rrule = parse_rrule(p.value);
            else if (p.name == "RDATE") {
                auto ds = parse_rdate_list(p.value, p.params, cal.warnings, cur_available.uid);
                for (auto& d : ds) cur_available.rdate.push_back(std::move(d));
            }
            else if (p.name == "EXDATE") {
                auto ds = parse_date_list(p.value, p.params, cal.warnings, cur_available.uid);
                for (auto& d : ds) cur_available.exdate.push_back(std::move(d));
            }
            continue;
        }

        // Inside VAVAILABILITY (but not inside AVAILABLE)
        if (in_vavailability) {
            cur_availability.raw_properties.push_back(p);
            if (p.name == "UID") cur_availability.uid = p.value;
            else if (p.name == "DTSTAMP") cur_availability.dtstamp = parse_ical_datetime(p.value);
            else if (p.name == "DTSTART") cur_availability.dtstart = parse_dodt(p.value, p.params, cal.warnings, cur_availability.uid);
            else if (p.name == "DTEND") cur_availability.dtend = parse_dodt(p.value, p.params, cal.warnings, cur_availability.uid);
            else if (p.name == "DURATION") cur_availability.duration = p.value;
            else if (p.name == "SUMMARY") cur_availability.summary = unescape_text(p.value);
            else if (p.name == "DESCRIPTION") cur_availability.description = unescape_text(p.value);
            else if (p.name == "BUSYTYPE") cur_availability.busytype = p.value;
            else if (p.name == "PRIORITY") {
                try { cur_availability.priority = std::stoi(p.value); } catch (...) {}
            }
            else if (p.name == "ORGANIZER") cur_availability.organizer = parse_cal_address(p);
            continue;
        }

        // Top-level VCALENDAR properties
        if (stack.size() == 1 && stack.back() == "VCALENDAR") {
            if (p.name == "PRODID") cal.prodid = p.value;
            else if (p.name == "VERSION") cal.version = p.value;
            else if (p.name == "CALSCALE") cal.calscale = p.value;
            else if (p.name == "METHOD") cal.method = to_upper(p.value);
            // RFC 7986 §5 calendar-level properties
            else if (p.name == "NAME") cal.name = unescape_text(p.value);
            else if (p.name == "DESCRIPTION") cal.description = unescape_text(p.value);
            else if (p.name == "REFRESH-INTERVAL") cal.refresh_interval = p.value;
            else if (p.name == "SOURCE") cal.source = p.value;
            else if (p.name == "COLOR") cal.color = p.value;
            else if (p.name == "URL") cal.url = p.value;
            else if (p.name == "CATEGORIES") {
                for (const auto& c : split(p.value, ',')) cal.categories.push_back(unescape_text(c));
            }
            else if (p.name == "IMAGE") {
                ImageEntry img;
                img.value = p.value;
                auto fit = p.params.find("FMTTYPE");
                if (fit != p.params.end()) img.fmttype = fit->second;
                auto eit = p.params.find("ENCODING");
                if (eit != p.params.end()) img.encoding = eit->second;
                auto dit = p.params.find("DISPLAY");
                if (dit != p.params.end()) img.display = dit->second;
                cal.images.push_back(std::move(img));
            }
            else if (p.name == "CONFERENCE") {
                ConferenceEntry conf;
                conf.value = p.value;
                auto feit = p.params.find("FEATURE");
                if (feit != p.params.end()) conf.feature = feit->second;
                auto lit = p.params.find("LABEL");
                if (lit != p.params.end()) conf.label = unescape_text(lit->second);
                cal.conferences.push_back(std::move(conf));
            }
            continue;
        }

        // VTIMEZONE-level properties
        if (in_vtimezone && !in_observance) {
            if (p.name == "TZID") cur_tz.tzid = p.value;
            else if (p.name == "LAST-MODIFIED") {
                if (auto dt = parse_ical_datetime(p.value); dt) cur_tz.last_modified = iso_format(*dt);
            }
            else if (p.name == "TZURL") cur_tz.tzurl = p.value;
            else if (p.name == "COMMENT") cur_tz.comment.push_back(unescape_text(p.value));
            continue;
        }

        // Inside STANDARD/DAYLIGHT observance
        if (in_observance) {
            if (p.name == "DTSTART") {
                // RFC 5545 §3.8.2.4: observance DTSTART is always floating local time.
                if (auto dt = parse_ical_datetime(p.value); dt) {
                    dt->kind = TimeKind::Floating;
                    dt->tzid.clear();
                    cur_obs.dtstart = *dt;
                }
            }
            else if (p.name == "TZOFFSETFROM") cur_obs.tzoffsetfrom = p.value;
            else if (p.name == "TZOFFSETTO") cur_obs.tzoffsetto = p.value;
            else if (p.name == "TZNAME") cur_obs.tzname = p.value;
            else if (p.name == "RRULE") cur_obs.rrule = parse_rrule(p.value);
            else if (p.name == "RDATE") {
                auto ds = parse_rdate_list(p.value, p.params, cal.warnings, std::string{});
                for (auto& d : ds) cur_obs.rdate.push_back(std::move(d));
            }
            continue;
        }

        // Dispatch to the active top-level sub-component.
        if (in_vevent) apply_common_prop(cur_event, p, cal);
        else if (in_vtodo) {
            apply_common_prop(cur_todo, p, cal);
            if (p.name == "DUE") cur_todo.due = parse_dodt(p.value, p.params, cal.warnings, cur_todo.uid);
            else if (p.name == "COMPLETED") cur_todo.completed = parse_dodt(p.value, p.params, cal.warnings, cur_todo.uid);
            else if (p.name == "PERCENT-COMPLETE") {
                try { cur_todo.percent_complete = std::stoi(p.value); } catch (...) {}
            }
        }
        else if (in_vjournal) apply_common_prop(cur_journal, p, cal);
        else if (in_vfreebusy) {
            apply_common_prop(cur_freebusy, p, cal);
            if (p.name == "FREEBUSY") {
                FreeBusyEntry entry;
                auto fbit = p.params.find("FBTYPE");
                if (fbit != p.params.end()) entry.fbtype = fbit->second;
                // Split comma-separated periods at the top level.
                std::string buf;
                for (char c : p.value) {
                    if (c == ',') {
                        if (!buf.empty()) {
                            if (auto pp = parse_period_token(
                                    buf, p.params, cal.warnings, cur_freebusy.uid);
                                pp) {
                                entry.periods.push_back(*pp);
                            }
                            buf.clear();
                        }
                    } else {
                        buf.push_back(c);
                    }
                }
                if (!buf.empty()) {
                    if (auto pp = parse_period_token(
                            buf, p.params, cal.warnings, cur_freebusy.uid);
                        pp) {
                        entry.periods.push_back(*pp);
                    }
                }
                cur_freebusy.freebusy_entries.push_back(std::move(entry));
            }
        }
    }

    if (!stack.empty()) {
        return ParseError{lines.empty() ? 1 : lines.back().line_number, 1,
                          "unclosed component: " + stack.back()};
    }

    // Sort observances by DTSTART (each kind independently) for downstream
    // active-from semantics.
    for (auto& tz : cal.timezones) {
        auto cmp = [](const Observance& a, const Observance& b) {
            return compare_datetime(a.dtstart, b.dtstart) < 0;
        };
        std::sort(tz.standard.begin(), tz.standard.end(), cmp);
        std::sort(tz.daylight.begin(), tz.daylight.end(), cmp);
    }

    // iTIP validation (METHOD-specific checks).
    validate_itip(cal);

    // Orphan override detection.
    validate_orphan_overrides(cal);

    // Duplicate UID detection.
    validate_duplicate_uids(cal);

    return std::nullopt;
}

} // namespace ical
