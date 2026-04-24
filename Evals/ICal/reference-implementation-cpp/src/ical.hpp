#pragma once

#include <cstdint>
#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <tuple>
#include <vector>

namespace ical {

// --- Date/time ---

struct Date {
    int year{}, month{}, day{};
    bool operator==(const Date&) const = default;
    auto operator<=>(const Date&) const = default;
};

enum class TimeKind {
    Floating,  // no zone
    Utc,       // trailing Z
    Zoned,     // has TZID that resolves in-file
};

struct DateTime {
    Date date{};
    int hour{}, minute{}, second{};
    TimeKind kind{TimeKind::Floating};
    std::string tzid;  // only when kind == Zoned
    bool operator==(const DateTime&) const = default;
    auto operator<=>(const DateTime&) const = default;
};

struct Property {
    std::string name;
    std::map<std::string, std::string> params;
    std::string value;
    std::size_t line{};
};

struct Warning {
    std::string kind;
    std::string message;
    std::optional<std::string> uid;
    std::optional<std::string> value;
};

struct ParseError {
    std::size_t line{}, column{};
    std::string message;
};

enum class Freq { Secondly, Minutely, Hourly, Daily, Weekly, Monthly, Yearly };
enum class Weekday { Sunday = 0, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday };

struct ByDayEntry {
    Weekday weekday{};
    std::optional<int> ordinal;
};

struct RRule {
    Freq freq{Freq::Daily};
    int interval{1};
    std::optional<int> count;
    std::optional<DateTime> until;
    std::vector<int> bymonth;
    std::vector<int> bymonthday;
    std::vector<ByDayEntry> byday;
    std::vector<int> bysetpos;
    std::vector<int> bysecond, byminute, byhour, byyearday, byweekno;
    Weekday wkst{Weekday::Monday};
    std::optional<std::string> rscale;  // RFC 7529: calendar system name (uppercase)
    std::optional<std::string> skip;    // RFC 7529: OMIT|BACKWARD|FORWARD
};

struct DateOrDateTime {
    std::optional<Date> date;
    std::optional<DateTime> datetime;
    std::optional<std::string> tzid;  // reflect the TZID= param if present
};

// --- RDATE period value (§3.3.9) ---
// Either explicit `start/end` or `start/duration`. Exactly one of `end`
// or `duration` is populated.
struct Period {
    DateOrDateTime start;
    std::optional<DateOrDateTime> end;
    std::optional<std::string> duration;
};

// An RDATE entry is a tagged union: plain date-or-datetime, OR a period.
struct RDateEntry {
    std::optional<DateOrDateTime> dt;   // plain DATE / DATE-TIME
    std::optional<Period> period;       // VALUE=PERIOD
};

// --- Cal-address (ATTENDEE / ORGANIZER) ---

struct CalAddress {
    std::string value;                      // URI
    std::optional<std::string> cn;
    std::optional<std::string> cutype;
    std::optional<std::string> role;
    std::optional<std::string> partstat;
    std::optional<bool> rsvp;
    std::vector<std::string> member;
    std::vector<std::string> delegated_from;
    std::vector<std::string> delegated_to;
    std::optional<std::string> sent_by;
    std::optional<std::string> dir;
    std::optional<std::string> language;
};

// --- Attach ---

struct Attach {
    std::string value;
    std::optional<std::string> fmttype;
    std::optional<std::string> encoding;
    std::optional<std::string> value_type;  // VALUE= param
};

// --- VALARM ---

struct Trigger {
    std::string value;                     // raw duration like "-PT15M" or ISO datetime
    std::optional<std::string> related;    // "START" | "END" | nullopt (absolute)
};

struct VAlarm {
    std::optional<std::string> action;
    std::optional<Trigger> trigger;
    std::optional<std::string> duration;
    std::optional<int> repeat;
    std::vector<Attach> attach;
    std::optional<std::string> description;
    std::optional<std::string> summary;
    std::vector<CalAddress> attendees;
    std::optional<std::string> acknowledged;  // normalized ISO-8601 UTC
    std::vector<Property> raw_properties;
};

struct VEvent {
    std::string uid;
    std::optional<DateTime> dtstamp;
    std::optional<DateOrDateTime> dtstart;
    std::optional<DateOrDateTime> dtend;
    std::optional<std::string> duration;
    std::optional<std::string> summary;
    std::optional<std::string> description;
    std::optional<std::string> location;
    std::optional<std::string> status;
    std::optional<std::string> class_;
    std::optional<DateOrDateTime> recurrence_id;
    std::optional<std::string> recurrence_id_range;  // e.g. "THISANDFUTURE"
    std::optional<RRule> rrule;
    std::optional<RRule> exrule;
    std::vector<RDateEntry> rdate;
    std::vector<DateOrDateTime> exdate;
    std::vector<std::string> categories;
    std::optional<CalAddress> organizer;
    std::vector<CalAddress> attendees;
    std::optional<int> sequence;
    std::vector<VAlarm> alarms;
    std::vector<Property> raw_properties;
};

// VTODO / VJOURNAL / VFREEBUSY share most of VEvent's fields. For simplicity,
// reuse the VEvent struct for all four and tag by container.
struct VTodo : VEvent {
    std::optional<DateOrDateTime> due;
    std::optional<DateOrDateTime> completed;
    std::optional<int> percent_complete;
};
struct VJournal : VEvent {};
struct VFreeBusy : VEvent {};

struct Observance {
    DateTime dtstart{};
    std::string tzoffsetfrom;  // e.g. "-0500"
    std::string tzoffsetto;
    std::optional<std::string> tzname;
    std::optional<RRule> rrule;
    std::vector<RDateEntry> rdate;
};

struct VTimezone {
    std::string tzid;
    std::vector<Observance> standard;
    std::vector<Observance> daylight;
};

// --- RFC 7986: calendar-level image / conference entries ---
struct ImageEntry {
    std::string value;
    std::optional<std::string> fmttype;
    std::optional<std::string> encoding;
    std::optional<std::string> display;
};

struct ConferenceEntry {
    std::string value;
    std::optional<std::string> feature;
    std::optional<std::string> label;
};

struct Calendar {
    std::string prodid, version;
    std::optional<std::string> calscale;
    std::optional<std::string> method;
    // RFC 7986 calendar-level properties
    std::optional<std::string> name;
    std::optional<std::string> description;
    std::optional<std::string> refresh_interval;
    std::optional<std::string> source;
    std::optional<std::string> color;
    std::optional<std::string> url;
    std::vector<std::string> categories;
    std::vector<ImageEntry> images;
    std::vector<ConferenceEntry> conferences;
    std::vector<VEvent> events;
    std::vector<VTodo> todos;
    std::vector<VJournal> journals;
    std::vector<VFreeBusy> freebusy;
    std::vector<VTimezone> timezones;
    std::vector<Warning> warnings;
};

struct Occurrence {
    std::string uid;
    DateOrDateTime dtstart;
    std::optional<DateOrDateTime> dtend;
    std::optional<std::string> tz;
    bool override{false};
    bool cancelled{false};
    std::optional<std::string> recurrence_id;  // ISO-8601 value if override
    std::optional<std::string> range;          // "THISANDFUTURE" or nullopt
};

// --- API ---

std::optional<ParseError> parse_ics(std::string_view source, Calendar& cal);

std::vector<Occurrence> expand_events(
    const Calendar& cal,
    const DateOrDateTime& from,
    const DateOrDateTime& to,
    std::vector<Warning>& warnings
);

std::string emit_parse_json(const Calendar& cal);
std::string emit_expand_json(
    const std::vector<Occurrence>& occurrences,
    const std::vector<Warning>& warnings
);
std::string emit_error_json(const ParseError& err, const std::vector<Warning>& warnings);

// --- Utilities ---

std::string to_upper(std::string_view s);
std::string iso_format(const Date& d);
std::string iso_format(const DateTime& dt);
std::string iso_format(const DateOrDateTime& d);

std::optional<DateTime> parse_iso_datetime(std::string_view s);
std::optional<DateTime> parse_ical_datetime(std::string_view s);
std::optional<Date> parse_ical_date(std::string_view s);

int days_in_month(int year, int month);
bool is_leap_year(int year);
Weekday weekday_of(const Date& d);

Date add_days(const Date& d, int n);
Date add_months(const Date& d, int n);
Date add_years(const Date& d, int n);

DateTime add_seconds(const DateTime& dt, long long n);

int compare(const DateOrDateTime& a, const DateOrDateTime& b);
int compare_datetime(const DateTime& a, const DateTime& b);

// Parse UTC offset like "-0500" or "+0530" or "-050030" into total seconds.
std::optional<int> parse_utc_offset(std::string_view s);
std::string format_utc_offset(int seconds);

// Convert a zoned local DateTime to UTC using a named TZID resolved against
// cal.timezones. Returns nullopt if TZID not found (caller emits warning).
std::optional<DateTime> resolve_zoned_to_utc(
    const DateTime& local, const std::string& tzid, const Calendar& cal
);

// Does `target` match any occurrence generated by `rrule` + `rdate` starting
// from `dtstart`? Used for parse-time orphan detection of overrides.
// Searches up to COUNT or a generous horizon.
bool rrule_contains_target(
    const DateTime& dtstart, const RRule& rrule,
    const std::vector<RDateEntry>& rdates,
    const DateTime& target
);

} // namespace ical
