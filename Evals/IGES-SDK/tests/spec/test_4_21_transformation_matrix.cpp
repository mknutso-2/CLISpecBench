// Tests for §4.21 — Transformation Matrix Entity (Type 124).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/transformation_matrix_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include <cmath>
#include <numbers>

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// ─────────────────────────────────────────────────────────────────
// §4.21: "Parameters: R11, R12, R13, T1, R21, R22, R23, T2,
//   R31, R32, R33, T3" — 12 reals in row-major order
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.21 — parse identity transformation matrix", "[entity][spec-4.21]") {
    // §4.21: "Parameters: R11, R12, R13, T1, R21, R22, R23, T2,
    //   R31, R32, R33, T3"
    ParamTokenizer tok("1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.;", ',', ';');
    auto r = parse_transformation_matrix_entity(tok);
    REQUIRE(r.has_value());
    auto& tm = r.value();
    // Identity rotation
    CHECK_THAT(tm.rotation(0,0), WithinRel(1.0));
    CHECK_THAT(tm.rotation(0,1), WithinAbs(0.0, 1e-15));
    CHECK_THAT(tm.rotation(0,2), WithinAbs(0.0, 1e-15));
    CHECK_THAT(tm.rotation(1,0), WithinAbs(0.0, 1e-15));
    CHECK_THAT(tm.rotation(1,1), WithinRel(1.0));
    CHECK_THAT(tm.rotation(1,2), WithinAbs(0.0, 1e-15));
    CHECK_THAT(tm.rotation(2,0), WithinAbs(0.0, 1e-15));
    CHECK_THAT(tm.rotation(2,1), WithinAbs(0.0, 1e-15));
    CHECK_THAT(tm.rotation(2,2), WithinRel(1.0));
    // Zero translation
    CHECK_THAT(tm.translation.x, WithinAbs(0.0, 1e-15));
    CHECK_THAT(tm.translation.y, WithinAbs(0.0, 1e-15));
    CHECK_THAT(tm.translation.z, WithinAbs(0.0, 1e-15));
}

TEST_CASE("§4.21 — parse spec example rotation", "[entity][spec-4.21]") {
    // §4.21: Rotation R = [[0,0,1],[0,1,0],[-1,0,0]], T = [0,0,0]
    ParamTokenizer tok("0.,0.,1.,0.,0.,1.,0.,0.,-1.,0.,0.,0.;", ',', ';');
    auto r = parse_transformation_matrix_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r.value().rotation(0,2), WithinRel(1.0));
    CHECK_THAT(r.value().rotation(2,0), WithinRel(-1.0));
}

TEST_CASE("§4.21 — parse with translation", "[entity][spec-4.21]") {
    // §4.21: "T1, T2, T3" are the translation components
    ParamTokenizer tok("1.,0.,0.,10.,0.,1.,0.,20.,0.,0.,1.,30.;", ',', ';');
    auto r = parse_transformation_matrix_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r.value().translation.x, WithinRel(10.0));
    CHECK_THAT(r.value().translation.y, WithinRel(20.0));
    CHECK_THAT(r.value().translation.z, WithinRel(30.0));
}

// ─────────────────────────────────────────────────────────────────
// §4.21: "transforms three-row column vectors by means of a
//   matrix multiplication and then a vector addition"
//   i.e., result = R * point + T
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.21 — apply identity leaves point unchanged", "[entity][spec-4.21]") {
    // §4.21: "R * point + T" with R=identity, T=0 → point unchanged
    TransformationMatrixEntity tm;
    tm.rotation = Matrix3x3{};  // identity
    tm.translation = {0, 0, 0};
    auto p = tm.apply({1, 2, 3});
    CHECK_THAT(p.x, WithinRel(1.0));
    CHECK_THAT(p.y, WithinRel(2.0));
    CHECK_THAT(p.z, WithinRel(3.0));
}

TEST_CASE("§4.21 — apply pure translation", "[entity][spec-4.21]") {
    // §4.21: "R * point + T" with R=identity → result = point + T
    TransformationMatrixEntity tm;
    tm.rotation = Matrix3x3{};
    tm.translation = {10, 20, 30};
    auto p = tm.apply({1, 2, 3});
    CHECK_THAT(p.x, WithinRel(11.0));
    CHECK_THAT(p.y, WithinRel(22.0));
    CHECK_THAT(p.z, WithinRel(33.0));
}

TEST_CASE("§4.21 — apply spec example rotation to unit-X", "[entity][spec-4.21]") {
    // §4.21: R = [[0,0,1],[0,1,0],[-1,0,0]], T = [0,0,0]
    //   R * [1,0,0] = [0,0,-1]
    TransformationMatrixEntity tm;
    tm.rotation.r = {{{0,0,1},{0,1,0},{-1,0,0}}};
    tm.translation = {0, 0, 0};
    auto p = tm.apply({1, 0, 0});
    CHECK_THAT(p.x, WithinAbs(0.0, 1e-15));
    CHECK_THAT(p.y, WithinAbs(0.0, 1e-15));
    CHECK_THAT(p.z, WithinRel(-1.0));
}

