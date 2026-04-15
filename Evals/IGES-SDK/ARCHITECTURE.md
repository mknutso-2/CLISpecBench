# IGES-SDK Architecture

A C++23 static library for reading, writing, and round-tripping IGES 5.3 files, focused on comprehensive entity coverage. Development follows strict Test-Driven Development: every spec requirement is a failing test before it is a line of production code.

---

## 1. Design Goals

| Priority | Goal |
|----------|------|
| P0 | **Test-first development.** Every requirement extracted from the IGES 5.3 specification is encoded as one or more unit tests. No production code is written without a failing test that motivates it. |
| P0 | Correct, spec-conformant round-trip of IGES Fixed Format files (read then write produces semantically equivalent output). |
| P1 | Full coverage of 87 IGES entity types: curve/surface geometry, CSG primitives, Boolean trees, B-Rep topology (MSBO chain), transformation matrices, subfigures, properties, associativities, annotation/dimensioning, FEA, and network subfigures. |
| P1 | Type-safe C++23 API using `std::expected`, strong typedefs (`DEIndex`, `EntityType`, `FormNumber`), and plain data structs with free-function parsers/writers. |
| P2 | Extensible: each entity is a self-contained header + source pair. Adding a new entity requires no modifications to existing code beyond registering it in CMakeLists.txt and the central writer. |
| P3 | Optional geometric evaluation utilities (B-spline evaluation, circular arc parameterization). |

Non-goals (at least initially): C++ modules, Binary Format (Appendix H, deprecated), MACRO entities (Type 306/600+), rendering/visualization.

---

## 2. TDD Methodology

### 2.1 The Red-Green-Refactor Cycle

Every unit of work follows this cycle:

1. **Red:** Write a test that encodes a specific requirement from the IGES 5.3 spec. The test references the spec section it derives from (e.g., `// §2.2.2.1: "The implicit default for an integer field is zero."`). The test fails because no production code exists yet.
2. **Green:** Write the minimum production code to make the test pass.
3. **Refactor:** Clean up the production code while keeping all tests green.

### 2.2 Requirement Traceability

Every test case is tagged with the spec section it validates:

```
TEST_CASE("§<section> — <requirement summary>", "[<module>][spec-<section>]")
```

For example:
```cpp
TEST_CASE("§2.2.2.1 — integer implicit default is zero", "[parser][spec-2.2.2.1]") { ... }
TEST_CASE("§4.3 — parse circular arc", "[entity][spec-4.3]") { ... }
TEST_CASE("§4.66 — round-trip radius dimension Form 1", "[entity][spec-4.66]") { ... }
```

### 2.3 Test Invariant Policy

A test must verify an **unequivocally unambiguous invariant**. If there is any question regarding how the reference documentation is to be interpreted, we do not test it. The test suite must never encode our *interpretation* of the spec as if it were the spec itself.

There are exactly three tiers:

1. **Spec says it clearly** — Test it. Quote the exact spec text in an inline comment.
2. **Spec is ambiguous, but the format breaks without it** — Test it. Add a comment explaining *why* this invariant is structurally necessary despite the ambiguity.
3. **Spec is ambiguous and the format could work either way** — Do **not** test it. No opinion-based assertions.

### 2.4 Test Categories

| Category | Location | Purpose |
|----------|----------|---------|
| **Spec requirement tests** | `tests/spec/test_<section>_*.cpp` | One test per extractable requirement from the IGES 5.3 spec. |
| **Entity parse/write tests** | `tests/spec/test_4_*_<entity>.cpp` | Parse from PD string, verify fields, round-trip through writer. |
| **Writer format tests** | `tests/spec/test_writer_*.cpp` | Verify Hollerith encoding, field formatting, PD/DE/file assembly. |
| **Round-trip tests** | `tests/spec/test_writer_roundtrip*.cpp`, `test_file_roundtrip.cpp` | Read entity/file, write, read again, compare. |
| **Geometric evaluation** | `tests/spec/test_geometric_evaluation.cpp` | B-spline evaluation, arc parameterization. |
| **Malformed input tests** | `tests/spec/test_malformed.cpp` | Deliberately broken input; assert graceful diagnostics, no crashes. |
| **Validation tests** | `tests/spec/test_validate.cpp` | Structural validation rules (e.g., B-spline knot vector length). |
| **Integration tests** | `tests/integration/test_reference_files.cpp` | Parse real-world `.igs` files, verify entity counts and key fields. |

