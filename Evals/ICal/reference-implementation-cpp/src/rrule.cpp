#include "ical.hpp"

#include <algorithm>
#include <set>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace ical {

namespace {

DateTime seed_of(const DateOrDateTime& d) {
    if (d.datetime) return *d.datetime;
    DateTime dt{};
    dt.date = *d.date;
    dt.kind = TimeKind::Floating;
    return dt;
}

bool match_bymonth(const Date& d, const std::vector<int>& bym) {
    if (bym.empty()) return true;
    for (int m : bym) if (m == d.month) return true;
    return false;
}

bool match_bymonthday(const Date& d, const std::vector<int>& bmd) {
    if (bmd.empty()) return true;
    int dim = days_in_month(d.year, d.month);
    for (int v : bmd) {
        int actual = v > 0 ? v : dim + 1 + v;
        if (actual == d.day) return true;
    }
    return false;
}

bool weekday_bare_match(const Date& d, const std::vector<ByDayEntry>& byday) {
    if (byday.empty()) return true;
    Weekday w = weekday_of(d);
    for (const auto& e : byday) {
        if (e.weekday == w && !e.ordinal.has_value()) return true;
    }
    return false;
}

std::vector<Date> monthly_byday_occurrences(int year, int month, const std::vector<ByDayEntry>& byday) {
    std::vector<Date> out;
    int dim = days_in_month(year, month);
    for (const auto& e : byday) {
        std::vector<int> matches;
        for (int day = 1; day <= dim; ++day) {
            if (weekday_of(Date{year, month, day}) == e.weekday) matches.push_back(day);
        }
        if (e.ordinal.has_value()) {
            int o = *e.ordinal;
            int idx = o > 0 ? o - 1 : static_cast<int>(matches.size()) + o;
            if (idx >= 0 && idx < static_cast<int>(matches.size())) {
                out.push_back(Date{year, month, matches[idx]});
            }
        } else {
            for (int day : matches) out.push_back(Date{year, month, day});
        }
    }
    std::sort(out.begin(), out.end());
    out.erase(std::unique(out.begin(), out.end()), out.end());
    return out;
}

std::vector<Date> apply_bysetpos_date(const std::vector<Date>& in, const std::vector<int>& bsp) {
    if (bsp.empty()) return in;
    std::vector<Date> out;
    int n = static_cast<int>(in.size());
    for (int p : bsp) {
        int idx = p > 0 ? p - 1 : n + p;
        if (idx >= 0 && idx < n) out.push_back(in[idx]);
    }
    std::sort(out.begin(), out.end());
    out.erase(std::unique(out.begin(), out.end()), out.end());
    return out;
}

std::vector<DateTime> apply_bysetpos_dt(const std::vector<DateTime>& in, const std::vector<int>& bsp) {
    if (bsp.empty()) return in;
    std::vector<DateTime> out;
    int n = static_cast<int>(in.size());
    for (int p : bsp) {
        int idx = p > 0 ? p - 1 : n + p;
        if (idx >= 0 && idx < n) out.push_back(in[idx]);
    }
    return out;
}

// Expand a day `d` across BYHOUR/BYMINUTE/BYSECOND into a set of DateTime's on that day.
// If a BY* is empty, use the seed's value.
std::vector<DateTime> time_expand(const Date& d, const RRule& r, const DateTime& seed) {
    std::vector<int> hours = r.byhour.empty() ? std::vector<int>{seed.hour} : r.byhour;
    std::vector<int> mins = r.byminute.empty() ? std::vector<int>{seed.minute} : r.byminute;
    std::vector<int> secs = r.bysecond.empty() ? std::vector<int>{seed.second} : r.bysecond;
    std::vector<DateTime> out;
    for (int h : hours) {
        for (int mi : mins) {
            for (int s : secs) {
                DateTime dt;
                dt.date = d;
                dt.hour = h;
                dt.minute = mi;
                dt.second = s;
                dt.kind = seed.kind;
                dt.tzid = seed.tzid;
                out.push_back(dt);
            }
        }
    }
    std::sort(out.begin(), out.end(),
              [](const DateTime& a, const DateTime& b) { return compare_datetime(a, b) < 0; });
    return out;
}

// Enumerate candidate DateTimes for one period (e.g. one day for DAILY, one month for MONTHLY).
std::vector<DateTime> expand_period(const RRule& r, const DateTime& seed, const Date& anchor) {
    std::vector<Date> dates;
    switch (r.freq) {
        case Freq::Secondly:
        case Freq::Minutely:
        case Freq::Hourly:
        case Freq::Daily: {
            dates.push_back(anchor);
            dates.erase(std::remove_if(dates.begin(), dates.end(), [&](const Date& d) {
                if (!match_bymonth(d, r.bymonth)) return true;
                if (!match_bymonthday(d, r.bymonthday)) return true;
                if (!r.byday.empty() && !weekday_bare_match(d, r.byday)) return true;
                return false;
            }), dates.end());
            break;
        }
        case Freq::Weekly: {
            Weekday awd = weekday_of(anchor);
            int wkst = static_cast<int>(r.wkst);
            int cur = static_cast<int>(awd);
            int back = (cur - wkst + 7) % 7;
            Date week_start = add_days(anchor, -back);
            for (int i = 0; i < 7; ++i) {
                Date d = add_days(week_start, i);
                if (!match_bymonth(d, r.bymonth)) continue;
                if (!r.byday.empty() && !weekday_bare_match(d, r.byday)) continue;
                if (!match_bymonthday(d, r.bymonthday)) continue;
                dates.push_back(d);
            }
            break;
        }
        case Freq::Monthly: {
            int y = anchor.year, m = anchor.month;
            int dim = days_in_month(y, m);
            std::vector<Date> cands;
            if (!r.bymonthday.empty()) {
                for (int v : r.bymonthday) {
                    int day = v > 0 ? v : dim + 1 + v;
                    if (day >= 1 && day <= dim) cands.push_back(Date{y, m, day});
                }
                if (!r.byday.empty()) {
                    bool any_ord = false;
                    for (const auto& e : r.byday) if (e.ordinal) { any_ord = true; break; }
                    cands.erase(std::remove_if(cands.begin(), cands.end(), [&](const Date& d) {
                        Weekday w = weekday_of(d);
                        for (const auto& e : r.byday) {
                            if (e.weekday == w) return false;
                        }
                        return true;
                    }), cands.end());
                    (void)any_ord;
                }
            } else if (!r.byday.empty()) {
                cands = monthly_byday_occurrences(y, m, r.byday);
            } else {
                if (anchor.day <= dim) cands.push_back(Date{y, m, anchor.day});
            }
            cands.erase(std::remove_if(cands.begin(), cands.end(), [&](const Date& d) {
                return !match_bymonth(d, r.bymonth);
            }), cands.end());
            std::sort(cands.begin(), cands.end());
            cands.erase(std::unique(cands.begin(), cands.end()), cands.end());
            dates = std::move(cands);
            break;
        }
        case Freq::Yearly: {
            int y = anchor.year;
            std::vector<Date> cands;
            // BYYEARDAY (if present) takes precedence: convert each day-of-year to a date.
            if (!r.byyearday.empty()) {
                int year_len = is_leap_year(y) ? 366 : 365;
                for (int v : r.byyearday) {
                    int yd = v > 0 ? v : year_len + 1 + v;
                    if (yd < 1 || yd > year_len) continue;
                    // Convert day-of-year to (month, day).
                    int m = 1, remaining = yd;
                    while (m <= 12) {
                        int dim = days_in_month(y, m);
                        if (remaining <= dim) break;
                        remaining -= dim;
                        m++;
                    }
                    if (m <= 12) cands.push_back(Date{y, m, remaining});
                }
                // Apply BYMONTH filter if also set.
                if (!r.bymonth.empty()) {
                    cands.erase(std::remove_if(cands.begin(), cands.end(),
                        [&](const Date& d) { return !match_bymonth(d, r.bymonth); }),
                        cands.end());
                }
                // Apply BYDAY filter (no ordinal in yearly-with-byyearday context).
                if (!r.byday.empty()) {
                    cands.erase(std::remove_if(cands.begin(), cands.end(),
                        [&](const Date& d) { return !weekday_bare_match(d, r.byday); }),
                        cands.end());
                }
            } else {
                std::vector<int> months = r.bymonth.empty()
                                              ? std::vector<int>{anchor.month}
                                              : r.bymonth;
                for (int m : months) {
                    int dim = days_in_month(y, m);
                    if (!r.bymonthday.empty()) {
                        for (int v : r.bymonthday) {
                            int day = v > 0 ? v : dim + 1 + v;
                            if (day >= 1 && day <= dim) cands.push_back(Date{y, m, day});
                        }
                    } else if (!r.byday.empty()) {
                        auto md = monthly_byday_occurrences(y, m, r.byday);
                        for (const auto& d : md) cands.push_back(d);
                    } else {
                        if (anchor.day <= dim) cands.push_back(Date{y, m, anchor.day});
                    }
                }
            }
            std::sort(cands.begin(), cands.end());
            cands.erase(std::unique(cands.begin(), cands.end()), cands.end());
            dates = std::move(cands);
            break;
        }
    }

    // Expand each date by time (BYHOUR/BYMINUTE/BYSECOND).
    std::vector<DateTime> out;
    for (const auto& d : dates) {
        auto dts = time_expand(d, r, seed);
        for (const auto& dt : dts) out.push_back(dt);
    }

    // Apply BYSETPOS across the period's datetime candidates.
    out = apply_bysetpos_dt(out, r.bysetpos);
    std::sort(out.begin(), out.end(),
              [](const DateTime& a, const DateTime& b) { return compare_datetime(a, b) < 0; });
    return out;
}

std::vector<DateTime> expand_rrule(const DateTime& dtstart, const RRule& r,
                                   const DateTime* window_to_utc_ish) {
    std::vector<DateTime> out;
    int count_remaining = r.count.has_value() ? *r.count : -1;
    int interval_limit = 1000;
    int interval = std::max(1, r.interval);
    Date anchor_date = dtstart.date;
    DateTime anchor_dt = dtstart;
    bool first_interval = true;
    int yearly_iter = 0;  // count of YEARLY iterations completed

    while (interval_limit-- > 0) {
        std::vector<DateTime> cands;
        if (r.freq == Freq::Secondly || r.freq == Freq::Minutely || r.freq == Freq::Hourly) {
            // Sub-day: each interval step is a single datetime offset from the previous.
            DateTime cand = anchor_dt;
            // Check BY filters: BYMONTH, BYMONTHDAY, BYDAY (filter), BYHOUR, BYMINUTE, BYSECOND (filter).
            auto passes_filters = [&](const DateTime& dt) {
                if (!match_bymonth(dt.date, r.bymonth)) return false;
                if (!match_bymonthday(dt.date, r.bymonthday)) return false;
                if (!r.byday.empty() && !weekday_bare_match(dt.date, r.byday)) return false;
                if (!r.byhour.empty()) {
                    bool found = false;
                    for (int h : r.byhour) if (h == dt.hour) { found = true; break; }
                    if (!found) return false;
                }
                if (!r.byminute.empty()) {
                    bool found = false;
                    for (int m : r.byminute) if (m == dt.minute) { found = true; break; }
                    if (!found) return false;
                }
                if (!r.bysecond.empty()) {
                    bool found = false;
                    for (int s : r.bysecond) if (s == dt.second) { found = true; break; }
                    if (!found) return false;
                }
                return true;
            };
            if (passes_filters(cand)) cands.push_back(cand);
        } else {
            cands = expand_period(r, dtstart, anchor_date);
        }

        if (first_interval) {
            cands.erase(std::remove_if(cands.begin(), cands.end(),
                [&](const DateTime& dt) { return compare_datetime(dt, dtstart) < 0; }),
                cands.end());
        }
        first_interval = false;

        for (const auto& dt : cands) {
            if (r.until.has_value() && compare_datetime(dt, *r.until) > 0) return out;
            out.push_back(dt);
            if (count_remaining > 0) {
                count_remaining--;
                if (count_remaining == 0) return out;
            }
        }

        if (window_to_utc_ish != nullptr && !cands.empty()) {
            if (compare_datetime(cands.back(), *window_to_utc_ish) >= 0) {
                return out;
            }
        }

        switch (r.freq) {
            case Freq::Secondly: anchor_dt = add_seconds(anchor_dt, interval); break;
            case Freq::Minutely: anchor_dt = add_seconds(anchor_dt, 60LL * interval); break;
            case Freq::Hourly:   anchor_dt = add_seconds(anchor_dt, 3600LL * interval); break;
            case Freq::Daily:    anchor_date = add_days(anchor_date, interval); break;
            case Freq::Weekly:   anchor_date = add_days(anchor_date, 7 * interval); break;
            case Freq::Monthly:  anchor_date = add_months(anchor_date, interval); break;
            case Freq::Yearly: {
                // For YEARLY, preserve the original month/day so SKIP=OMIT can
                // correctly drop invalid dates (e.g. Feb 29 in non-leap years).
                yearly_iter++;
                anchor_date = Date{dtstart.date.year + yearly_iter * interval,
                                   dtstart.date.month, dtstart.date.day};
                break;
            }
        }
        if (r.until.has_value()) {
            Date check = (r.freq == Freq::Secondly || r.freq == Freq::Minutely || r.freq == Freq::Hourly)
                             ? anchor_dt.date
                             : anchor_date;
            if (check > r.until->date) {
                // Even so, the final interval may contain valid instances; keep going but limit.
            }
        }
    }
    return out;
}

// Convert a DateTime (floating / UTC / zoned) to the UTC comparison form for windowing.
DateTime to_comparable(const DateTime& dt, const Calendar& cal, std::vector<Warning>& warnings,
                       const std::string& uid) {
    if (dt.kind == TimeKind::Zoned && !dt.tzid.empty()) {
        auto resolved = resolve_zoned_to_utc(dt, dt.tzid, cal);
        if (resolved) {
            // DST fold-ambiguous / nonexistent-local-time detection.
            std::string anomaly = detect_tz_anomaly(dt, dt.tzid, cal);
            if (!anomaly.empty()) {
                Warning w; w.kind = anomaly;
                if (anomaly == "timezone_fold_ambiguous") {
                    w.message = "Local time in DST fall-back overlap; using pre-transition offset";
                } else {
                    w.message = "Local time in DST spring-forward gap; using post-transition offset";
                }
                w.uid = uid.empty() ? std::optional<std::string>{} : uid;
                w.value = dt.tzid;
                warnings.push_back(std::move(w));
            }
            return *resolved;
        }
        Warning w; w.kind = "unresolved_tzid";
        w.message = "TZID '" + dt.tzid + "' is not defined in the file; treating as floating";
        w.uid = uid.empty() ? std::optional<std::string>{} : uid;
        w.value = dt.tzid;
        warnings.push_back(std::move(w));
        DateTime floating = dt;
        floating.kind = TimeKind::Floating;
        floating.tzid.clear();
        return floating;
    }
    return dt;
}

Occurrence make_occurrence(
    const std::string& uid, const DateTime& dt, bool override_flag,
    const DateOrDateTime& dtstart_form, const Calendar& cal,
    std::vector<Warning>& warnings) {
    Occurrence o;
    o.uid = uid;
    o.override = override_flag;
    DateTime cmp = to_comparable(dt, cal, warnings, uid);
    DateOrDateTime v;
    if (dtstart_form.date && !dtstart_form.datetime) {
        v.date = cmp.date;
    } else {
        v.datetime = cmp;
    }
    o.dtstart = v;
    if (!dtstart_form.date && dt.kind == TimeKind::Zoned) o.tz = dt.tzid;
    return o;
}

// Extract a DateTime seed from an RDateEntry (plain dt only). Period entries
// are handled separately by callers.
std::optional<DateTime> rdate_entry_seed(const RDateEntry& e) {
    if (!e.dt) return std::nullopt;
    DateTime d = seed_of(*e.dt);
    if (e.dt->tzid) { d.kind = TimeKind::Zoned; d.tzid = *e.dt->tzid; }
    return d;
}

} // namespace