// ─────────────────────────────────────────────────────────────────
// §3.2.3: "If the Transformation Matrix Entity, referenced by
//   DE Field 7, points to another Transformation Matrix Entity,
//   ... the resultant transformation is the composition"
//   R_result = R2 * R1, T_result = R2 * T1 + T2
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§3.2.3 — compose two translations", "[entity][spec-3.2.3]") {
    // §3.2.3: Composition: R = R2*R1, T = R2*T1 + T2
    TransformationMatrixEntity tm1;
    tm1.rotation = Matrix3x3{};
    tm1.translation = {1, 0, 0};

    TransformationMatrixEntity tm2;
    tm2.rotation = Matrix3x3{};
    tm2.translation = {0, 2, 0};

    auto composed = tm2.compose(tm1);
    auto p = composed.apply({0, 0, 0});
    CHECK_THAT(p.x, WithinRel(1.0));
    CHECK_THAT(p.y, WithinRel(2.0));
    CHECK_THAT(p.z, WithinAbs(0.0, 1e-15));
}

TEST_CASE("§3.2.3 — compose rotation then translation", "[entity][spec-3.2.3]") {
    // §3.2.3: Composition: apply tm1 first, then tm2
    //   tm1: 90° Z rotation, tm2: translate (5,0,0)
    //   (1,0,0) → R1*(1,0,0) = (0,1,0) → + T2 = (5,1,0)
    TransformationMatrixEntity tm1;
    tm1.rotation.r = {{{0,-1,0},{1,0,0},{0,0,1}}};
    tm1.translation = {0, 0, 0};

    TransformationMatrixEntity tm2;
    tm2.rotation = Matrix3x3{};
    tm2.translation = {5, 0, 0};

    auto composed = tm2.compose(tm1);
    auto p = composed.apply({1, 0, 0});
    CHECK_THAT(p.x, WithinAbs(5.0, 1e-12));
    CHECK_THAT(p.y, WithinAbs(1.0, 1e-12));
    CHECK_THAT(p.z, WithinAbs(0.0, 1e-12));
}

// ─────────────────────────────────────────────────────────────────
// §4.21: "Form 0: R is an orthogonal matrix with determinant = +1
//   (proper rotation)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.21 — Form 0 identity has determinant +1", "[entity][spec-4.21]") {
    // §4.21: "Form 0 ... determinant of [R] equals +1"
    Matrix3x3 m{};  // identity
    CHECK_THAT(determinant(m), WithinRel(1.0));
}

TEST_CASE("§4.21 — 90-degree Z rotation has determinant +1", "[entity][spec-4.21]") {
    // §4.21: "Form 0 ... determinant of [R] equals +1"
    Matrix3x3 m;
    m.r = {{{0,-1,0},{1,0,0},{0,0,1}}};
    CHECK_THAT(determinant(m), WithinRel(1.0));
}

// ─────────────────────────────────────────────────────────────────
// §4.21: "Form 1: ... the determinant of [R] equals -1
//   (reflection or improper rotation)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.21 — Form 1 reflection has determinant -1", "[entity][spec-4.21]") {
    // §4.21: "Form 1 ... the determinant of [R] equals -1"
    Matrix3x3 m;
    m.r = {{{1,0,0},{0,1,0},{0,0,-1}}};
    CHECK_THAT(determinant(m), WithinRel(-1.0));
}

// ─────────────────────────────────────────────────────────────────
// §4.21: Matrix operations — multiplication, transpose
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.21 — matrix multiply identity * identity = identity", "[entity][spec-4.21]") {
    // §4.21: Matrix multiplication used for R_result = R2 * R1
    Matrix3x3 id{};
    auto r = multiply(id, id);
    for (int i = 0; i < 3; ++i)
        for (int j = 0; j < 3; ++j)
            CHECK_THAT(r(i,j), WithinAbs(i == j ? 1.0 : 0.0, 1e-15));
}

TEST_CASE("§4.21 — transpose of identity is identity", "[entity][spec-4.21]") {
    // §4.21: "R is an orthogonal matrix" — R^T = R^{-1}
    Matrix3x3 id{};
    auto t = transpose(id);
    CHECK(t == id);
}

TEST_CASE("§4.21 — transpose of rotation satisfies R^T * R = I", "[entity][spec-4.21]") {
    // §4.21: "R is an orthogonal matrix" — R^T * R = I for proper rotations
    Matrix3x3 m;
    m.r = {{{0,-1,0},{1,0,0},{0,0,1}}};
    auto mt = transpose(m);
    auto prod = multiply(mt, m);
    for (int i = 0; i < 3; ++i)
        for (int j = 0; j < 3; ++j)
            CHECK_THAT(prod(i,j), WithinAbs(i == j ? 1.0 : 0.0, 1e-12));
}