### 2.5 Test Suite Status

The test suite currently contains **592 test cases** with **24,759 assertions**, all passing. Entity parsers and writers have been verified against the IGES 5.3 spec PDF through multiple rounds of independent auditing.

---

## 3. Architecture Overview

The SDK uses a **structs + free functions** architecture rather than an OOP class hierarchy. Each entity is a plain data struct. Parsing and writing are free functions that operate on those structs via `ParamTokenizer` and `ParamWriter`.

```
 .igs file  ──►  Lexer  ──►  FileReader  ──►  IgesFile
  bytes         lines/       entities/      GlobalSection +
                sections     DE + PD        RawEntity[]

 IgesFile   ──►  parse_*_entity()  ──►  Entity structs
                 (per-entity free       (plain data,
                  functions)             no inheritance)

 Entity structs ──►  write_*_entity()  ──►  PD strings
                     (per-entity free       (comma-sep,
                      functions)             semicolon-term)

 PD strings ──►  FileWriter  ──►  .igs file
                 (assembles DE     (80-column
                  + PD + sections)  fixed format)
```

### 3.1 Why Structs + Free Functions

IGES entities share almost no behavior. A `LineEntity` and a `BooleanTreeEntity` have nothing in common except that they both come from a PD record. Rather than forcing them into a class hierarchy with virtual dispatch, each entity is a self-contained struct:

```cpp
struct LineEntity {
    Vec3 start;
    Vec3 terminate;
};

std::expected<LineEntity, Diagnostic>
parse_line_entity(ParamTokenizer& tok);
```

This gives:
- Zero-overhead data access (no vtable, no indirection)
- Trivial serializability
- Compile-time exhaustive handling via overload sets
- Each entity is independently testable

---

## 4. Key Types

### 4.1 Fundamental Types (`src/types.hpp`)

```cpp
using Real = double;

struct DEIndex {                    // Strong-typed DE sequence number
    int value = 0;
    constexpr bool is_null() const;
};

struct EntityType { int value = 0; };
struct FormNumber { int value = 0; };

struct Diagnostic {
    enum class Severity { Info, Warning, Error };
    Severity    severity;
    int         line;
    SectionKind section;
    std::string message;
    std::string spec_ref;       // e.g. "§2.2.2.1"
};
```

All fallible functions return `std::expected<T, Diagnostic>` or `std::expected<T, DiagList>`.

Enumerations: `Units`, `SpecVersion`, `DraftingStandard`, `BlankStatus`, `SubordinateSwitch`, `EntityUseFlag`, `HierarchyFlag`, `LineFontPattern`, `Color`, `SectionKind`.

Variant types for DE fields that accept value-or-pointer: `LineFontVariant`, `LevelVariant`, `ColorVariant`.

### 4.2 Math Types (`src/entities/entity.hpp`)

```cpp
struct Vec3 {
    Real x = 0.0, y = 0.0, z = 0.0;
    // operator+, operator-, operator*, length(), length_sq()
};

struct Matrix3x3 {
    std::array<std::array<Real, 3>, 3> r = {{{1,0,0},{0,1,0},{0,0,1}}};
};

// Free functions: dot(), cross(), determinant(), multiply(), transpose()
```

### 4.3 File Model

```cpp
// Parsed from two 80-column DE lines
struct DirectoryEntry {
    EntityType entity_type;     // fields 1, 11
    int param_data_ptr;         // field 2
    StatusNumber status;        // field 9 (decomposed into 4 sub-fields)
    FormNumber form;            // field 15
    // ... all 20 DE fields
};

// The 26-field Global Section
struct GlobalSection {
    char param_delimiter = ',';
    char record_delimiter = ';';
    std::string product_id_sender;  // required
    // ... all 26 fields with spec-defined defaults
};

// One entity as extracted from the file
struct RawEntity {
    DirectoryEntry de;
    std::string pd_string;      // concatenated PD data
};

// Complete parsed file
struct IgesFile {
    std::vector<std::string> start_lines;
    GlobalSection global;
    std::vector<RawEntity> entities;
};
```

### 4.4 ParamTokenizer (`src/parser/param_tokenizer.hpp`)

Consumes a free-format PD string and produces typed field values:

