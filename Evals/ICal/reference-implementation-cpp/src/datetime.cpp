#include "ical.hpp"

#include <cctype>
#include <cstdio>
#include <string>

namespace ical {

bool is_leap_year(int year) {
    return (year % 4 == 0 && year % 100 != 0) || (year % 400 == 0);
}

int days_in_month(int year, int month) {
    static constexpr int DAYS[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    if (month < 1 || month > 12) return 0;
    if (month == 2 && is_leap_year(year)) return 29;
    return DAYS[month - 1];
}

static long long days_since_epoch(const Date& d) {
    long long y = d.year;
    long long m = d.month;
    if (m <= 2) { y -= 1; m += 12; }
    long long era = (y >= 0 ? y : y - 399) / 400;
    long long yoe = y - era * 400;
    long long doy = (153 * (m - 3) + 2) / 5 + d.day - 1;
    long long doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    return era * 146097 + doe - 719468;
}

static Date date_from_days(long long days) {
    days += 719468;
    long long era = (days >= 0 ? days : days - 146096) / 146097;
    long long doe = days - era * 146097;
    long long yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    long long y = yoe + era * 400;
    long long doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    long long mp = (5 * doy + 2) / 153;
    long long d = doy - (153 * mp + 2) / 5 + 1;
    long long m = mp < 10 ? mp + 3 : mp - 9;
    if (m <= 2) y += 1;
    return Date{static_cast<int>(y), static_cast<int>(m), static_cast<int>(d)};
}

Weekday weekday_of(const Date& d) {
    long long days = days_since_epoch(d);
    long long w = ((days % 7) + 7 + 4) % 7;
    return static_cast<Weekday>(w);
}

Date add_days(const Date& d, int n) {
    return date_from_days(days_since_epoch(d) + n);
}

Date add_months(const Date& d, int n) {
    int m = d.month + n;
    int y = d.year + (m - 1) / 12;
    int mm = ((m - 1) % 12 + 12) % 12 + 1;
    if (m <= 0 && mm != 12) y -= 1;
    int dim = days_in_month(y, mm);
    int dd = d.day < dim ? d.day : dim;
    return Date{y, mm, dd};
}

Date add_years(const Date& d, int n) {
    int y = d.year + n;
    int dim = days_in_month(y, d.month);
    int dd = d.day < dim ? d.day : dim;
    return Date{y, d.month, dd};
}

DateTime add_seconds(const DateTime& dt, long long n) {
    long long total_secs = dt.second + dt.minute * 60LL + dt.hour * 3600LL + n;
    long long day_delta = 0;
    long long secs_in_day = 24LL * 3600;
    if (total_secs >= 0) {
        day_delta = total_secs / secs_in_day;
        total_secs %= secs_in_day;
    } else {
        day_delta = -((-total_secs + secs_in_day - 1) / secs_in_day);
        total_secs -= day_delta * secs_in_day;
    }
    DateTime out;
    out.date = add_days(dt.date, static_cast<int>(day_delta));
    out.hour = static_cast<int>(total_secs / 3600);
    out.minute = static_cast<int>((total_secs % 3600) / 60);
    out.second = static_cast<int>(total_secs % 60);
    out.kind = dt.kind;
    out.tzid = dt.tzid;
    return out;
}

static bool parse_uint(std::string_view s, std::size_t start, std::size_t len, int& out) {
    if (start + len > s.size()) return false;
    int v = 0;
    for (std::size_t i = 0; i < len; ++i) {
        char c = s[start + i];
        if (c < '0' || c > '9') return false;
        v = v * 10 + (c - '0');
    }
    out = v;
    return true;
}

std::optional<Date> parse_ical_date(std::string_view s) {
    if (s.size() != 8) return std::nullopt;
    Date d;
    if (!parse_uint(s, 0, 4, d.year)) return std::nullopt;
    if (!parse_uint(s, 4, 2, d.month)) return std::nullopt;
    if (!parse_uint(s, 6, 2, d.day)) return std::nullopt;
    if (d.month < 1 || d.month > 12) return std::nullopt;
    if (d.day < 1 || d.day > days_in_month(d.year, d.month)) return std::nullopt;
    return d;
}

std::optional<DateTime> parse_ical_datetime(std::string_view s) {
    if (s.size() != 15 && s.size() != 16) return std::nullopt;
    if (s[8] != 'T') return std::nullopt;
    if (s.size() == 16 && s[15] != 'Z') return std::nullopt;
    DateTime dt;
    auto date_opt = parse_ical_date(s.substr(0, 8));
    if (!date_opt) return std::nullopt;
    dt.date = *date_opt;
    if (!parse_uint(s, 9, 2, dt.hour)) return std::nullopt;
    if (!parse_uint(s, 11, 2, dt.minute)) return std::nullopt;
    if (!parse_uint(s, 13, 2, dt.second)) return std::nullopt;
    if (dt.hour > 23 || dt.minute > 59 || dt.second > 60) return std::nullopt;
    dt.kind = (s.size() == 16) ? TimeKind::Utc : TimeKind::Floating;
    return dt;
}

std::optional<DateTime> parse_iso_datetime(std::string_view s) {
    if (s.size() != 19 && s.size() != 20) return std::nullopt;
    if (s[4] != '-' || s[7] != '-' || s[10] != 'T' || s[13] != ':' || s[16] != ':') return std::nullopt;
    if (s.size() == 20 && s[19] != 'Z') return std::nullopt;
    DateTime dt;
    if (!parse_uint(s, 0, 4, dt.date.year)) return std::nullopt;
    if (!parse_uint(s, 5, 2, dt.date.month)) return std::nullopt;
    if (!parse_uint(s, 8, 2, dt.date.day)) return std::nullopt;
    if (!parse_uint(s, 11, 2, dt.hour)) return std::nullopt;
    if (!parse_uint(s, 14, 2, dt.minute)) return std::nullopt;
    if (!parse_uint(s, 17, 2, dt.second)) return std::nullopt;
    if (dt.date.month < 1 || dt.date.month > 12) return std::nullopt;
    if (dt.date.day < 1 || dt.date.day > days_in_month(dt.date.year, dt.date.month)) return std::nullopt;
    if (dt.hour > 23 || dt.minute > 59 || dt.second > 60) return std::nullopt;
    dt.kind = (s.size() == 20) ? TimeKind::Utc : TimeKind::Floating;
    return dt;
}

std::string iso_format(const Date& d) {
    char buf[16];
    std::snprintf(buf, sizeof(buf), "%04d-%02d-%02d", d.year, d.month, d.day);
    return buf;
}

std::string iso_format(const DateTime& dt) {
    char buf[32];
    std::snprintf(buf, sizeof(buf), "%04d-%02d-%02dT%02d:%02d:%02d%s",
                  dt.date.year, dt.date.month, dt.date.day,
                  dt.hour, dt.minute, dt.second,
                  dt.kind == TimeKind::Utc ? "Z" : "");
    return buf;
}

std::string iso_format(const DateOrDateTime& d) {
    if (d.date) return iso_format(*d.date);
    if (d.datetime) return iso_format(*d.datetime);
    return "";
}

int compare_datetime(const DateTime& a, const DateTime& b) {
    if (a.date != b.date) return a.date < b.date ? -1 : 1;
    if (a.hour != b.hour) return a.hour < b.hour ? -1 : 1;
    if (a.minute != b.minute) return a.minute < b.minute ? -1 : 1;
    if (a.second != b.second) return a.second < b.second ? -1 : 1;
    return 0;
}

int compare(const DateOrDateTime& a, const DateOrDateTime& b) {
    Date ad = a.date ? *a.date : a.datetime->date;
    Date bd = b.date ? *b.date : b.datetime->date;
    if (ad < bd) return -1;
    if (ad > bd) return 1;
    if (a.datetime && b.datetime) {
        return compare_datetime(*a.datetime, *b.datetime);
    }
    if (a.date && b.date) return 0;
    if (a.datetime) return 1;
    return -1;
}

std::string to_upper(std::string_view s) {
    std::string out;
    out.reserve(s.size());
    for (char c : s) {
        out.push_back(static_cast<char>(std::toupper(static_cast<unsigned char>(c))));
    }
    return out;
}

std::optional<int> parse_utc_offset(std::string_view s) {
    // ±HHMM or ±HHMMSS
    if (s.size() != 5 && s.size() != 7) return std::nullopt;
    int sign = (s[0] == '-') ? -1 : (s[0] == '+' ? 1 : 0);
    if (sign == 0) return std::nullopt;
    int hh = 0, mm = 0, ss = 0;
    if (!parse_uint(s, 1, 2, hh)) return std::nullopt;
    if (!parse_uint(s, 3, 2, mm)) return std::nullopt;
    if (s.size() == 7) { if (!parse_uint(s, 5, 2, ss)) return std::nullopt; }
    return sign * (hh * 3600 + mm * 60 + ss);
}

std::string format_utc_offset(int seconds) {
    int abs_s = seconds < 0 ? -seconds : seconds;
    int hh = abs_s / 3600;
    int mm = (abs_s % 3600) / 60;
    int ss = abs_s % 60;
    char buf[16];
    if (ss != 0) {
        // RFC 5545 §3.3.14: UTC-OFFSET permits an optional SECOND field.
        // Preserve the precision of the source TZOFFSET* value when the
        // on-wire form carried seconds (e.g. pre-1972 historical zones).
        std::snprintf(buf, sizeof(buf), "%c%02d:%02d:%02d",
                      seconds < 0 ? '-' : '+', hh, mm, ss);
    } else {
        std::snprintf(buf, sizeof(buf), "%c%02d:%02d",
                      seconds < 0 ? '-' : '+', hh, mm);
    }
    return buf;
}

// TZID resolution: find the observance active at `local`, apply its TZOFFSETTO
// to convert local → UTC.
std::optional<DateTime> resolve_zoned_to_utc(
    const DateTime& local, const std::string& tzid, const Calendar& cal) {
    const VTimezone* tz = nullptr;
    for (const auto& t : cal.timezones) {
        if (t.tzid == tzid) { tz = &t; break; }
    }
    if (!tz) return std::nullopt;

    // Enumerate all transition instances (DTSTART + RRULE expansions + RDATE entries)
    // from each observance, pick the latest whose effective start is <= local.
    auto enumerate_observance = [](const Observance& obs, const DateTime& up_to_local)
        -> std::vector<DateTime> {
        std::vector<DateTime> out;
        // Always include DTSTART.
        if (!obs.rrule) {
            out.push_back(obs.dtstart);
        }
        // Add any RDATE entries (treated as additional transition instants).
        for (const auto& rd : obs.rdate) {
            if (rd.dt && rd.dt->datetime) out.push_back(*rd.dt->datetime);
            else if (rd.dt && rd.dt->date) {
                out.push_back(DateTime{*rd.dt->date, 0, 0, 0, TimeKind::Floating, {}});
            }
        }
        if (!obs.rrule) return out;
        const RRule& r = *obs.rrule;
        DateTime cur = obs.dtstart;
        int safety = 10000;
        int interval = std::max(1, r.interval);
        while (safety-- > 0) {
            if (compare_datetime(cur, up_to_local) > 0) break;
            // Honor UNTIL: if cur > until, stop (cur is not valid).
            if (r.until && compare_datetime(cur, *r.until) > 0) break;
            out.push_back(cur);
            // Advance one interval.
            DateTime next;
            switch (r.freq) {
                case Freq::Yearly:
                    next = cur;
                    next.date = add_years(cur.date, interval);
                    break;
                case Freq::Monthly:
                    next = cur;
                    next.date = add_months(cur.date, interval);
                    break;
                case Freq::Weekly:
                    next = cur;
                    next.date = add_days(cur.date, 7 * interval);
                    break;
                case Freq::Daily:
                    next = cur;
                    next.date = add_days(cur.date, interval);
                    break;
                default:
                    return out;
            }
            // Apply BYMONTH / BYDAY adjustments for annual transitions (e.g. "2nd Sunday of March").
            if (r.freq == Freq::Yearly && !r.bymonth.empty()) {
                int target_month = r.bymonth[0];
                next.date.month = target_month;
                // If BYDAY has an ordinal, find the Nth weekday of that month.
                if (!r.byday.empty() && r.byday[0].ordinal.has_value()) {
                    int y = next.date.year;
                    int m = next.date.month;
                    int target_ord = *r.byday[0].ordinal;
                    Weekday target_wd = r.byday[0].weekday;
                    int dim = days_in_month(y, m);
                    std::vector<int> matches;
                    for (int day = 1; day <= dim; ++day) {
                        if (weekday_of(Date{y, m, day}) == target_wd) matches.push_back(day);
                    }
                    int idx = target_ord > 0 ? target_ord - 1 : static_cast<int>(matches.size()) + target_ord;
                    if (idx >= 0 && idx < static_cast<int>(matches.size())) {
                        next.date.day = matches[idx];
                    }
                }
            }
            cur = next;
        }
        return out;
    };

    // Find the most recent transition <= local across both standard and daylight.
    DateTime best = {};
    const std::string* best_offset_to = nullptr;
    bool have_best = false;
    DateTime dummy = local;

    for (const auto& obs : tz->standard) {
        for (const auto& dt : enumerate_observance(obs, dummy)) {
            if (!have_best || compare_datetime(dt, best) > 0) {
                best = dt;
                best_offset_to = &obs.tzoffsetto;
                have_best = true;
            }
        }
    }
    for (const auto& obs : tz->daylight) {
        for (const auto& dt : enumerate_observance(obs, dummy)) {
            if (!have_best || compare_datetime(dt, best) > 0) {
                best = dt;
                best_offset_to = &obs.tzoffsetto;
                have_best = true;
            }
        }
    }

    // Fallback: event is before any observance's DTSTART. Use the earliest
    // observance's TZOFFSETFROM (describes the state BEFORE that observance).
    // Observances are stored sorted by DTSTART, so pick the first.
    std::string fallback_offset;
    if (!have_best) {
        const Observance* earliest = nullptr;
        for (const auto& obs : tz->standard) {
            if (!earliest || compare_datetime(obs.dtstart, earliest->dtstart) < 0) earliest = &obs;
        }
        for (const auto& obs : tz->daylight) {
            if (!earliest || compare_datetime(obs.dtstart, earliest->dtstart) < 0) earliest = &obs;
        }
        if (earliest) {
            fallback_offset = earliest->tzoffsetfrom;
            best_offset_to = &fallback_offset;
            have_best = true;
        }
    }

    if (!have_best || !best_offset_to) return std::nullopt;

    auto off_opt = parse_utc_offset(*best_offset_to);
    if (!off_opt) return std::nullopt;
    // Convert local → UTC: UTC = local - offset.
    DateTime result = add_seconds(local, -static_cast<long long>(*off_opt));
    result.kind = TimeKind::Utc;
    result.tzid.clear();
    return result;
}

// Detect whether a local time falls in a DST fall-back overlap ("fold",
// ambiguous) or spring-forward gap ("gap", nonexistent) for the given TZID.
// Returns "" if neither, or the anomaly kind as a string.
std::string detect_tz_anomaly(
    const DateTime& local, const std::string& tzid, const Calendar& cal) {
    const VTimezone* tz = nullptr;
    for (const auto& t : cal.timezones) {
        if (t.tzid == tzid) { tz = &t; break; }
    }
    if (!tz) return "";

    // Enumerate every transition instant for the observance that falls near
    // `local` (within a year on either side). Includes:
    //   * DTSTART itself (if within range and RRULE absent or year matches)
    //   * RRULE-expansions for local.year - 1, local.year, local.year + 1
    //     (honoring UNTIL). BYMONTH / BYMONTHDAY / ordinal-BYDAY applied.
    //   * RDATE entries (floating DATE-TIMEs).
    //
    // Returning one DateTime per generated transition means a zone with
    // multiple rules (e.g., BYMONTHDAY-only vs. ordinal BYDAY) produces
    // multiple candidate transitions per year, and RDATE-only observances
    // produce their explicit transition instants.
    auto compute_ordinal_day = [](int year, int month, int ordinal, Weekday wd) -> int {
        int dim = days_in_month(year, month);
        std::vector<int> matches;
        for (int day = 1; day <= dim; ++day) {
            if (weekday_of(Date{year, month, day}) == wd) matches.push_back(day);
        }
        int idx = ordinal > 0 ? ordinal - 1 : static_cast<int>(matches.size()) + ordinal;
        if (idx >= 0 && idx < static_cast<int>(matches.size())) {
            return matches[idx];
        }
        return -1;
    };

    auto transitions_for = [&](const Observance& obs) -> std::vector<DateTime> {
        std::vector<DateTime> out;
        if (!obs.rrule) {
            out.push_back(obs.dtstart);
        }
        // RDATE entries.
        for (const auto& rd : obs.rdate) {
            if (rd.dt && rd.dt->datetime) {
                out.push_back(*rd.dt->datetime);
            } else if (rd.dt && rd.dt->date) {
                out.push_back(DateTime{*rd.dt->date, 0, 0, 0, TimeKind::Floating, {}});
            }
        }
        if (!obs.rrule) return out;
        const RRule& r = *obs.rrule;
        // Generate one transition per target year in [local.year - 1, +1]:
        for (int dy = -1; dy <= 1; ++dy) {
            int year = local.date.year + dy;
            DateTime t = obs.dtstart;
            t.date.year = year;
            // Skip if year is before the observance's DTSTART year.
            if (year < obs.dtstart.date.year) continue;
            if (!r.bymonth.empty()) t.date.month = r.bymonth[0];
            if (!r.bymonthday.empty()) {
                t.date.day = r.bymonthday[0];
            } else if (!r.byday.empty() && r.byday[0].ordinal.has_value()) {
                int d = compute_ordinal_day(
                    t.date.year, t.date.month, *r.byday[0].ordinal, r.byday[0].weekday
                );
                if (d > 0) t.date.day = d;
            }
            // Honor UNTIL.
            if (r.until && compare_datetime(t, *r.until) > 0) continue;
            out.push_back(t);
        }
        return out;
    };

    auto check_transition = [&](const Observance& obs, const DateTime& t) -> std::string {
        auto off_from = parse_utc_offset(obs.tzoffsetfrom);
        auto off_to = parse_utc_offset(obs.tzoffsetto);
        if (!off_from || !off_to) return "";
        long long delta = static_cast<long long>(*off_to) - static_cast<long long>(*off_from);
        if (delta == 0) return "";
        DateTime lo, hi;
        bool fold;
        if (delta < 0) {
            lo = add_seconds(t, delta);
            hi = t;
            fold = true;
        } else {
            lo = t;
            hi = add_seconds(t, delta);
            fold = false;
        }
        if (compare_datetime(local, lo) >= 0 && compare_datetime(local, hi) < 0) {
            return fold ? "timezone_fold_ambiguous" : "nonexistent_local_time";
        }
        return "";
    };

    for (const auto& obs : tz->standard) {
        for (const auto& t : transitions_for(obs)) {
            auto k = check_transition(obs, t);
            if (!k.empty()) return k;
        }
    }
    for (const auto& obs : tz->daylight) {
        for (const auto& t : transitions_for(obs)) {
            auto k = check_transition(obs, t);
            if (!k.empty()) return k;
        }
    }
    return "";
}

} // namespace ical
