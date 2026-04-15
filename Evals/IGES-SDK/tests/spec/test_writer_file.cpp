// Tests for the full IGES file writer.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "writer/file_writer.hpp"
#include "writer/entity_writer.hpp"
#include "model/global_section.hpp"
#include "model/directory_entry.hpp"

using namespace iges;

// -----------------------------------------------------------------
// Helper: count lines with a given section letter at col 73
// -----------------------------------------------------------------
static int count_section_lines(std::string const& file, char section_char) {
    int count = 0;
    std::size_t pos = 0;
    while (pos < file.size()) {
        auto nl = file.find('\n', pos);
        if (nl == std::string::npos) nl = file.size();
        auto line_len = nl - pos;
        if (line_len >= 73 && file[pos + 72] == section_char) {
            ++count;
        }
        pos = nl + 1;
    }
    return count;
}

// -----------------------------------------------------------------
// Basic file structure
// -----------------------------------------------------------------

TEST_CASE("write_iges_file -- minimal file has all 5 sections", "[writer][file]") {
    // A valid IGES file must have S, G, D, P, T sections
    GlobalSection g;
    g.product_id_sender = "test";
    g.file_name = "test.igs";
    g.native_system_id = "SDK";
    g.preprocessor_version = "1.0";
    g.integer_bits = 32;
    g.sp_magnitude = 38;
    g.sp_significance = 6;
    g.dp_magnitude = 308;
    g.dp_significance = 15;

    // One line entity
    LineEntity le;
    le.start = {0, 0, 0};
    le.terminate = {1, 1, 1};
    std::string pd = write_line_entity(le);

    DirectoryEntry de;
    de.entity_type = EntityType{110};

    WritableEntity we{de, pd};
    auto file = write_iges_file({"IGES-SDK test file"}, g, {we});

    // Check all sections present
    CHECK(count_section_lines(file, 'S') >= 1);
    CHECK(count_section_lines(file, 'G') >= 1);
    CHECK(count_section_lines(file, 'D') == 2);  // one entity = 2 DE lines
    CHECK(count_section_lines(file, 'P') >= 1);
    CHECK(count_section_lines(file, 'T') == 1);
}

TEST_CASE("write_iges_file -- all lines are 80 columns", "[writer][file]") {
    // §2.2.4: "Each line ... shall contain exactly 80 columns"
    GlobalSection g;
    g.product_id_sender = "test";
    g.file_name = "test.igs";
    g.native_system_id = "SDK";
    g.preprocessor_version = "1.0";
    g.integer_bits = 32;
    g.sp_magnitude = 38;
    g.sp_significance = 6;
    g.dp_magnitude = 308;
    g.dp_significance = 15;

    LineEntity le;
    le.start = {1, 2, 3};
    le.terminate = {4, 5, 6};
    std::string pd = write_line_entity(le);

    DirectoryEntry de;
    de.entity_type = EntityType{110};

    WritableEntity we{de, pd};
    auto file = write_iges_file({"test"}, g, {we});

    // Every line should be exactly 80 characters
    std::size_t pos = 0;
    int line_num = 0;
    while (pos < file.size()) {
        auto nl = file.find('\n', pos);
        if (nl == std::string::npos) break;
        ++line_num;
        auto line_len = nl - pos;
        INFO("Line " << line_num << " length = " << line_len);
        CHECK(line_len == 80);
        pos = nl + 1;
    }
}

TEST_CASE("write_iges_file -- terminate line counts match", "[writer][file]") {
    // §2.2.4.6: Terminate line encodes counts of S, G, D, P lines
    GlobalSection g;
    g.product_id_sender = "test";
    g.file_name = "test.igs";
    g.native_system_id = "SDK";
    g.preprocessor_version = "1.0";
    g.integer_bits = 32;
    g.sp_magnitude = 38;
    g.sp_significance = 6;
    g.dp_magnitude = 308;
    g.dp_significance = 15;

    // Two entities
    LineEntity le;
    le.start = {0, 0, 0};
    le.terminate = {1, 1, 1};

    DirectoryEntry de1;
    de1.entity_type = EntityType{110};
    WritableEntity we1{de1, write_line_entity(le)};

    PointEntity pe;
    pe.coords = {5, 5, 5};
    pe.display_symbol = DEIndex{0};

    DirectoryEntry de2;
    de2.entity_type = EntityType{116};
    WritableEntity we2{de2, write_point_entity(pe)};

    auto file = write_iges_file({"test"}, g, {we1, we2});

    int s = count_section_lines(file, 'S');
    int gn = count_section_lines(file, 'G');
    int d = count_section_lines(file, 'D');
    int p = count_section_lines(file, 'P');

    // Find terminate line: search for line with 'T' at col 73
    std::string t_line;
    {
        std::size_t pos2 = 0;
        while (pos2 < file.size()) {
            auto nl = file.find('\n', pos2);
            if (nl == std::string::npos) nl = file.size();
            if (nl - pos2 >= 73 && file[pos2 + 72] == 'T') {
                t_line = file.substr(pos2, 80);
                break;
            }
            pos2 = nl + 1;
        }
    }
    REQUIRE(t_line.size() == 80);

    // Parse counts from terminate line: S in cols 1-8, G in 9-16, D in 17-24, P in 25-32
    auto parse_count = [&](int col, char prefix) {
        auto field = t_line.substr(col, 8);
        CHECK(field[0] == prefix);
        // Parse the number from the remaining 7 chars
        int val = 0;
        for (int i = 1; i < 8; ++i) {
            if (field[i] >= '0' && field[i] <= '9') val = val * 10 + (field[i] - '0');
        }
        return val;
    };

    CHECK(parse_count(0, 'S') == s);
    CHECK(parse_count(8, 'G') == gn);
    CHECK(parse_count(16, 'D') == d);
    CHECK(parse_count(24, 'P') == p);
}

TEST_CASE("write_iges_file -- empty start section gets one line", "[writer][file]") {
    // §2.2.4.2: At least one Start line required
    GlobalSection g;
    g.product_id_sender = "test";
    g.file_name = "test.igs";
    g.native_system_id = "SDK";
    g.preprocessor_version = "1.0";
    g.integer_bits = 32;
    g.sp_magnitude = 38;
    g.sp_significance = 6;
    g.dp_magnitude = 308;
    g.dp_significance = 15;

    auto file = write_iges_file({}, g, {});
    CHECK(count_section_lines(file, 'S') == 1);
}