```cpp
class ParamTokenizer {
public:
    ParamTokenizer(std::string_view data, char pd, char rd);

    std::expected<int, Diagnostic>         next_integer();
    std::expected<int, Diagnostic>         next_integer_or(int def);
    std::expected<Real, Diagnostic>        next_real();
    std::expected<Real, Diagnostic>        next_real_or(Real def);
    std::expected<DEIndex, Diagnostic>     next_pointer();
    std::expected<std::string, Diagnostic> next_string();
    std::expected<bool, Diagnostic>        next_logical();
    bool at_record_end() const;
};
```

### 4.5 ParamWriter (`src/writer/param_writer.hpp`)

The inverse of ParamTokenizer:

```cpp
class ParamWriter {
public:
    void write_integer(int v);
    void write_real(Real v);
    void write_string(std::string_view v);
    void write_pointer(DEIndex idx);
    void write_logical(bool v);
    void end_record();
    std::string const& str() const;
};
```

---

## 5. Entity Pattern

Every entity follows the same pattern. For entity Type `N`:

**Header** (`src/entities/<name>_entity.hpp`):
```cpp
struct FooEntity {
    // Fields matching the spec's PD parameter table
    DEIndex some_pointer;
    int some_count = 0;
    Real some_value = 0.0;
    std::vector<DEIndex> items;
};

std::expected<FooEntity, Diagnostic>
parse_foo_entity(ParamTokenizer& tok);
// Form-dependent entities add: parse_foo_entity(ParamTokenizer& tok, int form);
```

**Implementation** (`src/entities/<name>_entity.cpp`):
```cpp
std::expected<FooEntity, Diagnostic>
parse_foo_entity(ParamTokenizer& tok) {
    FooEntity e;
    auto p = tok.next_pointer(); if (!p) return std::unexpected(p.error()); e.some_pointer = *p;
    auto n = tok.next_integer(); if (!n) return std::unexpected(n.error()); e.some_count = *n;
    // ...
    return e;
}
```

**Writer** (`src/writer/entity_writer.cpp`):
```cpp
std::string write_foo_entity(FooEntity const& e) {
    ParamWriter pw;
    pw.write_pointer(e.some_pointer);
    pw.write_integer(e.some_count);
    // ... mirror of parser
    pw.end_record();
    return pw.str();
}
```

**Test** (`tests/spec/test_<section>_<name>.cpp`):
```cpp
TEST_CASE("§X.Y — parse foo", "[entity][spec-X.Y]") {
    ParamTokenizer tok("1,3,10.0;", ',', ';');
    auto r = parse_foo_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->some_pointer.value == 1);
}

TEST_CASE("§X.Y — round-trip foo", "[entity][spec-X.Y]") {
    FooEntity orig;
    orig.some_pointer = DEIndex{1};
    auto pd = write_foo_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_foo_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->some_pointer.value == 1);
}
```

### 5.1 Form-Dependent Entities

Some entities have different PD layouts depending on the DE Form Number. These take an `int form` parameter:

| Entity | Type | Forms |
|--------|------|-------|
| Drawing | 404 | 0 (3 fields/view), 1 (4 fields/view with ANGLE) |
| External Reference | 416 | 0/2/4 (EXTFID+EXTNAM), 1 (EXTFID only), 3 (EXTNAM only) |
| Line Font Definition | 304 | 1 (subfigure template), 2 (segment pattern + bitmask) |
| Ordinate Dimension | 218 | 0 (DENOTE+DEWIT), 1 (DENOTE+DEORD+DESUPP) |
| Radius Dimension | 222 | 0 (4 fields), 1 (5 fields with DEARRW2) |
| View | 410 | 0 (VNO+SCALE+clip planes), 1 (22-field perspective view) |
| Plane/Cylindrical/Conical/Spherical/Toroidal Surface | 190-198 | 0 (unparameterized), 1 (parameterized) |
| Attribute Table Definition | 322 | 0/1/2 |

---

## 6. Entity Catalog

87 entity types are implemented across all IGES categories:

**Geometry (26 types):** Circular Arc (100), Composite Curve (102), Conic Arc (104), Copious Data (106), Plane (108), Line (110), Parametric Spline Curve (112), Parametric Spline Surface (114), Point (116), Ruled Surface (118), Surface of Revolution (120), Tabulated Cylinder (122), Direction (123), Transformation Matrix (124), Flash (125), Rational B-Spline Curve (126), Rational B-Spline Surface (128), Offset Curve (130), Offset Surface (140), Boundary (141), Curve on Parametric Surface (142), Bounded Surface (143), Trimmed Surface (144), Null (0), Connect Point (132), Copious Data/Linear Path (106 Forms 11-13)