bool rrule_contains_target(
    const DateTime& dtstart, const RRule& rrule,
    const std::vector<RDateEntry>& rdates,
    const DateTime& target) {
    // Check RDATE entries first.
    for (const auto& rd : rdates) {
        if (rd.period) {
            if (compare_datetime(seed_of(rd.period->start), target) == 0) return true;
        } else if (rd.dt) {
            if (compare_datetime(seed_of(*rd.dt), target) == 0) return true;
        }
    }
    // Expand RRULE and check.
    DateTime horizon = target;
    auto expanded = expand_rrule(dtstart, rrule, &horizon);
    for (const auto& d : expanded) {
        if (compare_datetime(d, target) == 0) return true;
    }
    return false;
}

std::vector<Occurrence> expand_events(
    const Calendar& cal, const DateOrDateTime& from, const DateOrDateTime& to,
    std::vector<Warning>& warnings) {

    // Index overrides: uid → list of (recurrence-id, override event, range, consumed flag).
    // Base events are those without RECURRENCE-ID.
    struct OverrideRec {
        DateTime target_utc;
        const VEvent* event;
        std::string range;
        bool consumed{false};
    };
    std::unordered_map<std::string, std::vector<OverrideRec>> overrides_by_uid;
    for (const auto& ev : cal.events) {
        if (ev.recurrence_id.has_value()) {
            DateTime rid_dt;
            if (ev.recurrence_id->datetime) rid_dt = *ev.recurrence_id->datetime;
            else if (ev.recurrence_id->date) rid_dt = DateTime{*ev.recurrence_id->date, 0, 0, 0, TimeKind::Floating, {}};
            auto cmp = to_comparable(rid_dt, cal, warnings, ev.uid);
            overrides_by_uid[ev.uid].push_back(
                OverrideRec{cmp, &ev, ev.recurrence_id_range.value_or(""), false});
        }
    }

    // Track which base-event UIDs exist so we can detect overrides with no
    // matching base event at all (one class of orphan).
    std::unordered_map<std::string, bool> has_base_event;
    for (const auto& ev : cal.events) {
        if (!ev.recurrence_id.has_value()) has_base_event[ev.uid] = true;
    }

    std::vector<Occurrence> result;
    DateTime from_dt = seed_of(from);
    DateTime to_dt = seed_of(to);

    for (const auto& ev : cal.events) {
        if (ev.recurrence_id.has_value()) continue;  // overrides are applied against base events
        if (!ev.dtstart) continue;
        DateTime seed = seed_of(*ev.dtstart);
        if (ev.dtstart->tzid) {
            seed.kind = TimeKind::Zoned;
            seed.tzid = *ev.dtstart->tzid;
        }

        auto* uid_overrides_ptr = overrides_by_uid.count(ev.uid) ? &overrides_by_uid[ev.uid] : nullptr;

        auto emit = [&](const DateTime& dt, bool override_flag) {
            Occurrence occ = make_occurrence(ev.uid, dt, override_flag, *ev.dtstart, cal, warnings);
            if (compare(occ.dtstart, from) < 0) return;
            if (compare(occ.dtstart, to) >= 0) return;
            result.push_back(std::move(occ));
        };
        auto emit_override = [&](const DateTime& dt, const std::string& rid_iso,
                                  const std::string& range_token, bool cancelled_flag) {
            Occurrence occ = make_occurrence(ev.uid, dt, true, *ev.dtstart, cal, warnings);
            occ.recurrence_id = rid_iso;
            if (!range_token.empty()) occ.range = range_token;
            occ.cancelled = cancelled_flag;
            if (compare(occ.dtstart, from) < 0) return;
            if (compare(occ.dtstart, to) >= 0) return;
            result.push_back(std::move(occ));
        };

        if (!ev.rrule.has_value()) {
            DateTime dt_cmp = to_comparable(seed, cal, warnings, ev.uid);
            // Check for override matching the base occurrence.
            bool consumed_here = false;
            if (uid_overrides_ptr) {
                for (auto& ov : *uid_overrides_ptr) {
                    if (compare_datetime(ov.target_utc, dt_cmp) == 0) {
                        ov.consumed = true;
                        consumed_here = true;
                        if (ov.event->status && *ov.event->status == "CANCELLED") {
                            // summary.md §7: STATUS:CANCELLED override marks
                            // the occurrence as cancelled but does NOT drop
                            // it from the array (§9.2 occurrence schema keeps
                            // every key present including `cancelled`). Emit
                            // at the ORIGINAL recurrence-id time with
                            // cancelled=true so consumers can see which
                            // instance was cancelled.
                            emit_override(seed, iso_format(ov.target_utc),
                                          ov.range, true);
                            break;
                        }
                        if (ov.event->dtstart) {
                            DateTime ov_dt = seed_of(*ov.event->dtstart);
                            if (ov.event->dtstart->tzid) {
                                ov_dt.kind = TimeKind::Zoned;
                                ov_dt.tzid = *ov.event->dtstart->tzid;
                            }
                            emit_override(ov_dt, iso_format(ov.target_utc), ov.range, false);
                        }
                        break;
                    }
                }
            }
            if (!consumed_here) emit(seed, false);
            for (const auto& rd : ev.rdate) {
                if (rd.period) {
                    DateTime start = seed_of(rd.period->start);
                    if (rd.period->start.tzid) {
                        start.kind = TimeKind::Zoned;
                        start.tzid = *rd.period->start.tzid;
                    }
                    Occurrence occ = make_occurrence(ev.uid, start, false, *ev.dtstart, cal, warnings);
                    if (rd.period->end) {
                        DateTime endt = seed_of(*rd.period->end);
                        if (rd.period->end->tzid) {
                            endt.kind = TimeKind::Zoned;
                            endt.tzid = *rd.period->end->tzid;
                        }
                        DateTime end_cmp = to_comparable(endt, cal, warnings, ev.uid);
                        DateOrDateTime end_dodt;
                        end_dodt.datetime = end_cmp;
                        occ.dtend = end_dodt;
                    }
                    if (compare(occ.dtstart, from) >= 0 && compare(occ.dtstart, to) < 0) {
                        result.push_back(std::move(occ));
                    }
                } else if (auto d = rdate_entry_seed(rd); d) {
                    emit(*d, false);
                }
            }
            continue;
        }

        // Recurring event.
        DateTime window_end_cmp = to_dt;
        auto expanded = expand_rrule(seed, *ev.rrule, &window_end_cmp);

        // Build EXDATE set (by UTC-compare string).
        std::set<std::string> excluded;
        for (const auto& ex : ev.exdate) {
            DateTime d = seed_of(ex);
            if (ex.tzid) { d.kind = TimeKind::Zoned; d.tzid = *ex.tzid; }
            excluded.insert(iso_format(to_comparable(d, cal, warnings, ev.uid)));
        }

        // Apply EXRULE subtractively.
        if (ev.exrule.has_value()) {
            auto ex_expanded = expand_rrule(seed, *ev.exrule, &window_end_cmp);
            for (const auto& ed : ex_expanded) {
                excluded.insert(iso_format(to_comparable(ed, cal, warnings, ev.uid)));
            }
        }

        // Identify a THISANDFUTURE override, if any. Only one is honored; v0.2
        // picks the earliest-target THISANDFUTURE override.
        const OverrideRec* taf_override = nullptr;
        if (uid_overrides_ptr) {
            for (const auto& ov : *uid_overrides_ptr) {
                if (ov.range == "THISANDFUTURE") {
                    if (!taf_override
                        || compare_datetime(ov.target_utc, taf_override->target_utc) < 0) {
                        taf_override = &ov;
                    }
                }
            }
        }
        // Precompute the THISANDFUTURE shift in seconds (override.dtstart - recurrence-id).
        long long taf_shift_seconds = 0;
        if (taf_override && taf_override->event->dtstart) {
            DateTime ov_dt = seed_of(*taf_override->event->dtstart);
            if (taf_override->event->dtstart->tzid) {
                ov_dt.kind = TimeKind::Zoned;
                ov_dt.tzid = *taf_override->event->dtstart->tzid;
            }
            DateTime ov_cmp = to_comparable(ov_dt, cal, warnings, ev.uid);
            // diff = ov_cmp - target_utc (in seconds)
            // Use a day-level + time-level computation.
            auto total_secs = [](const DateTime& a) -> long long {
                // Seconds since a fixed epoch; only the difference is used.
                long long day_n = 0;
                // reuse add_days-based arithmetic by counting days
                Date d0{1970, 1, 1};
                long long days = 0;
                if (a.date < d0) {
                    Date cur = a.date;
                    while (cur < d0) { cur = add_days(cur, 1); days--; }
                } else {
                    Date cur = d0;
                    while (cur < a.date) { cur = add_days(cur, 1); days++; }
                }
                return days * 86400LL + a.hour * 3600LL + a.minute * 60LL + a.second
                       + day_n;  // day_n is 0, just to silence unused-var
            };
            taf_shift_seconds = total_secs(ov_cmp) - total_secs(taf_override->target_utc);
        }

        for (const auto& dt : expanded) {
            DateTime cmp = to_comparable(dt, cal, warnings, ev.uid);
            if (excluded.count(iso_format(cmp))) continue;

            // Exact-match override (non-THISANDFUTURE): replace or cancel.
            if (uid_overrides_ptr) {
                bool handled = false;
                for (auto& ov : *uid_overrides_ptr) {
                    if (ov.range == "THISANDFUTURE") continue;
                    if (compare_datetime(ov.target_utc, cmp) == 0) {
                        handled = true;
                        ov.consumed = true;
                        if (ov.event->status && *ov.event->status == "CANCELLED") {
                            // summary.md §7 / §9.2: emit the occurrence at
                            // its original time with cancelled=true rather
                            // than dropping it from the array, so the
                            // consumer can see the cancellation explicitly.
                            emit_override(dt, iso_format(ov.target_utc),
                                          ov.range, true);
                            break;
                        }
                        if (ov.event->dtstart) {
                            DateTime ov_dt = seed_of(*ov.event->dtstart);
                            if (ov.event->dtstart->tzid) {
                                ov_dt.kind = TimeKind::Zoned;
                                ov_dt.tzid = *ov.event->dtstart->tzid;
                            }
                            emit_override(ov_dt, iso_format(ov.target_utc), ov.range, false);
                        }
                        break;
                    }
                }
                if (handled) continue;
            }

            // THISANDFUTURE: if base occurrence is at or after the TAF target,
            // emit the occurrence shifted by taf_shift_seconds.
            if (taf_override && compare_datetime(cmp, taf_override->target_utc) >= 0) {
                DateTime shifted = add_seconds(cmp, taf_shift_seconds);
                // Attach tz of the override for reporting.
                if (taf_override->event->dtstart && taf_override->event->dtstart->tzid) {
                    shifted.kind = TimeKind::Zoned;
                    shifted.tzid = *taf_override->event->dtstart->tzid;
                }
                // Mark the THISANDFUTURE anchor (where cmp == target_utc) with
                // recurrence_id; later shifted occurrences keep the range flag
                // but do not carry a recurrence_id.
                bool is_anchor = compare_datetime(cmp, taf_override->target_utc) == 0;
                if (is_anchor) {
                    // Mark the TAF override as consumed so the orphan pass
                    // below does not re-emit it.
                    if (uid_overrides_ptr) {
                        for (auto& ov : *uid_overrides_ptr) {
                            if (ov.range == "THISANDFUTURE"
                                && compare_datetime(ov.target_utc, taf_override->target_utc) == 0) {
                                ov.consumed = true;
                                break;
                            }
                        }
                    }
                    emit_override(shifted, iso_format(taf_override->target_utc),
                                  taf_override->range, false);
                } else {
                    // Shifted-forward occurrences carry range but no recurrence_id.
                    Occurrence occ = make_occurrence(ev.uid, shifted, true, *ev.dtstart, cal, warnings);
                    occ.range = taf_override->range;
                    if (compare(occ.dtstart, from) >= 0 && compare(occ.dtstart, to) < 0) {
                        result.push_back(std::move(occ));
                    }
                }
                continue;
            }

            emit(dt, false);
        }

        for (const auto& rd : ev.rdate) {
            if (rd.period) {
                DateTime start = seed_of(rd.period->start);
                if (rd.period->start.tzid) {
                    start.kind = TimeKind::Zoned;
                    start.tzid = *rd.period->start.tzid;
                }
                Occurrence occ = make_occurrence(ev.uid, start, false, *ev.dtstart, cal, warnings);
                if (rd.period->end) {
                    DateTime endt = seed_of(*rd.period->end);
                    if (rd.period->end->tzid) {
                        endt.kind = TimeKind::Zoned;
                        endt.tzid = *rd.period->end->tzid;
                    }
                    DateTime end_cmp = to_comparable(endt, cal, warnings, ev.uid);
                    DateOrDateTime end_dodt;
                    end_dodt.datetime = end_cmp;
                    occ.dtend = end_dodt;
                }
                if (compare(occ.dtstart, from) >= 0 && compare(occ.dtstart, to) < 0) {
                    result.push_back(std::move(occ));
                }
            } else if (auto d = rdate_entry_seed(rd); d) {
                emit(*d, false);
            }
        }
    }

    // After all base events have been expanded, surface orphan overrides:
    // override events whose RECURRENCE-ID did NOT match any base occurrence
    // (either no base event exists for this UID at all, or the base event
    // had no occurrence at the override's recurrence-id time).
    for (auto& [uid, ovs] : overrides_by_uid) {
        for (auto& ov : ovs) {
            if (ov.consumed) continue;
            if (ov.range == "THISANDFUTURE") continue;  // absorbed separately
            Warning w;
            w.kind = "orphan_override";
            w.message = "RECURRENCE-ID "
                      + iso_format(ov.target_utc)
                      + " for UID '" + uid + "' does not match any base occurrence";
            w.uid = uid;
            warnings.push_back(std::move(w));
            // Surface the override's own dtstart as a standalone occurrence.
            if (ov.event->dtstart) {
                DateTime ov_dt = seed_of(*ov.event->dtstart);
                if (ov.event->dtstart->tzid) {
                    ov_dt.kind = TimeKind::Zoned;
                    ov_dt.tzid = *ov.event->dtstart->tzid;
                }
                Occurrence occ = make_occurrence(uid, ov_dt, true, *ov.event->dtstart, cal, warnings);
                if (compare(occ.dtstart, from) >= 0 && compare(occ.dtstart, to) < 0) {
                    result.push_back(std::move(occ));
                }
            }
        }
    }
    (void)has_base_event;  // tracking retained for future per-UID checks

    // Stable sort by dtstart with UID lexicographic tie-break (spec: occurrences
    // are sorted ascending by dtstart; equal timestamps break ties on uid).
    std::sort(result.begin(), result.end(),
              [](const Occurrence& a, const Occurrence& b) {
                  int c = compare(a.dtstart, b.dtstart);
                  if (c != 0) return c < 0;
                  return a.uid < b.uid;
              });
    return result;
}

} // namespace ical
