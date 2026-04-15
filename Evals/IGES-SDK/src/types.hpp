#pragma once
// iges::types — Value types shared across the SDK.
//
// This header defines the fundamental scalar, enum, and strong-typedef
// types that appear throughout the IGES data model.

#include <cstdint>
#include <string>
#include <optional>
#include <variant>
#include <expected>
#include <vector>
#include <span>

namespace iges {

// ── Scalar aliases ───────────────────────────────────────────
using Real = double;

// ── Strong index types ───────────────────────────────────────
// DEIndex: a 1-based Directory Entry sequence number (always odd for
// the first line of an entity's DE pair).  Zero means "null pointer".
struct DEIndex {
    int value = 0;
    constexpr explicit DEIndex(int v = 0) : value(v) {}
    constexpr bool is_null() const { return value == 0; }
    constexpr bool operator==(DEIndex const&) const = default;
    constexpr auto operator<=>(DEIndex const&) const = default;
};

struct EntityType {
    int value = 0;
    constexpr explicit EntityType(int v = 0) : value(v) {}
    constexpr bool operator==(EntityType const&) const = default;
};

struct FormNumber {
    int value = 0;
    constexpr explicit FormNumber(int v = 0) : value(v) {}
    constexpr bool operator==(FormNumber const&) const = default;
};

// ── Enumerations ─────────────────────────────────────────────

enum class Units : int {
    Inches       = 1,
    Millimeters  = 2,
    SeeField15   = 3,
    Feet         = 4,
    Miles        = 5,
    Meters       = 6,
    Kilometers   = 7,
    Mils         = 8,
    Microns      = 9,
    Centimeters  = 10,
    Microinches  = 11,
};

enum class SpecVersion : int {
    V1_0       = 1,
    ANSI_1981  = 2,
    V2_0       = 3,
    V3_0       = 4,
    ASME_1987  = 5,
    V4_0       = 6,
    ASME_1989  = 7,
    V5_0       = 8,
    V5_2       = 9,
    V5_1       = 10,
    V5_3       = 11,
};

enum class DraftingStandard : int {
    None = 0,
    ISO  = 1,
    AFNOR = 2,
    ANSI  = 3,
    BSI   = 4,
    CSA   = 5,
    DIN   = 6,
    JIS   = 7,
};

enum class BlankStatus : int {
    Visible = 0,
    Blanked = 1,
};

enum class SubordinateSwitch : int {
    Independent        = 0,
    PhysicallyDependent = 1,
    LogicallyDependent  = 2,
    Both               = 3,
};

enum class EntityUseFlag : int {
    Geometry           = 0,
    Annotation         = 1,
    Definition         = 2,
    Other              = 3,
    LogicalPositional  = 4,
    Parametric2D       = 5,
    ConstructionGeometry = 6,
};

enum class HierarchyFlag : int {
    GlobalTopDown = 0,
    GlobalDefer   = 1,
    UseProperty   = 2,
};

enum class LineFontPattern : int {
    Default    = 0,
    Solid      = 1,
    Dashed     = 2,
    Phantom    = 3,
    Centerline = 4,
    Dotted     = 5,
};

enum class Color : int {
    None    = 0,
    Black   = 1,
    Red     = 2,
    Green   = 3,
    Blue    = 4,
    Yellow  = 5,
    Magenta = 6,
    Cyan    = 7,
    White   = 8,
};

// ── Section kinds ────────────────────────────────────────────
enum class SectionKind : char {
    Flag      = 'C',
    Start     = 'S',
    Global    = 'G',
    Directory = 'D',
    Parameter = 'P',
    Terminate = 'T',
};

// ── Diagnostics ──────────────────────────────────────────────
struct Diagnostic {
    enum class Severity { Info, Warning, Error };
    Severity    severity = Severity::Error;
    int         line     = 0;
    SectionKind section  = SectionKind::Start;
    std::string message;
    std::string spec_ref;   // e.g. "§2.2.2.1"
};

using DiagList = std::vector<Diagnostic>;

// ── Timestamp ────────────────────────────────────────────────
struct Timestamp {
    int year   = 0;
    int month  = 0;
    int day    = 0;
    int hour   = 0;
    int minute = 0;
    int second = 0;
    bool operator==(Timestamp const&) const = default;
};

// ── Variant types for DE fields that accept value-or-pointer ─
// Positive = value, negative absolute value = DE pointer.
struct LineFontVariant {
    int raw = 0;  // positive=pattern, negative=pointer to Type 304
    bool is_pointer() const { return raw < 0; }
    LineFontPattern pattern() const { return static_cast<LineFontPattern>(raw); }
    DEIndex pointer() const { return DEIndex{-raw}; }
};

struct LevelVariant {
    int raw = 0;
    bool is_pointer() const { return raw < 0; }
    int level() const { return raw; }
    DEIndex pointer() const { return DEIndex{-raw}; }
};

struct ColorVariant {
    int raw = 0;
    bool is_pointer() const { return raw < 0; }
    Color color() const { return static_cast<Color>(raw); }
    DEIndex pointer() const { return DEIndex{-raw}; }
};

} // namespace iges