**CSG Primitives (13 types):** Block (150), Wedge (152), Right Circular Cylinder (154), Cone Frustum (156), Sphere (158), Torus (160), Solid of Revolution (162), Solid of Linear Extrusion (164), Ellipsoid (168), Boolean Tree (180), Selected Component (182), Solid Assembly (184), Solid Instance (430)

**B-Rep Topology (11 types):** MSBO (186), Plane Surface (190), Cylindrical Surface (192), Conical Surface (194), Spherical Surface (196), Toroidal Surface (198), Vertex List (502), Edge List (504), Loop (508), Face (510), Shell (514)

**Annotation/Dimensioning (16 types):** Angular Dimension (202), Curve Dimension (204), Diameter Dimension (206), Flag Note (208), General Label (210), General Note (212), New General Note (213), Leader Arrow (214), Linear Dimension (216), Ordinate Dimension (218), Point Dimension (220), Radius Dimension (222), General Symbol (228), Sectioned Area (230), Text Display Template (312), Text Font Definition (310)

**Structure (13 types):** Associativity Definition (302), Line Font Definition (304), Subfigure Definition (308), Color Definition (314), Units Data (316), Network Subfigure Definition (320), Attribute Table Definition (322), Associativity Instance (402), Drawing (404), Property (406), Subfigure Instance (408), View (410), External Reference (416)

**Arrays (2 types):** Rectangular Array (412), Circular Array (414)

**FEA (6 types):** Node (134), Finite Element (136), Nodal Displacement (138), Nodal Results (146), Element Results (148), Nodal Load/Constraint (418)

**Network (1 type):** Network Subfigure Instance (420)

---

## 7. Directory Layout

```
IGES-SDK/
  CMakeLists.txt
  ARCHITECTURE.md                     # This file
  IGES5-3.pdf                         # IGES 5.3 specification reference
  iges-5-3-specification.md           # Spec transcription (3D CAD subset)
  src/
    types.hpp / types.cpp             # Scalar aliases, strong typedefs, enums, Diagnostic
    entities/
      entity.hpp / entity.cpp         # Vec3, Matrix3x3, math helpers
      line_entity.hpp / .cpp          # Type 110
      circular_arc_entity.hpp / .cpp  # Type 100
      ...                             # 87 entity types, flat layout
    model/
      global_section.hpp / .cpp       # 26-field GlobalSection struct + parser
      directory_entry.hpp / .cpp      # 20-field DirectoryEntry struct + parser
      validate.hpp / .cpp             # Structural validation rules
    parser/
      lexer.hpp / .cpp                # 80-column line splitting, section detection
      param_tokenizer.hpp / .cpp      # Free-format PD field tokenizer
      file_reader.hpp / .cpp          # Two-pass file reader → IgesFile
    writer/
      format.hpp / .cpp               # Low-level formatters (Hollerith, integer, real, etc.)
      param_writer.hpp / .cpp         # ParamWriter (inverse of ParamTokenizer)
      global_writer.hpp / .cpp        # GlobalSection → PD string
      entity_writer.hpp / .cpp        # All write_*_entity() functions
      file_writer.hpp / .cpp          # IgesFile assembly → 80-column output
  tests/
    spec/                             # Spec-requirement + entity tests (109 files)
      test_2_2_*                      # §2 data types, free format, sections
      test_4_*                        # §4 entity parse/write/round-trip tests
      test_writer_*                   # Writer formatting and round-trip tests
      test_file_roundtrip.cpp         # Full file round-trip
      test_geometric_evaluation.cpp   # B-spline/arc evaluation
      test_malformed.cpp              # Malformed input handling
      test_validate.cpp               # Structural validation
    integration/
      test_reference_files.cpp        # Real-world .igs file parsing
    data/
      ex1.iges                        # IC library cell (subfigures, copious data)
      ex2.iges                        # Mechanical drawing (lines, arcs, annotations)
      ex3.iges                        # Views, drawings, transformations
```

---

## 8. Parsing Pipeline

```
 FILE  ──►  Lexer  ──►  FileReader  ──►  IgesFile
 bytes     80-col       two-pass        GlobalSection +
           lines        DE scan +       RawEntity[]
                        PD concat
```

`read_iges_file(std::istream&)` performs a two-pass read:

**Pass 1 — Structure scan:** Start section lines, Global section (26 fields), Directory Entry pairs (two 80-column lines each), Terminate section validation.

**Pass 2 — Parameter data concatenation:** For each DE, the corresponding PD lines (columns 1-64) are concatenated into a single `pd_string`. This string is stored in `RawEntity` alongside its `DirectoryEntry`.

Entity-specific parsing is **not** done by the file reader. Callers use the appropriate `parse_*_entity()` free function with a `ParamTokenizer` constructed from the `pd_string`:

```cpp
auto file = read_iges_file(input);
for (auto const& e : file->entities) {
    if (e.de.entity_type == EntityType{110}) {
        ParamTokenizer tok(e.pd_string, file->global.param_delimiter,
                           file->global.record_delimiter);
        auto line = parse_line_entity(tok);
    }
}
```

---

## 9. Writer Pipeline

```
 Entity structs  ──►  write_*_entity()  ──►  PD strings
 GlobalSection   ──►  write_iges_file() ──►  .igs file string
```

`write_iges_file()` assembles a complete IGES file:

1. Emit Start section lines (padded to 72 columns, 'S' in column 73).
2. Serialize `GlobalSection` to free-format PD, split into 72-column lines.
3. For each entity: split PD string into 64-column data lines, build two 80-column DE lines.
4. Emit Terminate section with correct section counts.
5. All sequence numbers computed from scratch.

---

## 10. Build System

- **CMake 3.28+**, single static library target `iges`.
- **C++23** (`CMAKE_CXX_STANDARD 23`), no extensions.
- **Compiler:** MSVC (Visual Studio 2026). No C++ module support used.
- **No external dependencies** for the core library.
- **Test framework:** Catch2 v3.7.1 via FetchContent. Tests discovered via `catch_discover_tests()`.

```cmake
cmake_minimum_required(VERSION 3.28)
project(IGES-SDK LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)

add_library(iges STATIC)
target_include_directories(iges PUBLIC src)
target_sources(iges PRIVATE
    src/types.cpp
    src/parser/param_tokenizer.cpp
    src/parser/lexer.cpp
    src/parser/file_reader.cpp
    src/model/global_section.cpp
    src/model/directory_entry.cpp
    src/model/validate.cpp
    src/entities/entity.cpp
    src/entities/line_entity.cpp
    # ... 87 entity .cpp files ...
    src/writer/format.cpp
    src/writer/param_writer.cpp
    src/writer/global_writer.cpp
    src/writer/entity_writer.cpp
    src/writer/file_writer.cpp
)

# Catch2 v3.7.1 via FetchContent
include(FetchContent)
FetchContent_Declare(Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG        v3.7.1)
FetchContent_MakeAvailable(Catch2)

file(GLOB_RECURSE TEST_SOURCES tests/*.cpp)
add_executable(iges_tests ${TEST_SOURCES})
target_link_libraries(iges_tests PRIVATE iges Catch2::Catch2WithMain)
catch_discover_tests(iges_tests)
```

---

## 11. Design Rationale

**Why structs + free functions instead of a class hierarchy?**
IGES entities share almost no behavior. A flat struct per entity with free-function parse/write is simpler, more testable, and produces zero-overhead data access. There is no need for virtual dispatch, runtime polymorphism, or an entity registry — callers match on `EntityType` and call the appropriate parser directly.

**Why strong-typed indices instead of raw pointers?**
IGES files use sequence-number-based pointers. `DEIndex` keeps the model trivially serializable, mutations don't invalidate references, and dangling-pointer bugs are eliminated.

**Why `std::expected` over exceptions?**
IGES files in the wild are frequently malformed. The parser must accumulate diagnostics and continue. `std::expected` makes error paths explicit and composable without the overhead of exception unwinding.

**Why a two-pass reader?**
Forward references (DE field 7, PD pointers to other entities). The first pass scans all DE records so that PD pointers can be validated during the second pass. The DE scan is cheap (two fixed-width lines per entity).

**Why a central `entity_writer.cpp` instead of per-entity writers?**
All `write_*_entity()` functions share the same pattern (construct `ParamWriter`, write fields, `end_record()`). Keeping them in one file makes it easy to audit writer/parser symmetry across all entity types. Each function is small (5-15 lines) and self-contained.

**Why C++23?**
`std::expected` (the core error-handling mechanism) is a C++23 feature. The codebase also uses defaulted comparison operators, structured bindings, and `constexpr` features from C++20/23.
