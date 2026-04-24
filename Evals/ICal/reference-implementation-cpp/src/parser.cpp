#include "ical.hpp"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <sstream>
#include <string>
#include <unordered_map>

namespace ical {

namespace {

// --- Line unfolding (byte-based per RFC 5545 §3.1) ---

struct LineRecord { std::string text; std::size_t line_number{1}; };

std::vector<LineRecord> unfold_lines(std::string_view src) {
    std::vector<LineRecord> out;
    std::string cur;
    std::size_t start_line = 1;
    std::size_t cur_line = 1;
    bool have_cur = false;
    auto flush = [&](std::size_t ln) {
        if (have_cur) {
            out.push_back(LineRecord{std::move(cur), start_line});
            cur.clear();
            have_cur = false;
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
        } else {
            flush(cur_line);
            cur = line_text;
            start_line = cur_line;
            have_cur = true;
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

    auto check_event = [&](const VEvent& e) {
        if (m == "REQUEST") {
            if (!e.organizer) emit(e.uid, "REQUEST requires ORGANIZER");
        } else if (m == "REPLY") {
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
        } else if (m == "CANCEL") {
            if (!e.organizer) emit(e.uid, "CANCEL requires ORGANIZER");
        } else if (m == "ADD") {
            if (!e.organizer) emit(e.uid, "ADD requires ORGANIZER");
        } else if (m == "REFRESH") {
            if (!e.organizer) emit(e.uid, "REFRESH requires ORGANIZER");
            if (e.attendees.empty()) emit(e.uid, "REFRESH requires ATTENDEE");
        } else if (m == "COUNTER") {
            if (!e.organizer) emit(e.uid, "COUNTER requires ORGANIZER");
            if (e.attendees.empty()) emit(e.uid, "COUNTER requires ATTENDEE");
        } else if (m == "DECLINECOUNTER") {
            if (!e.organizer) emit(e.uid, "DECLINECOUNTER requires ORGANIZER");
        }
        // PUBLISH imposes no attendee-level iTIP requirement beyond the base.
    };

    for (const auto& e : cal.events) check_event(e);
    for (const auto& t : cal.todos) check_event(t);
    for (const auto& j : cal.journals) check_event(j);
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

void validate_orphan_overrides(Calendar& cal) {
    // Index base events by UID.
    std::unordered_map<std::string, const VEvent*> base_by_uid;
    for (const auto& e : cal.events) {
        if (!e.recurrence_id.has_value()) base_by_uid[e.uid] = &e;
    }
    for (const auto& e : cal.events) {
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
    bool in_vevent = false, in_vtodo = false, in_vjournal = false, in_vfreebusy = false;
    bool in_vtimezone = false, in_observance = false;
    bool in_valarm = false;
    std::string observance_kind;  // "STANDARD" or "DAYLIGHT"
    // Pointer to the currently-"open" component's alarm list; null if none.
    std::vector<VAlarm>* cur_alarm_owner = nullptr;

    for (const auto& ln : lines) {
        if (ln.text.empty()) continue;
        auto pp = parse_property_line(ln.text, ln.line_number);
        if (!pp) return ParseError{ln.line_number, 1, "malformed content line: " + ln.text};
        const Property& p = *pp;

        if (p.name == "BEGIN") {
            std::string name = to_upper(p.value);
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
                // Unknown sub-component — skip until matching END.
                stack.push_back(name);
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
            continue;
        }

        // Inside VALARM
        if (in_valarm) {
            apply_alarm_prop(cur_alarm, p, cal);
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
