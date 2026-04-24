#include "ical.hpp"

#include <cstdio>
#include <sstream>
#include <string>

namespace ical {

namespace {

void jstr(std::ostringstream& o, std::string_view s) {
    o << '"';
    for (unsigned char c : s) {
        switch (c) {
            case '"':  o << "\\\""; break;
            case '\\': o << "\\\\"; break;
            case '\b': o << "\\b";  break;
            case '\f': o << "\\f";  break;
            case '\n': o << "\\n";  break;
            case '\r': o << "\\r";  break;
            case '\t': o << "\\t";  break;
            default:
                if (c < 0x20) {
                    char buf[8];
                    std::snprintf(buf, sizeof(buf), "\\u%04x", c);
                    o << buf;
                } else {
                    o << static_cast<char>(c);
                }
        }
    }
    o << '"';
}

const char* freq_name(Freq f) {
    switch (f) {
        case Freq::Secondly: return "SECONDLY";
        case Freq::Minutely: return "MINUTELY";
        case Freq::Hourly:   return "HOURLY";
        case Freq::Daily:    return "DAILY";
        case Freq::Weekly:   return "WEEKLY";
        case Freq::Monthly:  return "MONTHLY";
        case Freq::Yearly:   return "YEARLY";
    }
    return "DAILY";
}

const char* weekday_name(Weekday w) {
    static const char* NAMES[] = {"SU", "MO", "TU", "WE", "TH", "FR", "SA"};
    return NAMES[static_cast<int>(w)];
}

void emit_int_list(std::ostringstream& o, const std::vector<int>& v) {
    o << '[';
    for (std::size_t i = 0; i < v.size(); ++i) {
        if (i) o << ',';
        o << v[i];
    }
    o << ']';
}

void emit_str_list(std::ostringstream& o, const std::vector<std::string>& v) {
    o << '[';
    for (std::size_t i = 0; i < v.size(); ++i) {
        if (i) o << ',';
        jstr(o, v[i]);
    }
    o << ']';
}

void emit_byday(std::ostringstream& o, const std::vector<ByDayEntry>& v) {
    o << '[';
    for (std::size_t i = 0; i < v.size(); ++i) {
        if (i) o << ',';
        o << "{\"weekday\":";
        jstr(o, weekday_name(v[i].weekday));
        if (v[i].ordinal.has_value()) {
            o << ",\"ordinal\":" << *v[i].ordinal;
        } else {
            o << ",\"ordinal\":null";
        }
        o << '}';
    }
    o << ']';
}

void emit_date_or_dt(std::ostringstream& o, const DateOrDateTime& d) {
    jstr(o, iso_format(d));
}

void emit_rrule(std::ostringstream& o, const RRule& r) {
    o << "{\"freq\":";
    jstr(o, freq_name(r.freq));
    o << ",\"interval\":" << r.interval;
    o << ",\"count\":";
    if (r.count.has_value()) o << *r.count; else o << "null";
    o << ",\"until\":";
    if (r.until.has_value()) jstr(o, iso_format(*r.until)); else o << "null";
    o << ",\"bymonth\":"; emit_int_list(o, r.bymonth);
    o << ",\"bymonthday\":"; emit_int_list(o, r.bymonthday);
    o << ",\"byday\":"; emit_byday(o, r.byday);
    o << ",\"bysetpos\":"; emit_int_list(o, r.bysetpos);
    o << ",\"byhour\":"; emit_int_list(o, r.byhour);
    o << ",\"byminute\":"; emit_int_list(o, r.byminute);
    o << ",\"bysecond\":"; emit_int_list(o, r.bysecond);
    o << ",\"byyearday\":"; emit_int_list(o, r.byyearday);
    o << ",\"byweekno\":"; emit_int_list(o, r.byweekno);
    o << ",\"wkst\":"; jstr(o, weekday_name(r.wkst));
    o << ",\"rscale\":"; if (r.rscale) jstr(o, *r.rscale); else o << "null";
    o << ",\"skip\":"; if (r.skip) jstr(o, *r.skip); else o << "null";
    o << '}';
}

void emit_warning(std::ostringstream& o, const Warning& w) {
    o << '{';
    o << "\"kind\":"; jstr(o, w.kind);
    o << ",\"message\":"; jstr(o, w.message);
    if (w.uid.has_value()) { o << ",\"uid\":"; jstr(o, *w.uid); }
    if (w.value.has_value()) { o << ",\"value\":"; jstr(o, *w.value); }
    o << '}';
}

void emit_cal_address(std::ostringstream& o, const CalAddress& a) {
    o << "{\"value\":"; jstr(o, a.value);
    o << ",\"cn\":"; if (a.cn) jstr(o, *a.cn); else o << "null";
    o << ",\"cutype\":"; if (a.cutype) jstr(o, *a.cutype); else o << "null";
    o << ",\"role\":"; if (a.role) jstr(o, *a.role); else o << "null";
    o << ",\"partstat\":"; if (a.partstat) jstr(o, *a.partstat); else o << "null";
    o << ",\"rsvp\":";
    if (a.rsvp.has_value()) o << (*a.rsvp ? "true" : "false");
    else o << "null";
    o << ",\"member\":"; emit_str_list(o, a.member);
    o << ",\"delegated_from\":"; emit_str_list(o, a.delegated_from);
    o << ",\"delegated_to\":"; emit_str_list(o, a.delegated_to);
    o << ",\"sent_by\":"; if (a.sent_by) jstr(o, *a.sent_by); else o << "null";
    o << ",\"dir\":"; if (a.dir) jstr(o, *a.dir); else o << "null";
    o << ",\"language\":"; if (a.language) jstr(o, *a.language); else o << "null";
    o << '}';
}

void emit_attach(std::ostringstream& o, const Attach& a) {
    o << "{\"value\":"; jstr(o, a.value);
    o << ",\"fmttype\":"; if (a.fmttype) jstr(o, *a.fmttype); else o << "null";
    o << ",\"encoding\":"; if (a.encoding) jstr(o, *a.encoding); else o << "null";
    o << "}";
}

void emit_raw_properties(std::ostringstream& o, const std::vector<Property>& raw) {
    o << '[';
    for (std::size_t i = 0; i < raw.size(); ++i) {
        if (i) o << ',';
        const auto& p = raw[i];
        o << "{\"name\":"; jstr(o, p.name);
        o << ",\"params\":{";
        bool first_p = true;
        for (const auto& [k, v] : p.params) {
            if (!first_p) o << ',';
            first_p = false;
            jstr(o, k);
            o << ':';
            jstr(o, v);
        }
        o << "},\"value\":"; jstr(o, p.value);
        o << '}';
    }
    o << ']';
}

void emit_trigger(std::ostringstream& o, const Trigger& t) {
    o << "{\"value\":"; jstr(o, t.value);
    o << ",\"related\":";
    if (t.related) jstr(o, *t.related); else o << "null";
    o << '}';
}

void emit_alarm(std::ostringstream& o, const VAlarm& a) {
    o << "{\"uid\":";
    if (a.uid) jstr(o, *a.uid); else o << "null";
    o << ",\"action\":";
    if (a.action) jstr(o, *a.action); else o << "null";
    o << ",\"trigger\":";
    if (a.trigger) emit_trigger(o, *a.trigger); else o << "null";
    o << ",\"duration\":";
    if (a.duration) jstr(o, *a.duration); else o << "null";
    o << ",\"repeat\":";
    if (a.repeat) o << *a.repeat; else o << "null";
    o << ",\"attach\":[";
    for (std::size_t i = 0; i < a.attach.size(); ++i) {
        if (i) o << ',';
        emit_attach(o, a.attach[i]);
    }
    o << "],\"description\":";
    if (a.description) jstr(o, *a.description); else o << "null";
    o << ",\"summary\":";
    if (a.summary) jstr(o, *a.summary); else o << "null";
    o << ",\"attendees\":[";
    for (std::size_t i = 0; i < a.attendees.size(); ++i) {
        if (i) o << ',';
        emit_cal_address(o, a.attendees[i]);
    }
    o << "],\"acknowledged\":";
    if (a.acknowledged) jstr(o, *a.acknowledged); else o << "null";
    o << ",\"proximity\":";
    if (a.proximity) jstr(o, *a.proximity); else o << "null";
    o << ",\"related_to\":[";
    for (std::size_t i = 0; i < a.related_to.size(); ++i) {
        if (i) o << ',';
        o << "{\"value\":";
        jstr(o, a.related_to[i].value);
        o << ",\"reltype\":";
        if (a.related_to[i].reltype) jstr(o, *a.related_to[i].reltype); else o << "null";
        o << '}';
    }
    o << "],\"raw_properties\":";
    emit_raw_properties(o, a.raw_properties);
    o << '}';
}

void emit_rdate_entry(std::ostringstream& o, const RDateEntry& e) {
    if (e.period) {
        const auto& p = *e.period;
        o << "{\"start\":"; jstr(o, iso_format(p.start));
        if (p.end) {
            o << ",\"end\":"; jstr(o, iso_format(*p.end));
        } else {
            o << ",\"end\":null";
        }
        if (p.duration) {
            o << ",\"duration\":"; jstr(o, *p.duration);
        } else {
            o << ",\"duration\":null";
        }
        o << '}';
    } else if (e.dt) {
        emit_date_or_dt(o, *e.dt);
    } else {
        o << "null";
    }
}

void emit_recurrence_id(std::ostringstream& o, const VEvent& e) {
    if (!e.recurrence_id) { o << "null"; return; }
    const auto& rid = *e.recurrence_id;
    o << "{\"value\":"; jstr(o, iso_format(rid));
    o << ",\"range\":";
    if (e.recurrence_id_range) jstr(o, *e.recurrence_id_range); else o << "null";
    o << ",\"tzid\":";
    if (rid.tzid) jstr(o, *rid.tzid); else o << "null";
    o << '}';
}

void emit_event_common(std::ostringstream& o, const VEvent& e) {
    o << "\"uid\":"; jstr(o, e.uid);
    o << ",\"dtstamp\":"; if (e.dtstamp) jstr(o, iso_format(*e.dtstamp)); else o << "null";
    o << ",\"dtstart\":"; if (e.dtstart) emit_date_or_dt(o, *e.dtstart); else o << "null";
    o << ",\"dtend\":"; if (e.dtend) emit_date_or_dt(o, *e.dtend); else o << "null";
    o << ",\"duration\":"; if (e.duration) jstr(o, *e.duration); else o << "null";
    o << ",\"summary\":"; if (e.summary) jstr(o, *e.summary); else o << "null";
    o << ",\"description\":"; if (e.description) jstr(o, *e.description); else o << "null";
    o << ",\"location\":"; if (e.location) jstr(o, *e.location); else o << "null";
    o << ",\"status\":"; if (e.status) jstr(o, *e.status); else o << "null";
    o << ",\"class\":"; if (e.class_) jstr(o, *e.class_); else o << "null";
    o << ",\"categories\":[";
    for (std::size_t i = 0; i < e.categories.size(); ++i) { if (i) o << ','; jstr(o, e.categories[i]); }
    o << "],\"organizer\":";
    if (e.organizer) emit_cal_address(o, *e.organizer); else o << "null";
    o << ",\"attendees\":[";
    for (std::size_t i = 0; i < e.attendees.size(); ++i) {
        if (i) o << ',';
        emit_cal_address(o, e.attendees[i]);
    }
    o << "],\"rrule\":"; if (e.rrule) emit_rrule(o, *e.rrule); else o << "null";
    o << ",\"rdate\":[";
    for (std::size_t i = 0; i < e.rdate.size(); ++i) { if (i) o << ','; emit_rdate_entry(o, e.rdate[i]); }
    o << "],\"exdate\":[";
    for (std::size_t i = 0; i < e.exdate.size(); ++i) { if (i) o << ','; emit_date_or_dt(o, e.exdate[i]); }
    o << "],\"exrule\":"; if (e.exrule) emit_rrule(o, *e.exrule); else o << "null";
    o << ",\"recurrence_id\":"; emit_recurrence_id(o, e);
    o << ",\"sequence\":"; if (e.sequence) o << *e.sequence; else o << "null";
    // Codex v1.0 review #2: formerly-missing schema fields.
    o << ",\"priority\":"; if (e.priority) o << *e.priority; else o << "null";
    o << ",\"transp\":"; if (e.transp) jstr(o, *e.transp); else o << "null";
    o << ",\"url\":"; if (e.url) jstr(o, *e.url); else o << "null";
    o << ",\"geo\":";
    if (e.geo) o << "{\"lat\":" << e.geo->lat << ",\"lon\":" << e.geo->lon << "}";
    else o << "null";
    o << ",\"resources\":[";
    for (std::size_t i = 0; i < e.resources.size(); ++i) { if (i) o << ','; jstr(o, e.resources[i]); }
    o << "],\"contact\":"; if (e.contact) jstr(o, *e.contact); else o << "null";
    o << ",\"created\":"; if (e.created) jstr(o, *e.created); else o << "null";
    o << ",\"last_modified\":"; if (e.last_modified) jstr(o, *e.last_modified); else o << "null";
    o << ",\"attachments\":[";
    for (std::size_t i = 0; i < e.attachments.size(); ++i) {
        if (i) o << ',';
        emit_attach(o, e.attachments[i]);
    }
    o << "],\"related_to\":[";
    // RFC 5545 §3.8.4.5: RELATED-TO may appear on VEVENT/VTODO/VJOURNAL/
    // VFREEBUSY. Shape matches VALARM's related_to: {value, reltype}.
    for (std::size_t i = 0; i < e.related_to.size(); ++i) {
        if (i) o << ',';
        o << "{\"value\":"; jstr(o, e.related_to[i].value);
        o << ",\"reltype\":";
        if (e.related_to[i].reltype) jstr(o, *e.related_to[i].reltype);
        else o << "null";
        o << '}';
    }
    o << "],\"color\":"; if (e.color) jstr(o, *e.color); else o << "null";
    o << ",\"images\":[";
    for (std::size_t i = 0; i < e.images.size(); ++i) {
        if (i) o << ',';
        const auto& img = e.images[i];
        o << "{\"value\":"; jstr(o, img.value);
        o << ",\"fmttype\":"; if (img.fmttype) jstr(o, *img.fmttype); else o << "null";
        o << ",\"encoding\":"; if (img.encoding) jstr(o, *img.encoding); else o << "null";
        o << ",\"display\":"; if (img.display) jstr(o, *img.display); else o << "null";
        o << '}';
    }
    o << "],\"conferences\":[";
    for (std::size_t i = 0; i < e.conferences.size(); ++i) {
        if (i) o << ',';
        const auto& c = e.conferences[i];
        o << "{\"value\":"; jstr(o, c.value);
        o << ",\"feature\":"; if (c.feature) jstr(o, *c.feature); else o << "null";
        o << ",\"label\":"; if (c.label) jstr(o, *c.label); else o << "null";
        o << '}';
    }
    o << "],\"alarms\":[";
    for (std::size_t i = 0; i < e.alarms.size(); ++i) {
        if (i) o << ',';
        emit_alarm(o, e.alarms[i]);
    }
    o << "],\"raw_properties\":";
    emit_raw_properties(o, e.raw_properties);
}

void emit_event(std::ostringstream& o, const VEvent& e) {
    o << '{';
    emit_event_common(o, e);
    o << '}';
}

void emit_todo(std::ostringstream& o, const VTodo& t) {
    o << '{';
    emit_event_common(o, t);
    o << ",\"due\":"; if (t.due) emit_date_or_dt(o, *t.due); else o << "null";
    o << ",\"completed\":"; if (t.completed) emit_date_or_dt(o, *t.completed); else o << "null";
    o << ",\"percent_complete\":";
    if (t.percent_complete) o << *t.percent_complete; else o << "null";
    o << '}';
}

// RFC 5545 §3.6.4 VFREEBUSY — each FREEBUSY property becomes a
// `{fbtype, periods: [<period>, ...]}` entry in `freebusy`.
void emit_freebusy(std::ostringstream& o, const VFreeBusy& fb) {
    o << '{';
    emit_event_common(o, fb);
    o << ",\"freebusy\":[";
    for (std::size_t i = 0; i < fb.freebusy_entries.size(); ++i) {
        if (i) o << ',';
        const auto& fe = fb.freebusy_entries[i];
        o << "{\"fbtype\":";
        if (fe.fbtype) jstr(o, *fe.fbtype); else jstr(o, std::string("BUSY"));
        o << ",\"periods\":[";
        for (std::size_t j = 0; j < fe.periods.size(); ++j) {
            if (j) o << ',';
            const auto& per = fe.periods[j];
            o << "{\"start\":"; emit_date_or_dt(o, per.start);
            if (per.end) {
                o << ",\"end\":"; emit_date_or_dt(o, *per.end);
            } else if (per.duration) {
                o << ",\"duration\":"; jstr(o, *per.duration);
            }
            o << '}';
        }
        o << "]}";
    }
    o << "]}";
}

// For VTIMEZONE observance DTSTART: always emit as floating (no trailing Z)
// per RFC 5545 §3.8.2.4.
std::string iso_format_floating(const DateTime& dt) {
    char buf[32];
    std::snprintf(buf, sizeof(buf), "%04d-%02d-%02dT%02d:%02d:%02d",
                  dt.date.year, dt.date.month, dt.date.day,
                  dt.hour, dt.minute, dt.second);
    return buf;
}

void emit_observance(std::ostringstream& o, const Observance& obs) {
    o << "{\"dtstart\":"; jstr(o, iso_format_floating(obs.dtstart));
    o << ",\"tzoffsetfrom\":";
    if (auto off = parse_utc_offset(obs.tzoffsetfrom); off) jstr(o, format_utc_offset(*off));
    else jstr(o, obs.tzoffsetfrom);
    o << ",\"tzoffsetto\":";
    if (auto off = parse_utc_offset(obs.tzoffsetto); off) jstr(o, format_utc_offset(*off));
    else jstr(o, obs.tzoffsetto);
    o << ",\"tzname\":";
    if (obs.tzname) jstr(o, *obs.tzname); else o << "null";
    o << ",\"rrule\":";
    if (obs.rrule) emit_rrule(o, *obs.rrule); else o << "null";
    o << ",\"rdate\":[";
    for (std::size_t i = 0; i < obs.rdate.size(); ++i) { if (i) o << ','; emit_rdate_entry(o, obs.rdate[i]); }
    o << "]}";
}

void emit_vtimezone(std::ostringstream& o, const VTimezone& tz) {
    o << "{\"tzid\":"; jstr(o, tz.tzid);
    o << ",\"last_modified\":";
    if (tz.last_modified) jstr(o, *tz.last_modified); else o << "null";
    o << ",\"tzurl\":"; if (tz.tzurl) jstr(o, *tz.tzurl); else o << "null";
    o << ",\"comment\":[";
    for (std::size_t i = 0; i < tz.comment.size(); ++i) {
        if (i) o << ',';
        jstr(o, tz.comment[i]);
    }
    o << "],\"standard\":[";
    for (std::size_t i = 0; i < tz.standard.size(); ++i) { if (i) o << ','; emit_observance(o, tz.standard[i]); }
    o << "],\"daylight\":[";
    for (std::size_t i = 0; i < tz.daylight.size(); ++i) { if (i) o << ','; emit_observance(o, tz.daylight[i]); }
    o << "]}";
}

} // namespace

std::string emit_parse_json(const Calendar& cal) {
    std::ostringstream o;
    o << "{\"calendar\":{\"prodid\":";
    jstr(o, cal.prodid);
    o << ",\"version\":";
    jstr(o, cal.version);
    o << ",\"calscale\":";
    if (cal.calscale) jstr(o, *cal.calscale); else o << "null";
    o << ",\"method\":";
    if (cal.method) jstr(o, *cal.method); else o << "null";
    // RFC 7986 calendar-level properties
    o << ",\"name\":"; if (cal.name) jstr(o, *cal.name); else o << "null";
    o << ",\"description\":"; if (cal.description) jstr(o, *cal.description); else o << "null";
    o << ",\"refresh_interval\":";
    if (cal.refresh_interval) jstr(o, *cal.refresh_interval); else o << "null";
    o << ",\"source\":"; if (cal.source) jstr(o, *cal.source); else o << "null";
    o << ",\"color\":"; if (cal.color) jstr(o, *cal.color); else o << "null";
    o << ",\"url\":"; if (cal.url) jstr(o, *cal.url); else o << "null";
    o << ",\"categories\":"; emit_str_list(o, cal.categories);
    o << ",\"images\":[";
    for (std::size_t i = 0; i < cal.images.size(); ++i) {
        if (i) o << ',';
        const auto& img = cal.images[i];
        o << "{\"value\":"; jstr(o, img.value);
        o << ",\"fmttype\":"; if (img.fmttype) jstr(o, *img.fmttype); else o << "null";
        o << ",\"encoding\":"; if (img.encoding) jstr(o, *img.encoding); else o << "null";
        o << ",\"display\":"; if (img.display) jstr(o, *img.display); else o << "null";
        o << '}';
    }
    o << "],\"conferences\":[";
    for (std::size_t i = 0; i < cal.conferences.size(); ++i) {
        if (i) o << ',';
        const auto& conf = cal.conferences[i];
        o << "{\"value\":"; jstr(o, conf.value);
        o << ",\"feature\":"; if (conf.feature) jstr(o, *conf.feature); else o << "null";
        o << ",\"label\":"; if (conf.label) jstr(o, *conf.label); else o << "null";
        o << '}';
    }
    o << "]},\"events\":[";
    for (std::size_t i = 0; i < cal.events.size(); ++i) { if (i) o << ','; emit_event(o, cal.events[i]); }
    o << "],\"todos\":[";
    for (std::size_t i = 0; i < cal.todos.size(); ++i) { if (i) o << ','; emit_todo(o, cal.todos[i]); }
    o << "],\"journals\":[";
    for (std::size_t i = 0; i < cal.journals.size(); ++i) { if (i) o << ','; emit_event(o, cal.journals[i]); }
    o << "],\"freebusy\":[";
    for (std::size_t i = 0; i < cal.freebusy.size(); ++i) { if (i) o << ','; emit_freebusy(o, cal.freebusy[i]); }
    o << "],\"timezones\":[";
    for (std::size_t i = 0; i < cal.timezones.size(); ++i) { if (i) o << ','; emit_vtimezone(o, cal.timezones[i]); }
    o << "],\"availabilities\":[";
    for (std::size_t i = 0; i < cal.availabilities.size(); ++i) {
        if (i) o << ',';
        const auto& va = cal.availabilities[i];
        o << "{\"uid\":"; jstr(o, va.uid);
        o << ",\"dtstamp\":"; if (va.dtstamp) jstr(o, iso_format(*va.dtstamp)); else o << "null";
        o << ",\"dtstart\":"; if (va.dtstart) emit_date_or_dt(o, *va.dtstart); else o << "null";
        o << ",\"dtend\":"; if (va.dtend) emit_date_or_dt(o, *va.dtend); else o << "null";
        o << ",\"duration\":"; if (va.duration) jstr(o, *va.duration); else o << "null";
        o << ",\"summary\":"; if (va.summary) jstr(o, *va.summary); else o << "null";
        o << ",\"description\":"; if (va.description) jstr(o, *va.description); else o << "null";
        o << ",\"busytype\":"; if (va.busytype) jstr(o, *va.busytype); else o << "null";
        o << ",\"priority\":"; if (va.priority) o << *va.priority; else o << "null";
        o << ",\"organizer\":";
        if (va.organizer) emit_cal_address(o, *va.organizer); else o << "null";
        o << ",\"available\":[";
        for (std::size_t j = 0; j < va.available.size(); ++j) {
            if (j) o << ',';
            const auto& av = va.available[j];
            o << "{\"uid\":"; jstr(o, av.uid);
            o << ",\"dtstamp\":"; if (av.dtstamp) jstr(o, iso_format(*av.dtstamp)); else o << "null";
            o << ",\"dtstart\":"; if (av.dtstart) emit_date_or_dt(o, *av.dtstart); else o << "null";
            o << ",\"dtend\":"; if (av.dtend) emit_date_or_dt(o, *av.dtend); else o << "null";
            o << ",\"duration\":"; if (av.duration) jstr(o, *av.duration); else o << "null";
            o << ",\"summary\":"; if (av.summary) jstr(o, *av.summary); else o << "null";
            o << ",\"description\":"; if (av.description) jstr(o, *av.description); else o << "null";
            o << ",\"location\":"; if (av.location) jstr(o, *av.location); else o << "null";
            o << ",\"contact\":"; if (av.contact) jstr(o, *av.contact); else o << "null";
            o << ",\"created\":"; if (av.created) jstr(o, *av.created); else o << "null";
            o << ",\"last_modified\":"; if (av.last_modified) jstr(o, *av.last_modified); else o << "null";
            // Emit recurrence_id with the same shape VEvent uses so both
            // recurrence override surfaces have identical param fidelity.
            // RFC 5545 §3.8.4.4 allows RECURRENCE-ID to carry TZID + RANGE.
            o << ",\"recurrence_id\":";
            if (av.recurrence_id) {
                const auto& rid = *av.recurrence_id;
                o << "{\"value\":"; jstr(o, iso_format(rid));
                o << ",\"range\":";
                if (av.recurrence_id_range) jstr(o, *av.recurrence_id_range);
                else o << "null";
                o << ",\"tzid\":";
                if (rid.tzid) jstr(o, *rid.tzid); else o << "null";
                o << '}';
            } else {
                o << "null";
            }
            o << ",\"categories\":[";
            for (std::size_t k = 0; k < av.categories.size(); ++k) {
                if (k) o << ',';
                jstr(o, av.categories[k]);
            }
            o << "],\"comment\":[";
            for (std::size_t k = 0; k < av.comment.size(); ++k) {
                if (k) o << ',';
                jstr(o, av.comment[k]);
            }
            o << "],\"rrule\":"; if (av.rrule) emit_rrule(o, *av.rrule); else o << "null";
            o << ",\"rdate\":[";
            for (std::size_t k = 0; k < av.rdate.size(); ++k) {
                if (k) o << ',';
                emit_rdate_entry(o, av.rdate[k]);
            }
            o << "],\"exdate\":[";
            for (std::size_t k = 0; k < av.exdate.size(); ++k) {
                if (k) o << ',';
                emit_date_or_dt(o, av.exdate[k]);
            }
            o << "],\"raw_properties\":"; emit_raw_properties(o, av.raw_properties);
            o << '}';
        }
        o << "],\"raw_properties\":"; emit_raw_properties(o, va.raw_properties);
        o << '}';
    }
    o << "],\"warnings\":[";
    for (std::size_t i = 0; i < cal.warnings.size(); ++i) { if (i) o << ','; emit_warning(o, cal.warnings[i]); }
    o << "]}";
    return o.str();
}

std::string emit_expand_json(
    const std::vector<Occurrence>& occurrences, const std::vector<Warning>& warnings) {
    std::ostringstream o;
    o << "{\"occurrences\":[";
    for (std::size_t i = 0; i < occurrences.size(); ++i) {
        if (i) o << ',';
        const auto& occ = occurrences[i];
        o << "{\"uid\":"; jstr(o, occ.uid);
        o << ",\"dtstart\":"; emit_date_or_dt(o, occ.dtstart);
        o << ",\"dtend\":";
        if (occ.dtend) emit_date_or_dt(o, *occ.dtend); else o << "null";
        o << ",\"tz\":";
        if (occ.tz) jstr(o, *occ.tz); else o << "null";
        o << ",\"override\":" << (occ.override ? "true" : "false");
        o << ",\"cancelled\":" << (occ.cancelled ? "true" : "false");
        o << ",\"recurrence_id\":";
        if (occ.recurrence_id) jstr(o, *occ.recurrence_id); else o << "null";
        o << ",\"range\":";
        if (occ.range) jstr(o, *occ.range); else o << "null";
        o << '}';
    }
    o << "],\"warnings\":[";
    for (std::size_t i = 0; i < warnings.size(); ++i) { if (i) o << ','; emit_warning(o, warnings[i]); }
    o << "]}";
    return o.str();
}

std::string emit_error_json(const ParseError& err, const std::vector<Warning>& warnings) {
    std::ostringstream o;
    o << "{\"error\":{\"line\":" << err.line
      << ",\"column\":" << err.column
      << ",\"message\":"; jstr(o, err.message);
    o << "},\"warnings\":[";
    for (std::size_t i = 0; i < warnings.size(); ++i) { if (i) o << ','; emit_warning(o, warnings[i]); }
    o << "]}";
    return o.str();
}

} // namespace ical
