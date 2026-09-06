#include <algorithm>
#include <cctype>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

enum class ExitCode {
    kSuccess = 0,
    kInvalidInput = 1,
    kInternalError = 2,
};

enum class CoordinateMode {
    kAbsolute,
    kIncremental,
};

enum class Plane {
    kXY,
    kXZ,
    kYZ,
};

enum class LengthUnit {
    kInches,
    kMillimeters,
};

enum class SpindleDirection {
    kClockwise,
    kCounterClockwise,
    kOff,
};

enum class CutterCompSide {
    kOff,
    kLeft,
    kRight,
};

struct Position {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double a = 0.0;
    double b = 0.0;
    double c = 0.0;
};

struct Point2D {
    double x = 0.0;
    double y = 0.0;
};

struct ParameterWrite {
    int index = 0;
    double value = 0.0;
};

struct ToolTableEntry {
    double tool_length_offset = 0.0;
    double diameter = 0.0;
};

struct CannedCycleStickyState {
    std::optional<double> retract_word;
    std::optional<char> depth_axis_letter;
    std::optional<double> depth_word;
};

struct ProbeBox {
    double x_min = 0.0;
    double x_max = 0.0;
    double y_min = 0.0;
    double y_max = 0.0;
    double z_min = 0.0;
    double z_max = 0.0;
    LengthUnit unit = LengthUnit::kInches;
};

constexpr int kMinParameterIndex = 1;
// The file range in 3.2.1 includes 5400; program reads/settings in
// 3.3.2.2 and 3.3.3 retain the narrower upper bound 5399.
constexpr int kMaxParameterIndex = 5399;
constexpr int kMaxParameterFileIndex = 5400;
constexpr int kParameterCount = kMaxParameterFileIndex + 1;
constexpr int kProbeTripXParameter = 5061;
constexpr int kProbeTripYParameter = 5062;
constexpr int kProbeTripZParameter = 5063;
constexpr int kProbeTripAParameter = 5064;
constexpr int kProbeTripBParameter = 5065;
constexpr int kProbeTripCParameter = 5066;
constexpr int kSelectedCoordinateSystemParameter = 5220;
constexpr int kG92XAxisOffsetParameter = 5211;
constexpr int kG92YAxisOffsetParameter = 5212;
constexpr int kG92ZAxisOffsetParameter = 5213;
constexpr int kG92AAxisOffsetParameter = 5214;
constexpr int kG92BAxisOffsetParameter = 5215;
constexpr int kG92CAxisOffsetParameter = 5216;
constexpr double kNearIntegerTolerance = 0.0001;
constexpr double kMillimetersPerInch = 25.4;

std::map<std::string, Position> make_default_coordinate_system_offsets() {
    return {
        {"1", {}},
        {"2", {}},
        {"3", {}},
        {"4", {}},
        {"5", {}},
        {"6", {}},
        {"7", {}},
        {"8", {}},
        {"9", {}},
    };
}

std::vector<double> make_default_parameters() {
    std::vector<double> parameters(kParameterCount, 0.0);
    parameters[kSelectedCoordinateSystemParameter] = 1.0;
    return parameters;
}

std::vector<bool> make_default_reported_parameters() {
    std::vector<bool> reported_parameters(kParameterCount, false);
    reported_parameters[kSelectedCoordinateSystemParameter] = true;
    return reported_parameters;
}

std::vector<std::optional<LengthUnit>> make_default_parameter_length_units() {
    return std::vector<std::optional<LengthUnit>>(kParameterCount, std::nullopt);
}

struct MachineState {
    // RS274 section 3.4 makes startup modal settings effective before the
    // first block. Publish the interpreter's chosen defaults alongside the
    // matching state fields below, including Table 2's default 5220=1 (G54).
    // An empty percent-delimited program must report those active modes too.
    std::map<std::string, std::string> active_modal_g_codes{
        {"1", "G0"}, {"2", "G17"}, {"3", "G90"}, {"5", "G94"}, {"6", "G20"},
        {"7", "G40"}, {"8", "G49"}, {"10", "G98"}, {"12", "G54"}, {"13", "G64"},
    };
    std::map<std::string, std::string> active_modal_m_codes{
        {"7", "M5"}, {"8", "M9"}, {"9", "M48"},
    };
    std::map<std::string, Position> coordinate_system_offsets = make_default_coordinate_system_offsets();
    std::map<int, ToolTableEntry> tool_table;
    std::vector<double> parameters = make_default_parameters();
    std::vector<bool> reported_parameters = make_default_reported_parameters();
    std::vector<std::optional<LengthUnit>> parameter_length_units = make_default_parameter_length_units();
    Position machine_position{};
    Position g92_axis_offsets{};
    double feed_rate = 0.0;
    double spindle_speed = 0.0;
    SpindleDirection spindle_direction = SpindleDirection::kOff;
    std::optional<int> cutter_radius_compensation_number;
    CutterCompSide cutter_comp_side = CutterCompSide::kOff;
    bool pending_first_cutter_comp_move = false;
    std::optional<Point2D> cutter_comp_programmed_xy;
    std::optional<Point2D> cutter_comp_last_linear_direction;
    std::optional<int> tool_length_offset_index;
    std::optional<double> active_tool_length_offset;
    std::optional<LengthUnit> active_tool_length_offset_unit;
    std::optional<int> selected_tool;
    std::optional<int> tool_in_spindle;
    std::optional<int> carousel_slots;
    std::optional<ProbeBox> probe_box;
    std::optional<int> probe_tool_number;
    CannedCycleStickyState canned_cycle_sticky_state;
    CoordinateMode coordinate_mode = CoordinateMode::kAbsolute;
    Plane selected_plane = Plane::kXY;
    LengthUnit current_length_unit = LengthUnit::kInches;
    std::string selected_coordinate_system = "1";
};

struct ProgramOptions {
    std::string input_path;
    std::string output_path;
    bool block_delete = false;
    std::optional<int> carousel_slots;
    std::optional<std::string> parameter_input_path;
    std::optional<std::string> parameter_output_path;
    std::optional<std::string> tool_table_path;
    std::optional<ProbeBox> probe_box;
    std::optional<int> probe_tool_number;
};

struct ParsedLine {
    std::map<std::string, std::string> active_modal_g_codes;
    std::map<std::string, std::string> active_modal_m_codes;
    std::vector<ParameterWrite> parameter_writes;
    std::optional<double> x;
    std::optional<double> y;
    std::optional<double> z;
    std::optional<double> a;
    std::optional<double> b;
    std::optional<double> c;
    std::optional<int> d;
    std::optional<int> h;
    std::optional<double> i;
    std::optional<double> j;
    std::optional<double> k;
    std::optional<double> l;
    std::optional<double> p;
    std::optional<double> q;
    std::optional<double> r;
    std::optional<int> t;
    std::optional<std::string> coordinate_system_offset_target;
    std::optional<std::string> g92_command;
    std::optional<std::string> home_command;
    std::optional<double> feed_rate;
    std::optional<double> spindle_speed;
    std::optional<SpindleDirection> spindle_direction;
    bool has_g4 = false;
    bool has_g10 = false;
    bool use_machine_coordinates = false;
    bool end_program = false;
};

class InputError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

ProgramOptions parse_command_line(int argc, char* argv[]);
MachineState execute_program(
    const std::string& input_path,
    bool block_delete,
    const std::optional<int>& carousel_slots,
    const std::optional<std::string>& parameter_input_path,
    const std::optional<std::string>& tool_table_path,
    const std::optional<ProbeBox>& probe_box,
    const std::optional<int>& probe_tool_number
);
void load_parameter_file(const std::string& parameter_input_path, MachineState& state);
void load_tool_table(const std::string& tool_table_path, MachineState& state);
void initialize_state_from_parameters(MachineState& state);
ParsedLine parse_line(std::string_view raw_line, const MachineState& state);
void apply_line(const ParsedLine& parsed_line, MachineState& state);
template <typename T>
void assign_unique_word(std::optional<T>& destination, T value, std::string_view word);
std::string remove_ignorable_whitespace(std::string_view line);
double parse_numeric_literal(std::string_view text, std::size_t& position);
double parse_real_value(std::string_view text, std::size_t& position, const MachineState& state);
double parse_expression(std::string_view text, std::size_t& position, const MachineState& state);
double parse_expression_group3(std::string_view text, std::size_t& position, const MachineState& state);
double parse_expression_group2(std::string_view text, std::size_t& position, const MachineState& state);
double parse_expression_group1(std::string_view text, std::size_t& position, const MachineState& state);
double parse_atomic_real_value(std::string_view text, std::size_t& position, const MachineState& state);
double parse_parameter_value(std::string_view text, std::size_t& position, const MachineState& state);
double parse_unary_operation_value(std::string_view text, std::size_t& position, const MachineState& state);
int parse_parameter_index(std::string_view text, std::size_t& position, const MachineState& state);
int require_parameter_index(double value);
int require_non_negative_integer(double value, std::string_view word);
void validate_tool_slot_number(
    const MachineState& state,
    int slot_number,
    std::string_view letter,
    bool allow_zero
);
bool is_close_to_integer(double value);
int round_if_close_to_integer(double value, std::string_view error_message);
int round_g_code_tenths_if_close(double value);
void parse_segment(std::string_view text, std::size_t& position, const MachineState& state, ParsedLine& parsed_line);
void parse_parameter_setting(
    std::string_view text,
    std::size_t& position,
    const MachineState& state,
    ParsedLine& parsed_line
);
void parse_word_segment(
    std::string_view text,
    std::size_t& position,
    const MachineState& state,
    ParsedLine& parsed_line
);
void parse_line_number(std::string_view text, std::size_t& position);
void apply_program_axis_value(
    std::optional<double> value,
    double& machine_axis,
    CoordinateMode coordinate_mode,
    double coordinate_system_offset
);
void apply_coordinate_system_axis_value(std::optional<double> value, double& axis);
void apply_g_code_value(double value, ParsedLine& parsed_line);
void apply_g_code_word(const std::string& word, ParsedLine& parsed_line);
void apply_m_code_value(double value, ParsedLine& parsed_line);
void apply_m_code_word(const std::string& word, ParsedLine& parsed_line);
bool has_xy_axis_word(const ParsedLine& parsed_line);
bool is_arc_motion(std::string_view active_gcode);
bool is_linear_motion(std::string_view active_gcode);
bool is_any_canned_cycle_motion(std::string_view active_gcode);
bool is_supported_canned_cycle_motion(std::string_view active_gcode);
bool is_feed_rate_motion(std::string_view active_gcode);
Plane plane_for_g_code(std::string_view active_gcode);
double resolved_program_axis_endpoint(
    std::optional<double> value,
    double current_machine_axis,
    CoordinateMode coordinate_mode,
    double coordinate_system_offset
);
bool has_linear_axis_word(const ParsedLine& parsed_line);
bool line_has_motion_axis_word(const ParsedLine& parsed_line);
bool line_mentions_canned_cycle_words(const ParsedLine& parsed_line);
bool is_probe_motion(std::string_view active_gcode);
void validate_linear_motion_command(const ParsedLine& parsed_line, const MachineState& state);
void validate_arc_command(const ParsedLine& parsed_line, const MachineState& state);
void validate_canned_cycle_command(
    const ParsedLine& parsed_line,
    const MachineState& state,
    std::string_view prior_motion_gcode
);
void register_non_modal_g_code(ParsedLine& parsed_line, std::string_view active_gcode);
void register_modal_g_code(
    ParsedLine& parsed_line,
    std::string_view group_number,
    std::string_view active_gcode
);
void register_modal_m_code(
    ParsedLine& parsed_line,
    std::string_view group_number,
    std::string_view active_mcode
);
std::string coordinate_system_number_for_g_code(std::string_view active_gcode);
std::string active_g_code_for_coordinate_system_number(int system_number);
int parameter_index_for_coordinate_system_axis(int system_number, int axis_index);
bool decode_coordinate_system_axis_parameter(int parameter_index, int& system_number, int& axis_index);
int parameter_index_for_home_axis(bool secondary_home, int axis_index);
bool decode_home_axis_parameter(int parameter_index, bool& secondary_home, int& axis_index);
bool decode_g92_axis_parameter(int parameter_index, int& axis_index);
bool axis_uses_length_units(int axis_index);
double position_axis_value(const Position& position, int axis_index);
double& position_axis_ref(Position& position, int axis_index);
std::optional<double> parsed_line_axis_word(const ParsedLine& parsed_line, int axis_index);
void set_parameter_value(
    MachineState& state,
    int parameter_index,
    double value,
    std::optional<LengthUnit> length_unit = std::nullopt
);
void set_selected_coordinate_system(MachineState& state, int system_number);
void set_coordinate_system_axis(MachineState& state, int system_number, int axis_index, double value);
void set_g92_axis_offset(MachineState& state, int axis_index, double value);
void reset_g92_axis_offsets(MachineState& state, bool reset_parameters);
void restore_g92_axis_offsets_from_parameters(MachineState& state);
double active_program_origin_offset_for_axis(const MachineState& state, int axis_index);
void apply_home_return(MachineState& state, const ParsedLine& parsed_line, bool secondary_home);
bool point_is_inside_probe_box(const Position& point, const ProbeBox& probe_box, LengthUnit current_unit);
std::optional<Position> find_probe_trip_point(
    const Position& start,
    const Position& programmed_point,
    const ProbeBox& probe_box,
    LengthUnit current_unit
);
void apply_probe_motion(MachineState& state, const ParsedLine& parsed_line);
void apply_canned_cycle_motion(
    MachineState& state,
    const ParsedLine& parsed_line,
    std::string_view active_gcode,
    bool same_cycle_already_active
);
double convert_length_value(double value, LengthUnit from, LengthUnit to);
void convert_position_in_place(Position& position, LengthUnit from, LengthUnit to);
LengthUnit length_unit_for_g_code(std::string_view active_gcode);
void apply_length_unit_change(MachineState& state, LengthUnit new_unit);
double parameter_length_value_in_current_units(const MachineState& state, int parameter_index);
double active_tool_length_offset_in_current_units(const MachineState& state);
void apply_tool_length_offset_change(MachineState& state, std::optional<int> new_index);
bool cutter_radius_compensation_is_active(const MachineState& state);
CutterCompSide cutter_comp_side_for_g_code(std::string_view active_gcode);
void activate_cutter_radius_compensation(
    MachineState& state,
    CutterCompSide side,
    std::optional<int> d_number
);
void deactivate_cutter_radius_compensation(MachineState& state);
double active_cutter_radius(const MachineState& state);
Point2D resolve_programmed_xy_endpoint(const ParsedLine& parsed_line, const MachineState& state);
Point2D resolve_current_programmed_xy(const MachineState& state);
bool cutter_comp_arc_offsets_outward(std::string_view motion_gcode, CutterCompSide side);
Point2D resolve_center_format_arc_center(
    Point2D programmed_start,
    const ParsedLine& parsed_line
);
Point2D resolve_radius_format_arc_center(
    Point2D programmed_start,
    Point2D programmed_endpoint,
    double radius_word,
    std::string_view motion_gcode
);
Point2D resolve_first_cutter_comp_radius_format_arc_center(
    Point2D current_tool_center,
    Point2D programmed_endpoint,
    double programmed_arc_radius,
    double tool_center_arc_radius,
    double radius_word,
    std::string_view motion_gcode
);
double compensated_arc_radius(
    double programmed_arc_radius,
    double tool_radius,
    bool offsets_outward
);
Point2D compute_first_cutter_comp_linear_endpoint(
    Point2D current_tool_center,
    Point2D programmed_endpoint,
    double tool_radius,
    CutterCompSide side
);
void apply_cutter_compensated_linear_xy_motion(MachineState& state, const ParsedLine& parsed_line);
void apply_cutter_compensated_arc_xy_motion(MachineState& state, const ParsedLine& parsed_line);
void apply_parameter_writes(const ParsedLine& parsed_line, MachineState& state);
void reset_after_program_end(MachineState& state);
std::string parse_g10_coordinate_system_number(const ParsedLine& parsed_line);
std::string strip_comments(std::string_view raw_line);
std::string json_escape(std::string_view text);
std::string to_json(const MachineState& state, std::optional<std::string_view> error = std::nullopt);
bool is_required_parameter(int parameter_index);
std::string to_parameter_file(const MachineState& state);
std::string to_string(SpindleDirection direction);
void write_output_file(const std::string& output_path, const std::string& contents);

ProgramOptions parse_command_line(int argc, char* argv[]) {
    ProgramOptions options;
    auto parse_double_argument = [](const char* text, std::string_view argument_name) {
        try {
            std::size_t parsed_length = 0;
            const double value = std::stod(text, &parsed_length);
            if (parsed_length != std::string_view(text).size()) {
                throw InputError(
                    "Expected numeric value for " + std::string(argument_name)
                );
            }
            return value;
        } catch (const std::invalid_argument&) {
            throw InputError("Expected numeric value for " + std::string(argument_name));
        } catch (const std::out_of_range&) {
            throw InputError("Numeric value out of range for " + std::string(argument_name));
        }
    };
    auto parse_non_negative_integer_argument = [](const char* text, std::string_view argument_name) {
        try {
            std::size_t parsed_length = 0;
            const int value = std::stoi(text, &parsed_length);
            if (parsed_length != std::string_view(text).size() || value < 0) {
                throw InputError(
                    "Expected non-negative integer value for " + std::string(argument_name)
                );
            }
            return value;
        } catch (const std::invalid_argument&) {
            throw InputError(
                "Expected non-negative integer value for " + std::string(argument_name)
            );
        } catch (const std::out_of_range&) {
            throw InputError("Integer value out of range for " + std::string(argument_name));
        }
    };

    for (int index = 1; index < argc; ++index) {
        const std::string argument = argv[index];
        if (argument == "--input" && index + 1 < argc) {
            options.input_path = argv[++index];
            continue;
        }
        if (argument == "--output" && index + 1 < argc) {
            options.output_path = argv[++index];
            continue;
        }
        if (argument == "--block-delete") {
            options.block_delete = true;
            continue;
        }
        if (argument == "--carousel-slots" && index + 1 < argc) {
            options.carousel_slots =
                parse_non_negative_integer_argument(argv[++index], "--carousel-slots");
            continue;
        }
        if (argument == "--parameter-input" && index + 1 < argc) {
            options.parameter_input_path = argv[++index];
            continue;
        }
        if (argument == "--parameter-output" && index + 1 < argc) {
            options.parameter_output_path = argv[++index];
            continue;
        }
        if (argument == "--tool-table" && index + 1 < argc) {
            options.tool_table_path = argv[++index];
            continue;
        }
        if (argument == "--probe-box" && index + 6 < argc) {
            const double x_min = parse_double_argument(argv[++index], "--probe-box");
            const double x_max = parse_double_argument(argv[++index], "--probe-box");
            const double y_min = parse_double_argument(argv[++index], "--probe-box");
            const double y_max = parse_double_argument(argv[++index], "--probe-box");
            const double z_min = parse_double_argument(argv[++index], "--probe-box");
            const double z_max = parse_double_argument(argv[++index], "--probe-box");
            if (x_min > x_max || y_min > y_max || z_min > z_max) {
                throw InputError("Probe-box ranges must be ordered min then max");
            }
            options.probe_box = ProbeBox{x_min, x_max, y_min, y_max, z_min, z_max};
            continue;
        }
        if (argument == "--probe-tool" && index + 1 < argc) {
            options.probe_tool_number =
                parse_non_negative_integer_argument(argv[++index], "--probe-tool");
            continue;
        }

        throw InputError(
            "Usage: rs274_reference --input <gcode_file> --output <result_file> "
            "[--block-delete] "
            "[--carousel-slots <slot_count>] [--parameter-input <parameter_file>] "
            "[--parameter-output <parameter_file>] [--tool-table <tool_file>] "
            "[--probe-box <x_min> <x_max> <y_min> <y_max> <z_min> "
            "<z_max>] [--probe-tool <tool_number>]"
        );
    }

    if (options.input_path.empty() || options.output_path.empty()) {
        throw InputError(
            "Usage: rs274_reference --input <gcode_file> --output <result_file> "
            "[--block-delete] "
            "[--carousel-slots <slot_count>] [--parameter-input <parameter_file>] "
            "[--parameter-output <parameter_file>] [--tool-table <tool_file>] "
            "[--probe-box <x_min> <x_max> <y_min> <y_max> <z_min> "
            "<z_max>] [--probe-tool <tool_number>]"
        );
    }

    return options;
}

MachineState execute_program(
    const std::string& input_path,
    bool block_delete,
    const std::optional<int>& carousel_slots,
    const std::optional<std::string>& parameter_input_path,
    const std::optional<std::string>& tool_table_path,
    const std::optional<ProbeBox>& probe_box,
    const std::optional<int>& probe_tool_number
) {
    std::ifstream input_stream(input_path);
    if (!input_stream.is_open()) {
        throw InputError("Could not open input file: " + input_path);
    }

    MachineState state;
    state.carousel_slots = carousel_slots;
    state.probe_box = probe_box;
    state.probe_tool_number = probe_tool_number;
    if (parameter_input_path.has_value()) {
        load_parameter_file(*parameter_input_path, state);
        initialize_state_from_parameters(state);
    }
    if (tool_table_path.has_value()) {
        load_tool_table(*tool_table_path, state);
    }

    // RS274 3.1: a percent-delimited file ends at its second percent line;
    // require that closing delimiter even if an M2/M30 appears first.
    // Preserve the existing plain-EOF behavior; delimiter parsing is separate
    // from the unresolved EOF policy and must not synthesize M2/M30 resets.
    std::vector<std::string> lines;
    std::string line;
    while (std::getline(input_stream, line)) {
        lines.push_back(line);
    }
    std::size_t first = 0;
    std::size_t end = lines.size();
    while (first < end && remove_ignorable_whitespace(lines[first]).empty()) {
        ++first;
    }
    if (first < end && remove_ignorable_whitespace(lines[first]) == "%") {
        ++first;
        std::size_t closing = first;
        while (closing < end && remove_ignorable_whitespace(lines[closing]) != "%") {
            ++closing;
        }
        if (closing == end) {
            throw InputError("File with percent prefix is missing closing percent line");
        }
        end = closing;
    }

    for (std::size_t index = first; index < end; ++index) {
        line = lines[index];
        const std::string compact_line = remove_ignorable_whitespace(strip_comments(line));
        if (block_delete && !compact_line.empty() && compact_line.front() == '/') {
            continue;
        }

        const ParsedLine parsed_line = parse_line(line, state);
        apply_line(parsed_line, state);
        apply_parameter_writes(parsed_line, state);
        if (parsed_line.end_program) {
            reset_after_program_end(state);
            break;
        }
    }

    return state;
}

void load_parameter_file(const std::string& parameter_input_path, MachineState& state) {
    std::ifstream parameter_stream(parameter_input_path);
    if (!parameter_stream.is_open()) {
        throw InputError("Could not open parameter file: " + parameter_input_path);
    }

    std::string line;
    bool in_data_section = false;
    int previous_parameter_index = 0;
    std::vector<bool> loaded_parameters(kParameterCount, false);
    while (std::getline(parameter_stream, line)) {
        if (!in_data_section) {
            if (line.empty()) {
                in_data_section = true;
            }
            continue;
        }

        if (line.empty()) {
            continue;
        }

        std::istringstream line_stream(line);
        int parameter_index = 0;
        double value = 0.0;
        if (!(line_stream >> parameter_index >> value)) {
            throw InputError("Invalid parameter file entry");
        }
        if (parameter_index < kMinParameterIndex || parameter_index > kMaxParameterFileIndex) {
            throw InputError("Parameter file index must be from 1 to 5400");
        }
        if (parameter_index <= previous_parameter_index) {
            throw InputError("Parameter file indices must be in ascending order");
        }

        state.parameters[parameter_index] = value;
        state.reported_parameters[parameter_index] = true;
        loaded_parameters[parameter_index] = true;

        int system_number = 0;
        int axis_index = 0;
        bool secondary_home = false;
        if (
            decode_coordinate_system_axis_parameter(parameter_index, system_number, axis_index)
            || decode_home_axis_parameter(parameter_index, secondary_home, axis_index)
            || decode_g92_axis_parameter(parameter_index, axis_index)
        ) {
            state.parameter_length_units[parameter_index] = axis_uses_length_units(axis_index)
                ? std::optional<LengthUnit>(state.current_length_unit)
                : std::nullopt;
        }

        previous_parameter_index = parameter_index;
    }

    // RS274 3.2.1, Table 2 requires all entries for the six supported axes.
    // Validate the file itself, even if a default value exists in state.
    for (int parameter_index = kMinParameterIndex; parameter_index <= kMaxParameterFileIndex; ++parameter_index) {
        if (is_required_parameter(parameter_index) && !loaded_parameters[parameter_index]) {
            throw InputError("Parameter file missing required parameter " + std::to_string(parameter_index));
        }
    }
}

void load_tool_table(const std::string& tool_table_path, MachineState& state) {
    std::ifstream tool_table_stream(tool_table_path);
    if (!tool_table_stream.is_open()) {
        throw InputError("Could not open tool table file: " + tool_table_path);
    }

    std::string line;
    bool in_data_section = false;
    while (std::getline(tool_table_stream, line)) {
        if (!in_data_section) {
            if (line.empty()) {
                in_data_section = true;
            }
            continue;
        }

        if (line.empty()) {
            continue;
        }

        std::istringstream line_stream(line);
        int pocket = 0;
        int fms = 0;
        double tool_length_offset = 0.0;
        double diameter = 0.0;
        if (!(line_stream >> pocket >> fms >> tool_length_offset >> diameter)) {
            throw InputError("Invalid tool table entry");
        }
        if (pocket < 0) {
            throw InputError("Tool table pocket number must be non-negative");
        }

        state.tool_table[pocket] = ToolTableEntry{tool_length_offset, diameter};
    }
}

std::string remove_ignorable_whitespace(std::string_view line) {
    std::string compact;
    compact.reserve(line.size());

    for (const char raw_character : line) {
        if (raw_character == ' ' || raw_character == '\t') {
            continue;
        }
        compact.push_back(raw_character);
    }

    return compact;
}

double parse_numeric_literal(std::string_view text, std::size_t& position) {
    const std::size_t start = position;
    if (position < text.size() && (text[position] == '+' || text[position] == '-')) {
        ++position;
    }

    bool saw_digit = false;
    bool saw_decimal_point = false;
    while (position < text.size()) {
        const unsigned char character = static_cast<unsigned char>(text[position]);
        if (std::isdigit(character) != 0) {
            saw_digit = true;
            ++position;
            continue;
        }
        if (text[position] == '.' && !saw_decimal_point) {
            saw_decimal_point = true;
            ++position;
            continue;
        }
        break;
    }

    if (!saw_digit) {
        throw InputError("Invalid numeric value");
    }

    try {
        return std::stod(std::string(text.substr(start, position - start)));
    } catch (const std::invalid_argument&) {
        throw InputError("Invalid numeric value");
    } catch (const std::out_of_range&) {
        throw InputError("Numeric value out of range");
    }
}

bool is_close_to_integer(double value) {
    return std::abs(value - std::round(value)) <= kNearIntegerTolerance;
}

int round_if_close_to_integer(double value, std::string_view error_message) {
    if (!is_close_to_integer(value)) {
        throw InputError(std::string(error_message));
    }

    return static_cast<int>(std::llround(value));
}

int round_g_code_tenths_if_close(double value) {
    const double scaled_value = value * 10.0;
    if (!is_close_to_integer(scaled_value)) {
        throw InputError("Unsupported G code value");
    }

    return static_cast<int>(std::llround(scaled_value));
}

int require_parameter_index(double value) {
    const int parameter_index =
        round_if_close_to_integer(value, "Parameter index must be an integer from 1 to 5399");
    if (parameter_index < kMinParameterIndex || parameter_index > kMaxParameterIndex) {
        throw InputError("Parameter index must be an integer from 1 to 5399");
    }

    return parameter_index;
}

bool matches_case_insensitive_keyword(
    std::string_view text,
    std::size_t position,
    std::string_view keyword
) {
    if (position + keyword.size() > text.size()) {
        return false;
    }

    for (std::size_t index = 0; index < keyword.size(); ++index) {
        if (std::toupper(static_cast<unsigned char>(text[position + index]))
            != std::toupper(static_cast<unsigned char>(keyword[index])))
        {
            return false;
        }
    }

    return true;
}

bool consume_case_insensitive_keyword(
    std::string_view text,
    std::size_t& position,
    std::string_view keyword
) {
    if (!matches_case_insensitive_keyword(text, position, keyword)) {
        return false;
    }

    position += keyword.size();
    return true;
}

double degrees_to_radians(double degrees) {
    return degrees * 3.14159265358979323846 / 180.0;
}

double radians_to_degrees(double radians) {
    return radians * 180.0 / 3.14159265358979323846;
}

double convert_length_value(double value, LengthUnit from, LengthUnit to) {
    if (from == to) {
        return value;
    }
    if (from == LengthUnit::kInches && to == LengthUnit::kMillimeters) {
        return value * kMillimetersPerInch;
    }

    return value / kMillimetersPerInch;
}

bool axis_uses_length_units(int axis_index) {
    return axis_index >= 0 && axis_index <= 2;
}

void convert_position_in_place(Position& position, LengthUnit from, LengthUnit to) {
    position.x = convert_length_value(position.x, from, to);
    position.y = convert_length_value(position.y, from, to);
    position.z = convert_length_value(position.z, from, to);
}

LengthUnit length_unit_for_g_code(std::string_view active_gcode) {
    if (active_gcode == "G20") {
        return LengthUnit::kInches;
    }
    if (active_gcode == "G21") {
        return LengthUnit::kMillimeters;
    }

    throw std::runtime_error("Unsupported length unit selection");
}

void apply_length_unit_change(MachineState& state, LengthUnit new_unit) {
    if (state.current_length_unit == new_unit) {
        return;
    }

    convert_position_in_place(state.machine_position, state.current_length_unit, new_unit);
    convert_position_in_place(state.g92_axis_offsets, state.current_length_unit, new_unit);
    for (auto& [_, offset] : state.coordinate_system_offsets) {
        convert_position_in_place(offset, state.current_length_unit, new_unit);
    }

    state.current_length_unit = new_unit;
}

double require_finite_real_value(double value, std::string_view context) {
    if (!std::isfinite(value)) {
        throw InputError("Invalid real value in " + std::string(context));
    }

    return value;
}

double apply_binary_operation(double lhs, std::string_view op, double rhs) {
    if (op == "**") {
        return require_finite_real_value(std::pow(lhs, rhs), "expression");
    }
    if (op == "*") {
        return lhs * rhs;
    }
    if (op == "/") {
        if (rhs == 0.0) {
            throw InputError("Division by zero in expression");
        }
        return lhs / rhs;
    }
    if (op == "MOD") {
        if (rhs == 0.0) {
            throw InputError("Modulo by zero in expression");
        }
        return std::fmod(lhs, rhs);
    }
    if (op == "+") {
        return lhs + rhs;
    }
    if (op == "-") {
        return lhs - rhs;
    }
    if (op == "AND") {
        return (lhs != 0.0 && rhs != 0.0) ? 1.0 : 0.0;
    }
    if (op == "OR") {
        return (lhs != 0.0 || rhs != 0.0) ? 1.0 : 0.0;
    }
    if (op == "XOR") {
        return ((lhs != 0.0) != (rhs != 0.0)) ? 1.0 : 0.0;
    }

    throw std::runtime_error("Unsupported binary operation");
}

double parse_expression(std::string_view text, std::size_t& position, const MachineState& state) {
    if (position >= text.size() || text[position] != '[') {
        throw InputError("Expression must start with '['");
    }

    ++position;
    const double value = parse_expression_group3(text, position, state);
    if (position >= text.size() || text[position] != ']') {
        throw InputError("Expression requires closing ']'");
    }
    ++position;
    return value;
}

double parse_expression_group3(
    std::string_view text,
    std::size_t& position,
    const MachineState& state
) {
    double value = parse_expression_group2(text, position, state);
    while (position < text.size()) {
        std::string_view op;
        if (consume_case_insensitive_keyword(text, position, "AND")) {
            op = "AND";
        } else if (consume_case_insensitive_keyword(text, position, "XOR")) {
            op = "XOR";
        } else if (consume_case_insensitive_keyword(text, position, "OR")) {
            op = "OR";
        } else if (text[position] == '+') {
            ++position;
            op = "+";
        } else if (text[position] == '-') {
            ++position;
            op = "-";
        } else {
            break;
        }

        value = apply_binary_operation(value, op, parse_expression_group2(text, position, state));
    }

    return value;
}

double parse_expression_group2(
    std::string_view text,
    std::size_t& position,
    const MachineState& state
) {
    double value = parse_expression_group1(text, position, state);
    while (position < text.size()) {
        std::string_view op;
        if (consume_case_insensitive_keyword(text, position, "MOD")) {
            op = "MOD";
        } else if (text[position] == '*') {
            if (position + 1 < text.size() && text[position + 1] == '*') {
                break;
            }
            ++position;
            op = "*";
        } else if (text[position] == '/') {
            ++position;
            op = "/";
        } else {
            break;
        }

        value = apply_binary_operation(value, op, parse_expression_group1(text, position, state));
    }

    return value;
}

double parse_expression_group1(
    std::string_view text,
    std::size_t& position,
    const MachineState& state
) {
    double value = parse_atomic_real_value(text, position, state);
    while (position + 1 < text.size() && text[position] == '*' && text[position + 1] == '*') {
        position += 2;
        value = apply_binary_operation(value, "**", parse_atomic_real_value(text, position, state));
    }

    return value;
}

double parse_parameter_value(std::string_view text, std::size_t& position, const MachineState& state) {
    if (position >= text.size() || text[position] != '#') {
        throw InputError("Parameter value must start with '#'");
    }

    ++position;
    const int parameter_index = parse_parameter_index(text, position, state);
    return state.parameters.at(parameter_index);
}

double parse_unary_operation_value(
    std::string_view text,
    std::size_t& position,
    const MachineState& state
) {
    auto parse_single_expression_argument = [&](std::string_view name) {
        const double argument = parse_expression(text, position, state);
        if (name == "ABS") {
            return std::abs(argument);
        }
        if (name == "ACOS") {
            return require_finite_real_value(radians_to_degrees(std::acos(argument)), "unary operation");
        }
        if (name == "ASIN") {
            return require_finite_real_value(radians_to_degrees(std::asin(argument)), "unary operation");
        }
        if (name == "COS") {
            return std::cos(degrees_to_radians(argument));
        }
        if (name == "EXP") {
            return require_finite_real_value(std::exp(argument), "unary operation");
        }
        if (name == "FIX") {
            return std::floor(argument);
        }
        if (name == "FUP") {
            return std::ceil(argument);
        }
        if (name == "LN") {
            return require_finite_real_value(std::log(argument), "unary operation");
        }
        if (name == "ROUND") {
            return std::round(argument);
        }
        if (name == "SIN") {
            return std::sin(degrees_to_radians(argument));
        }
        if (name == "SQRT") {
            return require_finite_real_value(std::sqrt(argument), "unary operation");
        }
        if (name == "TAN") {
            return require_finite_real_value(std::tan(degrees_to_radians(argument)), "unary operation");
        }

        throw std::runtime_error("Unsupported unary operation");
    };

    if (consume_case_insensitive_keyword(text, position, "ATAN")) {
        const double numerator = parse_expression(text, position, state);
        if (position >= text.size() || text[position] != '/') {
            throw InputError("ATAN requires two expressions separated by '/'");
        }
        ++position;
        const double denominator = parse_expression(text, position, state);
        return radians_to_degrees(std::atan2(numerator, denominator));
    }

    for (const std::string_view name :
         {std::string_view("ABS"),
          std::string_view("ACOS"),
          std::string_view("ASIN"),
          std::string_view("COS"),
          std::string_view("EXP"),
          std::string_view("FIX"),
          std::string_view("FUP"),
          std::string_view("LN"),
          std::string_view("ROUND"),
          std::string_view("SIN"),
          std::string_view("SQRT"),
          std::string_view("TAN")})
    {
        if (consume_case_insensitive_keyword(text, position, name)) {
            return parse_single_expression_argument(name);
        }
    }

    throw InputError("Unsupported unary operation");
}

double parse_atomic_real_value(std::string_view text, std::size_t& position, const MachineState& state) {
    if (position >= text.size()) {
        throw InputError("Missing real value");
    }
    if (text[position] == '[') {
        return parse_expression(text, position, state);
    }
    if (text[position] == '#') {
        return parse_parameter_value(text, position, state);
    }
    if (std::isalpha(static_cast<unsigned char>(text[position])) != 0) {
        return parse_unary_operation_value(text, position, state);
    }

    return parse_numeric_literal(text, position);
}

int parse_parameter_index(std::string_view text, std::size_t& position, const MachineState& state) {
    if (position >= text.size()) {
        throw InputError("Missing parameter index");
    }
    return require_parameter_index(parse_real_value(text, position, state));
}

double parse_real_value(std::string_view text, std::size_t& position, const MachineState& state) {
    if (position >= text.size()) {
        throw InputError("Missing real value");
    }

    return parse_atomic_real_value(text, position, state);
}

int require_non_negative_integer(double value, std::string_view word) {
    const int integer_value = round_if_close_to_integer(
        value,
        "Expected non-negative integer value for word: " + std::string(word)
    );
    if (integer_value < 0) {
        throw InputError("Expected non-negative integer value for word: " + std::string(word));
    }

    return integer_value;
}

void validate_tool_slot_number(
    const MachineState& state,
    int slot_number,
    std::string_view letter,
    bool allow_zero
) {
    if (!state.carousel_slots.has_value()) {
        return;
    }
    if (slot_number == 0 && allow_zero) {
        return;
    }
    if (slot_number > *state.carousel_slots) {
        throw InputError(
            std::string(letter) + " number cannot be larger than the number of carousel slots"
        );
    }
}

void parse_parameter_setting(
    std::string_view text,
    std::size_t& position,
    const MachineState& state,
    ParsedLine& parsed_line
) {
    ++position;
    const int parameter_index = parse_parameter_index(text, position, state);
    if (position >= text.size() || text[position] != '=') {
        throw InputError("Parameter setting requires '='");
    }
    ++position;

    parsed_line.parameter_writes.push_back(
        ParameterWrite{parameter_index, parse_real_value(text, position, state)}
    );
}

void parse_line_number(std::string_view text, std::size_t& position) {
    const double value = parse_numeric_literal(text, position);
    if (std::floor(value) != value || value < 0.0 || value > 99999.0) {
        throw InputError("Line number must be an integer from 0 to 99999");
    }
}

void parse_word_segment(
    std::string_view text,
    std::size_t& position,
    const MachineState& state,
    ParsedLine& parsed_line
) {
    const char letter = static_cast<char>(std::toupper(static_cast<unsigned char>(text[position++])));
    switch (letter) {
        case 'A':
            assign_unique_word(
                parsed_line.a,
                parse_real_value(text, position, state),
                std::string_view("A")
            );
            return;
        case 'B':
            assign_unique_word(
                parsed_line.b,
                parse_real_value(text, position, state),
                std::string_view("B")
            );
            return;
        case 'C':
            assign_unique_word(
                parsed_line.c,
                parse_real_value(text, position, state),
                std::string_view("C")
            );
            return;
        case 'D':
        {
            const int d_number = require_non_negative_integer(
                parse_real_value(text, position, state),
                std::string_view("D")
            );
            validate_tool_slot_number(state, d_number, std::string_view("D"), true);
            assign_unique_word(
                parsed_line.d,
                d_number,
                std::string_view("D")
            );
            return;
        }
        case 'F':
            assign_unique_word(
                parsed_line.feed_rate,
                parse_real_value(text, position, state),
                std::string_view("F")
            );
            return;
        case 'G':
            apply_g_code_value(parse_real_value(text, position, state), parsed_line);
            return;
        case 'H':
        {
            const int h_number = require_non_negative_integer(
                parse_real_value(text, position, state),
                std::string_view("H")
            );
            validate_tool_slot_number(state, h_number, std::string_view("H"), true);
            assign_unique_word(
                parsed_line.h,
                h_number,
                std::string_view("H")
            );
            return;
        }
        case 'I':
            assign_unique_word(
                parsed_line.i,
                parse_real_value(text, position, state),
                std::string_view("I")
            );
            return;
        case 'J':
            assign_unique_word(
                parsed_line.j,
                parse_real_value(text, position, state),
                std::string_view("J")
            );
            return;
        case 'K':
            assign_unique_word(
                parsed_line.k,
                parse_real_value(text, position, state),
                std::string_view("K")
            );
            return;
        case 'L':
            assign_unique_word(
                parsed_line.l,
                parse_real_value(text, position, state),
                std::string_view("L")
            );
            return;
        case 'M':
            apply_m_code_value(parse_real_value(text, position, state), parsed_line);
            return;
        case 'N':
            parse_line_number(text, position);
            return;
        case 'P':
            assign_unique_word(
                parsed_line.p,
                parse_real_value(text, position, state),
                std::string_view("P")
            );
            return;
        case 'Q':
            assign_unique_word(
                parsed_line.q,
                parse_real_value(text, position, state),
                std::string_view("Q")
            );
            return;
        case 'R':
            assign_unique_word(
                parsed_line.r,
                parse_real_value(text, position, state),
                std::string_view("R")
            );
            return;
        case 'S':
            assign_unique_word(
                parsed_line.spindle_speed,
                parse_real_value(text, position, state),
                std::string_view("S")
            );
            return;
        case 'T':
        {
            const int t_number = require_non_negative_integer(
                parse_real_value(text, position, state),
                std::string_view("T")
            );
            validate_tool_slot_number(state, t_number, std::string_view("T"), true);
            assign_unique_word(
                parsed_line.t,
                t_number,
                std::string_view("T")
            );
            return;
        }
        case 'X':
            assign_unique_word(
                parsed_line.x,
                parse_real_value(text, position, state),
                std::string_view("X")
            );
            return;
        case 'Y':
            assign_unique_word(
                parsed_line.y,
                parse_real_value(text, position, state),
                std::string_view("Y")
            );
            return;
        case 'Z':
            assign_unique_word(
                parsed_line.z,
                parse_real_value(text, position, state),
                std::string_view("Z")
            );
            return;
        default:
            throw InputError("Unsupported word");
    }
}

void parse_segment(std::string_view text, std::size_t& position, const MachineState& state, ParsedLine& parsed_line) {
    if (text[position] == '#') {
        parse_parameter_setting(text, position, state, parsed_line);
        return;
    }

    const unsigned char character = static_cast<unsigned char>(text[position]);
    if (std::isalpha(character) != 0) {
        parse_word_segment(text, position, state, parsed_line);
        return;
    }

    throw InputError("Unexpected character in line");
}

ParsedLine parse_line(std::string_view raw_line, const MachineState& state) {
    ParsedLine parsed_line;
    const std::string compact_line = remove_ignorable_whitespace(strip_comments(raw_line));
    std::size_t position = 0;
    if (position < compact_line.size() && compact_line[position] == '/') {
        ++position;
    }

    while (position < compact_line.size()) {
        parse_segment(compact_line, position, state, parsed_line);
    }

    const auto current_motion = state.active_modal_g_codes.find("1");
    const std::string_view effective_motion = parsed_line.active_modal_g_codes.contains("1")
        ? std::string_view(parsed_line.active_modal_g_codes.at("1"))
        : current_motion != state.active_modal_g_codes.end()
            ? std::string_view(current_motion->second)
            : std::string_view();
    const bool canned_cycle_context = is_any_canned_cycle_motion(effective_motion);

    if (parsed_line.l.has_value() && !parsed_line.has_g10 && !canned_cycle_context) {
        throw InputError("L word requires G10 or a canned cycle");
    }
    if (
        parsed_line.p.has_value() && !parsed_line.has_g10 && !parsed_line.has_g4
        && effective_motion != "G82" && effective_motion != "G86" && effective_motion != "G88"
        && effective_motion != "G89"
    ) {
        throw InputError("P word requires G4, G10, or a supported P-using canned cycle");
    }
    if (parsed_line.q.has_value() && effective_motion != "G83") {
        throw InputError("Q word requires G83");
    }
    if (parsed_line.has_g4) {
        if (parsed_line.l.has_value() || parsed_line.q.has_value()) {
            throw InputError("G4 does not use L or Q words");
        }
        if (!parsed_line.p.has_value()) {
            throw InputError("G4 requires a P word");
        }
        if (*parsed_line.p < 0.0) {
            throw InputError("G4 requires a non-negative P word");
        }
    }
    if (parsed_line.has_g10) {
        if (parsed_line.q.has_value()) {
            throw InputError("G10 does not use a Q word");
        }
        parsed_line.coordinate_system_offset_target = parse_g10_coordinate_system_number(parsed_line);
    }
    if (parsed_line.g92_command.has_value() && *parsed_line.g92_command == "G92"
        && !has_linear_axis_word(parsed_line))
    {
        throw InputError("G92 requires at least one axis word");
    }
    if (parsed_line.d.has_value()) {
        const auto cutter_compensation = parsed_line.active_modal_g_codes.find("7");
        if (cutter_compensation == parsed_line.active_modal_g_codes.end()
            || (cutter_compensation->second != "G41" && cutter_compensation->second != "G42"))
        {
            throw InputError("D word requires G41 or G42");
        }
    }

    return parsed_line;
}

template <typename T>
void assign_unique_word(std::optional<T>& destination, T value, std::string_view word) {
    if (destination.has_value()) {
        throw InputError("Multiple words with the same letter in the same block: " + std::string(word));
    }

    destination = value;
}

void apply_line(const ParsedLine& parsed_line, MachineState& state) {
    const auto prior_motion = state.active_modal_g_codes.find("1");
    const std::string prior_motion_gcode =
        prior_motion != state.active_modal_g_codes.end() ? prior_motion->second : std::string();

    if (parsed_line.active_modal_g_codes.contains("6") && cutter_radius_compensation_is_active(state)) {
        throw InputError("Cannot change units with cutter radius compensation active");
    }
    if (
        parsed_line.active_modal_g_codes.contains("2") && cutter_radius_compensation_is_active(state)
        && parsed_line.active_modal_g_codes.at("2") != "G17"
    ) {
        throw InputError("Cannot change planes away from XY with cutter radius compensation active");
    }
    if (parsed_line.active_modal_g_codes.contains("12") && cutter_radius_compensation_is_active(state)) {
        throw InputError("Cannot change coordinate systems with cutter radius compensation active");
    }
    if (parsed_line.home_command.has_value() && cutter_radius_compensation_is_active(state)) {
        throw InputError("Cannot use G28 or G30 with cutter radius compensation active");
    }
    if (parsed_line.g92_command.has_value() && cutter_radius_compensation_is_active(state)) {
        throw InputError("Cannot change axis offsets with cutter radius compensation active");
    }

    for (const auto& [group_number, active_gcode] : parsed_line.active_modal_g_codes) {
        state.active_modal_g_codes[group_number] = active_gcode;
        if (group_number == "3") {
            state.coordinate_mode =
                active_gcode == "G90" ? CoordinateMode::kAbsolute : CoordinateMode::kIncremental;
        } else if (group_number == "2") {
            state.selected_plane = plane_for_g_code(active_gcode);
        } else if (group_number == "6") {
            apply_length_unit_change(state, length_unit_for_g_code(active_gcode));
        } else if (group_number == "12") {
            set_selected_coordinate_system(
                state,
                std::stoi(coordinate_system_number_for_g_code(active_gcode))
            );
        }
    }
    for (const auto& [group_number, active_mcode] : parsed_line.active_modal_m_codes) {
        state.active_modal_m_codes[group_number] = active_mcode;
    }

    const auto current_motion = state.active_modal_g_codes.find("1");
    if (
        current_motion == state.active_modal_g_codes.end()
        || !is_supported_canned_cycle_motion(current_motion->second)
        || current_motion->second != prior_motion_gcode
    ) {
        state.canned_cycle_sticky_state = {};
    }

    if (parsed_line.feed_rate.has_value()) {
        state.feed_rate = *parsed_line.feed_rate;
    }
    if (parsed_line.spindle_speed.has_value() && *parsed_line.spindle_speed < 0.0) {
        throw InputError("S word must be non-negative");
    }
    if (parsed_line.spindle_speed.has_value()) {
        state.spindle_speed = *parsed_line.spindle_speed;
    }
    if (parsed_line.spindle_direction.has_value()) {
        state.spindle_direction = *parsed_line.spindle_direction;
    }
    if (parsed_line.t.has_value()) {
        state.selected_tool = *parsed_line.t;
    }
    if (parsed_line.active_modal_m_codes.contains("6")
        && parsed_line.active_modal_m_codes.at("6") == "M6")
    {
        state.spindle_direction = SpindleDirection::kOff;
        if (state.selected_tool.has_value() && *state.selected_tool != 0) {
            state.tool_in_spindle = state.selected_tool;
        } else {
            state.tool_in_spindle = std::nullopt;
        }
    }

    if (parsed_line.active_modal_g_codes.contains("7")) {
        const std::string_view active_crc = parsed_line.active_modal_g_codes.at("7");
        if (active_crc == "G40") {
            deactivate_cutter_radius_compensation(state);
        } else {
            activate_cutter_radius_compensation(
                state,
                cutter_comp_side_for_g_code(active_crc),
                parsed_line.d
            );
        }
    }
    if (parsed_line.active_modal_g_codes.contains("8")) {
        const std::string_view active_tlo = parsed_line.active_modal_g_codes.at("8");
        if (active_tlo == "G49") {
            apply_tool_length_offset_change(state, std::nullopt);
        } else {
            if (!parsed_line.h.has_value()) {
                throw InputError("G43 requires an H word");
            }
            apply_tool_length_offset_change(state, parsed_line.h);
        }
    }

    if (parsed_line.coordinate_system_offset_target.has_value()) {
        const int system_number = std::stoi(*parsed_line.coordinate_system_offset_target);
        for (int axis_index = 0; axis_index < 6; ++axis_index) {
            const std::optional<double> axis_word = parsed_line_axis_word(parsed_line, axis_index);
            if (axis_word.has_value()) {
                set_coordinate_system_axis(state, system_number, axis_index, *axis_word);
            }
        }
    } else if (parsed_line.g92_command.has_value()) {
        const std::string& g92_command = *parsed_line.g92_command;
        if (g92_command == "G92") {
            const Position& coordinate_system_offset =
                state.coordinate_system_offsets.at(state.selected_coordinate_system);
            for (int axis_index = 0; axis_index < 6; ++axis_index) {
                const std::optional<double> axis_word = parsed_line_axis_word(parsed_line, axis_index);
                if (!axis_word.has_value()) {
                    continue;
                }

                set_g92_axis_offset(
                    state,
                    axis_index,
                    position_axis_value(state.machine_position, axis_index)
                        - position_axis_value(coordinate_system_offset, axis_index) - *axis_word
                );
            }
        } else if (g92_command == "G92.1") {
            reset_g92_axis_offsets(state, true);
        } else if (g92_command == "G92.2") {
            reset_g92_axis_offsets(state, false);
        } else if (g92_command == "G92.3") {
            restore_g92_axis_offsets_from_parameters(state);
        } else {
            throw std::runtime_error("Unsupported G92 command");
        }
    } else if (parsed_line.home_command.has_value()) {
        apply_home_return(state, parsed_line, *parsed_line.home_command == "G30");
    } else {
        validate_linear_motion_command(parsed_line, state);
        validate_canned_cycle_command(parsed_line, state, prior_motion_gcode);
        validate_arc_command(parsed_line, state);
        const bool explicit_motion = parsed_line.active_modal_g_codes.contains("1");
        const bool implicit_motion = !explicit_motion && line_has_motion_axis_word(parsed_line);
        const std::string_view effective_motion = explicit_motion
            ? std::string_view(parsed_line.active_modal_g_codes.at("1"))
            : current_motion != state.active_modal_g_codes.end()
                ? std::string_view(current_motion->second)
                : std::string_view();
        const bool same_canned_cycle_already_active = !prior_motion_gcode.empty()
            && prior_motion_gcode == effective_motion;
        const bool canned_cycle_line = explicit_motion ? is_any_canned_cycle_motion(effective_motion)
            : current_motion != state.active_modal_g_codes.end() && is_any_canned_cycle_motion(effective_motion)
                && line_mentions_canned_cycle_words(parsed_line);

        if ((explicit_motion || implicit_motion) && is_probe_motion(effective_motion)) {
            apply_probe_motion(state, parsed_line);
        } else if (canned_cycle_line && is_supported_canned_cycle_motion(effective_motion)) {
            apply_canned_cycle_motion(
                state,
                parsed_line,
                effective_motion,
                same_canned_cycle_already_active
            );
        } else if (parsed_line.use_machine_coordinates) {
            for (int axis_index = 0; axis_index < 6; ++axis_index) {
                apply_coordinate_system_axis_value(
                    parsed_line_axis_word(parsed_line, axis_index),
                    position_axis_ref(state.machine_position, axis_index)
                );
            }
        } else if (cutter_radius_compensation_is_active(state) && has_xy_axis_word(parsed_line)) {
            if (current_motion != state.active_modal_g_codes.end()
                && is_arc_motion(current_motion->second))
            {
                apply_cutter_compensated_arc_xy_motion(state, parsed_line);
            } else {
                apply_cutter_compensated_linear_xy_motion(state, parsed_line);
            }
            apply_program_axis_value(
                parsed_line.z,
                state.machine_position.z,
                state.coordinate_mode,
                active_program_origin_offset_for_axis(state, 2)
            );
            for (int axis_index = 3; axis_index < 6; ++axis_index) {
                apply_program_axis_value(
                    parsed_line_axis_word(parsed_line, axis_index),
                    position_axis_ref(state.machine_position, axis_index),
                    state.coordinate_mode,
                    active_program_origin_offset_for_axis(state, axis_index)
                );
            }
        } else {
            for (int axis_index = 0; axis_index < 6; ++axis_index) {
                apply_program_axis_value(
                    parsed_line_axis_word(parsed_line, axis_index),
                    position_axis_ref(state.machine_position, axis_index),
                    state.coordinate_mode,
                    active_program_origin_offset_for_axis(state, axis_index)
                );
            }
        }
    }
}

void apply_program_axis_value(
    std::optional<double> value,
    double& machine_axis,
    CoordinateMode coordinate_mode,
    double coordinate_system_offset
) {
    if (!value.has_value()) {
        return;
    }

    if (coordinate_mode == CoordinateMode::kAbsolute) {
        machine_axis = coordinate_system_offset + *value;
        return;
    }

    machine_axis += *value;
}

bool is_arc_motion(std::string_view active_gcode) {
    return active_gcode == "G2" || active_gcode == "G3";
}

bool is_linear_motion(std::string_view active_gcode) {
    return active_gcode == "G0" || active_gcode == "G1";
}

bool is_any_canned_cycle_motion(std::string_view active_gcode) {
    return active_gcode == "G81" || active_gcode == "G82" || active_gcode == "G83"
        || active_gcode == "G84" || active_gcode == "G85" || active_gcode == "G86"
        || active_gcode == "G87" || active_gcode == "G88" || active_gcode == "G89";
}

bool is_supported_canned_cycle_motion(std::string_view active_gcode) {
    return active_gcode == "G81" || active_gcode == "G82" || active_gcode == "G83"
        || active_gcode == "G84" || active_gcode == "G85" || active_gcode == "G86"
        || active_gcode == "G87" || active_gcode == "G88" || active_gcode == "G89";
}

bool is_probe_motion(std::string_view active_gcode) {
    return active_gcode == "G38.2";
}

bool is_feed_rate_motion(std::string_view active_gcode) {
    return active_gcode == "G1" || active_gcode == "G2" || active_gcode == "G3";
}

Plane plane_for_g_code(std::string_view active_gcode) {
    if (active_gcode == "G17") {
        return Plane::kXY;
    }
    if (active_gcode == "G18") {
        return Plane::kXZ;
    }
    if (active_gcode == "G19") {
        return Plane::kYZ;
    }

    throw std::runtime_error("Unsupported plane selection: " + std::string(active_gcode));
}

double resolved_program_axis_endpoint(
    std::optional<double> value,
    double current_machine_axis,
    CoordinateMode coordinate_mode,
    double coordinate_system_offset
) {
    if (!value.has_value()) {
        return current_machine_axis;
    }
    if (coordinate_mode == CoordinateMode::kAbsolute) {
        return coordinate_system_offset + *value;
    }

    return current_machine_axis + *value;
}

bool has_linear_axis_word(const ParsedLine& parsed_line) {
    return parsed_line.x.has_value() || parsed_line.y.has_value() || parsed_line.z.has_value()
        || parsed_line.a.has_value() || parsed_line.b.has_value() || parsed_line.c.has_value();
}

bool has_xyz_axis_word(const ParsedLine& parsed_line) {
    return parsed_line.x.has_value() || parsed_line.y.has_value() || parsed_line.z.has_value();
}

bool has_xy_axis_word(const ParsedLine& parsed_line) {
    return parsed_line.x.has_value() || parsed_line.y.has_value();
}

bool line_has_motion_axis_word(const ParsedLine& parsed_line) {
    return has_linear_axis_word(parsed_line);
}

bool line_mentions_canned_cycle_words(const ParsedLine& parsed_line) {
    return parsed_line.x.has_value() || parsed_line.y.has_value() || parsed_line.z.has_value()
        || parsed_line.a.has_value() || parsed_line.b.has_value() || parsed_line.c.has_value()
        || parsed_line.l.has_value() || parsed_line.p.has_value() || parsed_line.q.has_value()
        || parsed_line.r.has_value() || parsed_line.i.has_value() || parsed_line.j.has_value()
        || parsed_line.k.has_value();
}

bool rotary_axis_words_are_stationary(const ParsedLine& parsed_line, const MachineState& state) {
    for (int axis_index = 3; axis_index < 6; ++axis_index) {
        const std::optional<double> axis_word = parsed_line_axis_word(parsed_line, axis_index);
        if (!axis_word.has_value()) {
            continue;
        }

        const double programmed_axis = resolved_program_axis_endpoint(
            axis_word,
            position_axis_value(state.machine_position, axis_index),
            state.coordinate_mode,
            active_program_origin_offset_for_axis(state, axis_index)
        );
        if (programmed_axis != position_axis_value(state.machine_position, axis_index)) {
            return false;
        }
    }

    return true;
}

void validate_linear_motion_command(const ParsedLine& parsed_line, const MachineState& state) {
    const auto current_motion = state.active_modal_g_codes.find("1");
    const bool explicit_motion = parsed_line.active_modal_g_codes.contains("1");
    const bool implicit_motion = !explicit_motion && line_has_motion_axis_word(parsed_line);

    if (parsed_line.use_machine_coordinates) {
        if (!explicit_motion && current_motion == state.active_modal_g_codes.end()) {
            throw InputError("G53 requires G0 or G1 to be active");
        }

        const std::string_view effective_motion = explicit_motion
            ? std::string_view(parsed_line.active_modal_g_codes.at("1"))
            : std::string_view(current_motion->second);
        if (!is_linear_motion(effective_motion)) {
            throw InputError("G53 requires G0 or G1 to be active");
        }
        if (!has_linear_axis_word(parsed_line)) {
            throw InputError("G53 requires at least one axis word");
        }
        if (cutter_radius_compensation_is_active(state)) {
            throw InputError("G53 cannot be used while cutter radius compensation is active");
        }
    }

    if (current_motion == state.active_modal_g_codes.end()) {
        return;
    }

    const std::string_view effective_motion = explicit_motion
        ? std::string_view(parsed_line.active_modal_g_codes.at("1"))
        : std::string_view(current_motion->second);

    if ((explicit_motion || implicit_motion) && effective_motion == "G38.2"
        && cutter_radius_compensation_is_active(state))
    {
        throw InputError("Cannot probe with cutter radius compensation active");
    }

    if ((explicit_motion || implicit_motion) && is_probe_motion(effective_motion)) {
        if (!has_xyz_axis_word(parsed_line)) {
            throw InputError("G38.2 requires at least one X, Y, or Z word");
        }
        if (!rotary_axis_words_are_stationary(parsed_line, state)) {
            throw InputError("G38.2 cannot command A, B, or C axis motion");
        }

        const Position programmed_point{
            resolved_program_axis_endpoint(
                parsed_line.x,
                state.machine_position.x,
                state.coordinate_mode,
                active_program_origin_offset_for_axis(state, 0)
            ),
            resolved_program_axis_endpoint(
                parsed_line.y,
                state.machine_position.y,
                state.coordinate_mode,
                active_program_origin_offset_for_axis(state, 1)
            ),
            resolved_program_axis_endpoint(
                parsed_line.z,
                state.machine_position.z,
                state.coordinate_mode,
                active_program_origin_offset_for_axis(state, 2)
            ),
            position_axis_value(state.machine_position, 3),
            position_axis_value(state.machine_position, 4),
            position_axis_value(state.machine_position, 5),
        };
        const double min_distance = state.current_length_unit == LengthUnit::kMillimeters ? 0.254 : 0.01;
        const double x_delta = programmed_point.x - state.machine_position.x;
        const double y_delta = programmed_point.y - state.machine_position.y;
        const double z_delta = programmed_point.z - state.machine_position.z;
        const double distance = std::sqrt((x_delta * x_delta) + (y_delta * y_delta) + (z_delta * z_delta));
        if (distance < min_distance) {
            throw InputError("G38.2 requires the programmed point to be sufficiently far away");
        }
    }

    if (explicit_motion && is_linear_motion(effective_motion) && !has_linear_axis_word(parsed_line)) {
        throw InputError("G0/G1 requires at least one axis word");
    }

    const auto feed_rate_mode = state.active_modal_g_codes.find("5");
    const bool inverse_time_feed_rate = feed_rate_mode != state.active_modal_g_codes.end()
        && feed_rate_mode->second == "G93";
    if (!inverse_time_feed_rate) {
        return;
    }

    if ((explicit_motion || implicit_motion)
        && (is_feed_rate_motion(effective_motion) || is_probe_motion(effective_motion))
        && !parsed_line.feed_rate.has_value())
    {
        throw InputError("Inverse time feed rate motion requires an F word");
    }
}

void validate_canned_cycle_command(
    const ParsedLine& parsed_line,
    const MachineState& state,
    std::string_view prior_motion_gcode
) {
    const auto current_motion = state.active_modal_g_codes.find("1");
    const bool explicit_motion = parsed_line.active_modal_g_codes.contains("1");
    const std::string_view effective_motion = explicit_motion
        ? std::string_view(parsed_line.active_modal_g_codes.at("1"))
        : current_motion != state.active_modal_g_codes.end()
            ? std::string_view(current_motion->second)
            : std::string_view();
    const bool cycle_line = explicit_motion ? is_any_canned_cycle_motion(effective_motion)
        : current_motion != state.active_modal_g_codes.end() && is_any_canned_cycle_motion(effective_motion)
            && line_mentions_canned_cycle_words(parsed_line);

    if (
        effective_motion == "G80" && has_linear_axis_word(parsed_line)
        && !parsed_line.has_g10 && !parsed_line.g92_command.has_value()
        && !parsed_line.home_command.has_value() && !parsed_line.use_machine_coordinates
    ) {
        throw InputError("Axis words are not allowed when G80 is active");
    }

    if (!cycle_line) {
        return;
    }
    if (!is_supported_canned_cycle_motion(effective_motion)) {
        throw InputError("Only the currently covered canned cycles are supported");
    }
    if (cutter_radius_compensation_is_active(state)) {
        throw InputError("Cannot use canned cycles with cutter radius compensation active");
    }

    const auto feed_rate_mode = state.active_modal_g_codes.find("5");
    if (feed_rate_mode != state.active_modal_g_codes.end() && feed_rate_mode->second == "G93") {
        throw InputError("Cannot use canned cycles in inverse time feed rate mode");
    }

    if (!has_xyz_axis_word(parsed_line)) {
        throw InputError("X, Y, and Z words may not all be omitted during a canned cycle");
    }
    if (!rotary_axis_words_are_stationary(parsed_line, state)) {
        throw InputError("Canned cycles cannot command A, B, or C axis motion");
    }

    if (parsed_line.l.has_value()) {
        const int repeat_count = round_if_close_to_integer(
            *parsed_line.l,
            "Canned cycle L word must be a positive integer"
        );
        if (repeat_count <= 0) {
            throw InputError("Canned cycle L word must be a positive integer");
        }
    }

    if (
        effective_motion == "G82" || effective_motion == "G86"
        || effective_motion == "G88" || effective_motion == "G89"
    ) {
        if (!parsed_line.p.has_value()) {
            throw InputError(std::string(effective_motion) + " requires a P word");
        }
        if (*parsed_line.p < 0.0) {
            throw InputError(std::string(effective_motion) + " requires a non-negative P word");
        }
    }
    if (effective_motion == "G83") {
        if (!parsed_line.q.has_value() || *parsed_line.q <= 0.0) {
            throw InputError("G83 requires a positive Q word");
        }
    }
    if (effective_motion == "G84" && state.spindle_direction != SpindleDirection::kClockwise) {
        throw InputError("G84 requires the spindle to be turning clockwise");
    }
    if (effective_motion == "G86" && state.spindle_direction == SpindleDirection::kOff) {
        throw InputError("G86 requires the spindle to be turning");
    }
    // Clarifications.md defines omitted G87 I/J/K words as zero. They
    // affect intermediate back-boring motion, not this snapshot's endpoint.

    char depth_axis_letter = 'Z';
    switch (state.selected_plane) {
        case Plane::kXY:
            depth_axis_letter = 'Z';
            break;
        case Plane::kXZ:
            depth_axis_letter = 'Y';
            break;
        case Plane::kYZ:
            depth_axis_letter = 'X';
            break;
    }

    const bool same_cycle_already_active = prior_motion_gcode == effective_motion;
    const bool has_depth_word = depth_axis_letter == 'X'
        ? parsed_line.x.has_value()
        : depth_axis_letter == 'Y' ? parsed_line.y.has_value() : parsed_line.z.has_value();
    if (!has_depth_word) {
        if (!same_cycle_already_active || !state.canned_cycle_sticky_state.depth_word.has_value()
            || state.canned_cycle_sticky_state.depth_axis_letter != depth_axis_letter)
        {
            throw InputError("The canned-cycle depth word must be programmed the first time");
        }
    }
    if (!parsed_line.r.has_value() && !state.canned_cycle_sticky_state.retract_word.has_value()) {
        throw InputError("The canned-cycle R word must be programmed the first time");
    }
}

void validate_arc_command(const ParsedLine& parsed_line, const MachineState& state) {
    const auto current_motion = state.active_modal_g_codes.find("1");
    const bool explicit_arc = parsed_line.active_modal_g_codes.contains("1")
        && is_arc_motion(parsed_line.active_modal_g_codes.at("1"));
    const bool line_mentions_arc_data = explicit_arc || parsed_line.r.has_value() || parsed_line.i.has_value()
        || parsed_line.j.has_value() || parsed_line.k.has_value() || parsed_line.x.has_value()
        || parsed_line.y.has_value() || parsed_line.z.has_value();
    if (current_motion == state.active_modal_g_codes.end() || !is_arc_motion(current_motion->second)
        || !line_mentions_arc_data)
    {
        return;
    }

    bool has_selected_plane_axis = false;
    bool has_center_offset = false;
    double current_first_axis = 0.0;
    double current_second_axis = 0.0;
    double end_first_axis = 0.0;
    double end_second_axis = 0.0;

    switch (state.selected_plane) {
        case Plane::kXY:
            has_selected_plane_axis = parsed_line.x.has_value() || parsed_line.y.has_value();
            has_center_offset = parsed_line.i.has_value() || parsed_line.j.has_value();
            current_first_axis = state.machine_position.x;
            current_second_axis = state.machine_position.y;
            end_first_axis = resolved_program_axis_endpoint(
                parsed_line.x,
                state.machine_position.x,
                state.coordinate_mode,
                active_program_origin_offset_for_axis(state, 0)
            );
            end_second_axis = resolved_program_axis_endpoint(
                parsed_line.y,
                state.machine_position.y,
                state.coordinate_mode,
                active_program_origin_offset_for_axis(state, 1)
            );
            break;
        case Plane::kXZ:
            has_selected_plane_axis = parsed_line.x.has_value() || parsed_line.z.has_value();
            has_center_offset = parsed_line.i.has_value() || parsed_line.k.has_value();
            current_first_axis = state.machine_position.x;
            current_second_axis = state.machine_position.z;
            end_first_axis = resolved_program_axis_endpoint(
                parsed_line.x,
                state.machine_position.x,
                state.coordinate_mode,
                active_program_origin_offset_for_axis(state, 0)
            );
            end_second_axis = resolved_program_axis_endpoint(
                parsed_line.z,
                state.machine_position.z,
                state.coordinate_mode,
                active_program_origin_offset_for_axis(state, 2)
            );
            break;
        case Plane::kYZ:
            has_selected_plane_axis = parsed_line.y.has_value() || parsed_line.z.has_value();
            has_center_offset = parsed_line.j.has_value() || parsed_line.k.has_value();
            current_first_axis = state.machine_position.y;
            current_second_axis = state.machine_position.z;
            end_first_axis = resolved_program_axis_endpoint(
                parsed_line.y,
                state.machine_position.y,
                state.coordinate_mode,
                active_program_origin_offset_for_axis(state, 1)
            );
            end_second_axis = resolved_program_axis_endpoint(
                parsed_line.z,
                state.machine_position.z,
                state.coordinate_mode,
                active_program_origin_offset_for_axis(state, 2)
            );
            break;
    }

    if (parsed_line.r.has_value()) {
        if (!has_selected_plane_axis) {
            throw InputError("Arc radius format requires an endpoint in the selected plane");
        }
        if (end_first_axis == current_first_axis && end_second_axis == current_second_axis) {
            throw InputError("Arc radius format cannot reuse the current point as the endpoint");
        }
        return;
    }

    if (!has_selected_plane_axis) {
        throw InputError("Arc center format requires an endpoint in the selected plane");
    }
    if (!has_center_offset) {
        throw InputError("Arc center format requires a center offset in the selected plane");
    }
}

void apply_coordinate_system_axis_value(std::optional<double> value, double& axis) {
    if (!value.has_value()) {
        return;
    }

    axis = *value;
}

std::string active_g_code_for_coordinate_system_number(int system_number) {
    switch (system_number) {
        case 1:
            return "G54";
        case 2:
            return "G55";
        case 3:
            return "G56";
        case 4:
            return "G57";
        case 5:
            return "G58";
        case 6:
            return "G59";
        case 7:
            return "G59.1";
        case 8:
            return "G59.2";
        case 9:
            return "G59.3";
        default:
            throw InputError("Coordinate system number must be from 1 to 9");
    }
}

int parameter_index_for_coordinate_system_axis(int system_number, int axis_index) {
    return 5221 + ((system_number - 1) * 20) + axis_index;
}

bool decode_coordinate_system_axis_parameter(int parameter_index, int& system_number, int& axis_index) {
    if (parameter_index < 5221 || parameter_index > 5386) {
        return false;
    }

    const int relative_index = parameter_index - 5221;
    const int within_system_block = relative_index % 20;
    if (within_system_block < 0 || within_system_block > 5) {
        return false;
    }

    system_number = (relative_index / 20) + 1;
    axis_index = within_system_block;
    return system_number >= 1 && system_number <= 9;
}

int parameter_index_for_home_axis(bool secondary_home, int axis_index) {
    return (secondary_home ? 5181 : 5161) + axis_index;
}

bool decode_home_axis_parameter(int parameter_index, bool& secondary_home, int& axis_index) {
    if (parameter_index >= 5161 && parameter_index <= 5166) {
        secondary_home = false;
        axis_index = parameter_index - 5161;
        return true;
    }
    if (parameter_index >= 5181 && parameter_index <= 5186) {
        secondary_home = true;
        axis_index = parameter_index - 5181;
        return true;
    }

    return false;
}

bool decode_g92_axis_parameter(int parameter_index, int& axis_index) {
    if (parameter_index < kG92XAxisOffsetParameter || parameter_index > kG92CAxisOffsetParameter) {
        return false;
    }

    axis_index = parameter_index - kG92XAxisOffsetParameter;
    return axis_index >= 0 && axis_index <= 5;
}

void set_parameter_value(
    MachineState& state,
    int parameter_index,
    double value,
    std::optional<LengthUnit> length_unit
) {
    state.parameters[parameter_index] = value;
    state.reported_parameters[parameter_index] = true;
    state.parameter_length_units[parameter_index] = length_unit;
}

void set_selected_coordinate_system(MachineState& state, int system_number) {
    state.selected_coordinate_system = std::to_string(system_number);
    set_parameter_value(state, kSelectedCoordinateSystemParameter, static_cast<double>(system_number));
    state.active_modal_g_codes["12"] = active_g_code_for_coordinate_system_number(system_number);
}

void set_coordinate_system_axis(MachineState& state, int system_number, int axis_index, double value) {
    Position& coordinate_system_offset = state.coordinate_system_offsets.at(std::to_string(system_number));
    position_axis_ref(coordinate_system_offset, axis_index) = value;

    set_parameter_value(
        state,
        parameter_index_for_coordinate_system_axis(system_number, axis_index),
        value,
        axis_uses_length_units(axis_index) ? std::optional<LengthUnit>(state.current_length_unit) : std::nullopt
    );
}

void set_g92_axis_offset(MachineState& state, int axis_index, double value) {
    position_axis_ref(state.g92_axis_offsets, axis_index) = value;
    set_parameter_value(
        state,
        kG92XAxisOffsetParameter + axis_index,
        value,
        axis_uses_length_units(axis_index) ? std::optional<LengthUnit>(state.current_length_unit) : std::nullopt
    );
}

double parameter_length_value_in_current_units(const MachineState& state, int parameter_index) {
    const double raw_value = state.parameters.at(parameter_index);
    const std::optional<LengthUnit>& raw_unit = state.parameter_length_units.at(parameter_index);
    if (!raw_unit.has_value()) {
        return raw_value;
    }

    return convert_length_value(raw_value, *raw_unit, state.current_length_unit);
}

double active_tool_length_offset_in_current_units(const MachineState& state) {
    if (!state.active_tool_length_offset.has_value()) {
        return 0.0;
    }
    if (!state.active_tool_length_offset_unit.has_value()) {
        return *state.active_tool_length_offset;
    }

    return convert_length_value(
        *state.active_tool_length_offset,
        *state.active_tool_length_offset_unit,
        state.current_length_unit
    );
}

bool cutter_radius_compensation_is_active(const MachineState& state) {
    return state.cutter_comp_side != CutterCompSide::kOff;
}

CutterCompSide cutter_comp_side_for_g_code(std::string_view active_gcode) {
    if (active_gcode == "G41") {
        return CutterCompSide::kLeft;
    }
    if (active_gcode == "G42") {
        return CutterCompSide::kRight;
    }

    throw std::runtime_error("Unsupported cutter compensation code: " + std::string(active_gcode));
}

void activate_cutter_radius_compensation(
    MachineState& state,
    CutterCompSide side,
    std::optional<int> d_number
) {
    if (state.selected_plane != Plane::kXY) {
        throw InputError("Cutter radius compensation requires the XY plane");
    }
    if (cutter_radius_compensation_is_active(state)) {
        throw InputError("Cannot turn cutter radius compensation on when it is already on");
    }

    if (d_number.has_value()) {
        state.cutter_radius_compensation_number = *d_number;
    } else {
        state.cutter_radius_compensation_number = state.tool_in_spindle;
    }
    state.cutter_comp_side = side;
    state.pending_first_cutter_comp_move = true;
    state.cutter_comp_programmed_xy = std::nullopt;
    state.cutter_comp_last_linear_direction = std::nullopt;
}

void deactivate_cutter_radius_compensation(MachineState& state) {
    state.cutter_radius_compensation_number = std::nullopt;
    state.cutter_comp_side = CutterCompSide::kOff;
    state.pending_first_cutter_comp_move = false;
    state.cutter_comp_programmed_xy = std::nullopt;
    state.cutter_comp_last_linear_direction = std::nullopt;
}

double active_cutter_radius(const MachineState& state) {
    if (!state.cutter_radius_compensation_number.has_value()) {
        throw InputError(
            "First compensated move requires a D number or a tool in the spindle when compensation was turned on"
        );
    }

    const int d_number = *state.cutter_radius_compensation_number;
    if (d_number == 0) {
        return 0.0;
    }

    const auto tool_entry = state.tool_table.find(d_number);
    if (tool_entry == state.tool_table.end()) {
        throw InputError("G41/G42 requires a matching tool-table entry for the active D number");
    }
    if (tool_entry->second.diameter < 0.0) {
        throw InputError("Tool diameter must be non-negative");
    }

    return tool_entry->second.diameter / 2.0;
}

Point2D resolve_programmed_xy_endpoint(const ParsedLine& parsed_line, const MachineState& state) {
    const Point2D base = resolve_current_programmed_xy(state);
    Point2D endpoint = base;
    if (state.coordinate_mode == CoordinateMode::kAbsolute) {
        endpoint.x = parsed_line.x.has_value()
            ? active_program_origin_offset_for_axis(state, 0) + *parsed_line.x
            : base.x;
        endpoint.y = parsed_line.y.has_value()
            ? active_program_origin_offset_for_axis(state, 1) + *parsed_line.y
            : base.y;
        return endpoint;
    }

    if (parsed_line.x.has_value()) {
        endpoint.x += *parsed_line.x;
    }
    if (parsed_line.y.has_value()) {
        endpoint.y += *parsed_line.y;
    }
    return endpoint;
}

Point2D resolve_current_programmed_xy(const MachineState& state) {
    return state.cutter_comp_programmed_xy.value_or(
        Point2D{state.machine_position.x, state.machine_position.y}
    );
}

bool cutter_comp_arc_offsets_outward(std::string_view motion_gcode, CutterCompSide side) {
    if (motion_gcode == "G2") {
        return side == CutterCompSide::kLeft;
    }
    if (motion_gcode == "G3") {
        return side == CutterCompSide::kRight;
    }

    throw std::runtime_error("Unsupported compensated arc motion: " + std::string(motion_gcode));
}

Point2D resolve_center_format_arc_center(
    Point2D programmed_start,
    const ParsedLine& parsed_line
) {
    return Point2D{
        programmed_start.x + parsed_line.i.value_or(0.0),
        programmed_start.y + parsed_line.j.value_or(0.0),
    };
}

Point2D resolve_radius_format_arc_center(
    Point2D programmed_start,
    Point2D programmed_endpoint,
    double radius_word,
    std::string_view motion_gcode
) {
    const double radius = std::abs(radius_word);
    const double chord_x = programmed_endpoint.x - programmed_start.x;
    const double chord_y = programmed_endpoint.y - programmed_start.y;
    const double chord_length = std::hypot(chord_x, chord_y);
    if (chord_length <= kNearIntegerTolerance) {
        throw InputError("Arc radius format cannot reuse the current point as the endpoint");
    }
    if (radius + kNearIntegerTolerance < (chord_length / 2.0)) {
        throw InputError("Arc radius is too small for the programmed endpoint span");
    }

    const Point2D midpoint{
        (programmed_start.x + programmed_endpoint.x) / 2.0,
        (programmed_start.y + programmed_endpoint.y) / 2.0,
    };
    const double half_chord = chord_length / 2.0;
    const double height_squared = std::max(0.0, (radius * radius) - (half_chord * half_chord));
    const double height = std::sqrt(height_squared);
    const Point2D left_normal{
        -chord_y / chord_length,
        chord_x / chord_length,
    };
    const Point2D candidate_a{
        midpoint.x + (left_normal.x * height),
        midpoint.y + (left_normal.y * height),
    };
    const Point2D candidate_b{
        midpoint.x - (left_normal.x * height),
        midpoint.y - (left_normal.y * height),
    };

    const auto matches_requested_arc = [&](const Point2D& center) {
        const double start_x = programmed_start.x - center.x;
        const double start_y = programmed_start.y - center.y;
        const double end_x = programmed_endpoint.x - center.x;
        const double end_y = programmed_endpoint.y - center.y;
        const double cross = (start_x * end_y) - (start_y * end_x);
        const bool short_arc_is_ccw = cross > 0.0;
        const bool requested_is_ccw = motion_gcode == "G3";
        const bool requested_is_short_arc = radius_word >= 0.0;
        const bool candidate_is_ccw = requested_is_short_arc ? short_arc_is_ccw : !short_arc_is_ccw;
        return candidate_is_ccw == requested_is_ccw;
    };

    return matches_requested_arc(candidate_a) ? candidate_a : candidate_b;
}

Point2D resolve_first_cutter_comp_radius_format_arc_center(
    Point2D current_tool_center,
    Point2D programmed_endpoint,
    double programmed_arc_radius,
    double tool_center_arc_radius,
    double radius_word,
    std::string_view motion_gcode
) {
    const double connector_x = programmed_endpoint.x - current_tool_center.x;
    const double connector_y = programmed_endpoint.y - current_tool_center.y;
    const double connector_length = std::hypot(connector_x, connector_y);
    if (connector_length <= kNearIntegerTolerance) {
        throw InputError("First cutter compensation arc cannot be constructed");
    }
    if (tool_center_arc_radius + programmed_arc_radius + kNearIntegerTolerance < connector_length) {
        throw InputError("First cutter compensation arc cannot be constructed");
    }
    if (connector_length + std::min(tool_center_arc_radius, programmed_arc_radius)
        + kNearIntegerTolerance
        < std::max(tool_center_arc_radius, programmed_arc_radius))
    {
        throw InputError("First cutter compensation arc cannot be constructed");
    }

    const double a = (
        (tool_center_arc_radius * tool_center_arc_radius)
        - (programmed_arc_radius * programmed_arc_radius)
        + (connector_length * connector_length)
    ) / (2.0 * connector_length);
    const Point2D base_point{
        current_tool_center.x + ((connector_x * a) / connector_length),
        current_tool_center.y + ((connector_y * a) / connector_length),
    };
    const double height_squared = std::max(
        0.0,
        (tool_center_arc_radius * tool_center_arc_radius) - (a * a)
    );
    const double height = std::sqrt(height_squared);
    const Point2D left_normal{
        -connector_y / connector_length,
        connector_x / connector_length,
    };
    const Point2D candidate_a{
        base_point.x + (left_normal.x * height),
        base_point.y + (left_normal.y * height),
    };
    const Point2D candidate_b{
        base_point.x - (left_normal.x * height),
        base_point.y - (left_normal.y * height),
    };

    const auto matches_requested_arc = [&](const Point2D& center) {
        const Point2D generated_endpoint{
            center.x + (((programmed_endpoint.x - center.x) * tool_center_arc_radius) / programmed_arc_radius),
            center.y + (((programmed_endpoint.y - center.y) * tool_center_arc_radius) / programmed_arc_radius),
        };
        const double start_x = current_tool_center.x - center.x;
        const double start_y = current_tool_center.y - center.y;
        const double end_x = generated_endpoint.x - center.x;
        const double end_y = generated_endpoint.y - center.y;
        const double cross = (start_x * end_y) - (start_y * end_x);
        const bool short_arc_is_ccw = cross > 0.0;
        const bool requested_is_ccw = motion_gcode == "G3";
        const bool requested_is_short_arc = radius_word >= 0.0;
        const bool candidate_is_ccw = requested_is_short_arc ? short_arc_is_ccw : !short_arc_is_ccw;
        return candidate_is_ccw == requested_is_ccw;
    };

    return matches_requested_arc(candidate_a) ? candidate_a : candidate_b;
}

double compensated_arc_radius(
    double programmed_arc_radius,
    double tool_radius,
    bool offsets_outward
) {
    if (offsets_outward) {
        return programmed_arc_radius + tool_radius;
    }
    if (programmed_arc_radius <= tool_radius + kNearIntegerTolerance) {
        throw InputError("Tool radius not less than arc radius with comp");
    }
    return programmed_arc_radius - tool_radius;
}

Point2D compute_first_cutter_comp_linear_endpoint(
    Point2D current_tool_center,
    Point2D programmed_endpoint,
    double tool_radius,
    CutterCompSide side
) {
    if (tool_radius == 0.0) {
        return programmed_endpoint;
    }

    const double dx = current_tool_center.x - programmed_endpoint.x;
    const double dy = current_tool_center.y - programmed_endpoint.y;
    const double distance_squared = (dx * dx) + (dy * dy);
    const double radius_squared = tool_radius * tool_radius;
    if (distance_squared + kNearIntegerTolerance < radius_squared) {
        throw InputError("First cutter compensation move gouges the programmed endpoint");
    }

    const double tangent_length = distance_squared <= radius_squared
        ? 0.0
        : std::sqrt(distance_squared - radius_squared);
    const double radial_scale = radius_squared / distance_squared;
    const double tangent_scale = (tool_radius * tangent_length) / distance_squared;

    const Point2D candidate_a{
        programmed_endpoint.x + (radial_scale * dx) - (tangent_scale * dy),
        programmed_endpoint.y + (radial_scale * dy) + (tangent_scale * dx),
    };
    const Point2D candidate_b{
        programmed_endpoint.x + (radial_scale * dx) + (tangent_scale * dy),
        programmed_endpoint.y + (radial_scale * dy) - (tangent_scale * dx),
    };

    const auto contour_is_on_requested_side = [&](const Point2D& candidate) {
        const double motion_x = candidate.x - current_tool_center.x;
        const double motion_y = candidate.y - current_tool_center.y;
        const double contour_offset_x = programmed_endpoint.x - candidate.x;
        const double contour_offset_y = programmed_endpoint.y - candidate.y;
        const double cross =
            (motion_x * contour_offset_y) - (motion_y * contour_offset_x);
        if (side == CutterCompSide::kLeft) {
            return cross <= kNearIntegerTolerance;
        }
        return cross >= -kNearIntegerTolerance;
    };

    return contour_is_on_requested_side(candidate_a) ? candidate_a : candidate_b;
}

void apply_cutter_compensated_linear_xy_motion(MachineState& state, const ParsedLine& parsed_line) {
    const auto current_motion = state.active_modal_g_codes.find("1");
    if (current_motion == state.active_modal_g_codes.end() || !is_linear_motion(current_motion->second)) {
        throw InputError("Cutter radius compensation currently supports only straight G0/G1 XY motion");
    }

    const Point2D programmed_endpoint = resolve_programmed_xy_endpoint(parsed_line, state);
    if (state.pending_first_cutter_comp_move) {
        const Point2D compensated_endpoint = compute_first_cutter_comp_linear_endpoint(
            Point2D{state.machine_position.x, state.machine_position.y},
            programmed_endpoint,
            active_cutter_radius(state),
            state.cutter_comp_side
        );
        state.machine_position.x = compensated_endpoint.x;
        state.machine_position.y = compensated_endpoint.y;
        state.pending_first_cutter_comp_move = false;
        state.cutter_comp_programmed_xy = programmed_endpoint;
        state.cutter_comp_last_linear_direction = std::nullopt;
        return;
    }

    const Point2D current_programmed_xy = state.cutter_comp_programmed_xy.value_or(programmed_endpoint);
    const Point2D segment{
        programmed_endpoint.x - current_programmed_xy.x,
        programmed_endpoint.y - current_programmed_xy.y,
    };
    const double segment_length = std::hypot(segment.x, segment.y);
    if (segment_length <= kNearIntegerTolerance) {
        state.cutter_comp_programmed_xy = programmed_endpoint;
        return;
    }

    if (state.cutter_comp_last_linear_direction.has_value()) {
        const Point2D& previous_segment = *state.cutter_comp_last_linear_direction;
        const double turn =
            (previous_segment.x * segment.y) - (previous_segment.y * segment.x);
        const double side_sign = state.cutter_comp_side == CutterCompSide::kLeft ? 1.0 : -1.0;
        if ((turn * side_sign) > kNearIntegerTolerance) {
            throw InputError("Concave corner with cutter radius compensation");
        }
    }

    double normal_x = -segment.y / segment_length;
    double normal_y = segment.x / segment_length;
    if (state.cutter_comp_side == CutterCompSide::kRight) {
        normal_x = -normal_x;
        normal_y = -normal_y;
    }

    const double tool_radius = active_cutter_radius(state);
    state.machine_position.x = programmed_endpoint.x + (normal_x * tool_radius);
    state.machine_position.y = programmed_endpoint.y + (normal_y * tool_radius);
    state.cutter_comp_programmed_xy = programmed_endpoint;
    state.cutter_comp_last_linear_direction = segment;
}

void apply_cutter_compensated_arc_xy_motion(MachineState& state, const ParsedLine& parsed_line) {
    const auto current_motion = state.active_modal_g_codes.find("1");
    if (current_motion == state.active_modal_g_codes.end() || !is_arc_motion(current_motion->second)) {
        throw InputError("Cutter radius compensation currently supports only G2/G3 XY arcs");
    }

    // Under CRC, §3.5.3 defers to Appendix B: the input describes the
    // path arc the tool tip traces (the "generated" arc per §B.6),
    // which shares its center with the auxiliary arc. I/J = offsets
    // from the current tool-tip location (§3.5.3.2 + §B.1.1) to that
    // shared center; R = radius of the path arc; X/Y = programmed
    // contour endpoint (on the auxiliary arc). The same construction
    // applies to first and continuation arcs.
    const Point2D current_tool_tip{state.machine_position.x, state.machine_position.y};
    const Point2D programmed_endpoint = resolve_programmed_xy_endpoint(parsed_line, state);
    const double tool_radius = active_cutter_radius(state);
    const bool offsets_outward =
        cutter_comp_arc_offsets_outward(current_motion->second, state.cutter_comp_side);
    Point2D programmed_center{};
    double tool_center_arc_radius = 0.0;
    if (parsed_line.r.has_value()) {
        const double path_arc_radius = std::abs(*parsed_line.r);
        // Auxiliary arc radius = path arc radius -/+ tool radius, depending on side.
        const double auxiliary_arc_radius = offsets_outward
            ? path_arc_radius - tool_radius
            : path_arc_radius + tool_radius;
        if (auxiliary_arc_radius <= kNearIntegerTolerance) {
            throw InputError("Tool radius not less than arc radius with comp");
        }
        // For two distinct intersections (and a non-degenerate path arc),
        // |aux_r - path_r| < chord < aux_r + path_r. Border cases
        // collapse to a single point and produce a zero-length path arc;
        // reject those as the analogue of §3.5.3.1's "end point of the
        // arc is the same as the current point."
        const double chord = std::hypot(
            programmed_endpoint.x - current_tool_tip.x,
            programmed_endpoint.y - current_tool_tip.y
        );
        if (chord > auxiliary_arc_radius + path_arc_radius + kNearIntegerTolerance) {
            throw InputError("First cutter compensation arc cannot be constructed");
        }
        if (chord <= std::abs(auxiliary_arc_radius - path_arc_radius) + kNearIntegerTolerance) {
            throw InputError("Tool radius not less than arc radius with comp");
        }
        programmed_center = resolve_first_cutter_comp_radius_format_arc_center(
            current_tool_tip,
            programmed_endpoint,
            auxiliary_arc_radius,
            path_arc_radius,
            *parsed_line.r,
            current_motion->second
        );
        tool_center_arc_radius = path_arc_radius;
    } else {
        programmed_center = resolve_center_format_arc_center(current_tool_tip, parsed_line);
        const double auxiliary_arc_radius = std::hypot(
            programmed_endpoint.x - programmed_center.x,
            programmed_endpoint.y - programmed_center.y
        );
        if (auxiliary_arc_radius <= kNearIntegerTolerance) {
            throw InputError("Arc endpoint may not be at the arc center");
        }
        tool_center_arc_radius =
            compensated_arc_radius(auxiliary_arc_radius, tool_radius, offsets_outward);
        // Verify the input I/J is consistent with the resolved path
        // geometry: |tool-tip - center| (= hypot(I, J)) must equal the
        // derived path-arc radius (= aux_r +/- tool_r).
        const double current_center_distance = std::hypot(
            current_tool_tip.x - programmed_center.x,
            current_tool_tip.y - programmed_center.y
        );
        if (std::abs(current_center_distance - tool_center_arc_radius) > kNearIntegerTolerance) {
            throw InputError("Cutter compensation arc inconsistent: I/J implies a path radius that does not match the auxiliary arc radius +/- tool radius");
        }
    }
    if (state.pending_first_cutter_comp_move) {
        state.pending_first_cutter_comp_move = false;
    }

    const double endpoint_center_distance = std::hypot(
        programmed_endpoint.x - programmed_center.x,
        programmed_endpoint.y - programmed_center.y
    );
    if (endpoint_center_distance <= kNearIntegerTolerance) {
        throw InputError("Arc endpoint may not be at the arc center");
    }

    const double scale = tool_center_arc_radius / endpoint_center_distance;
    state.machine_position.x =
        programmed_center.x + ((programmed_endpoint.x - programmed_center.x) * scale);
    state.machine_position.y =
        programmed_center.y + ((programmed_endpoint.y - programmed_center.y) * scale);
    state.cutter_comp_programmed_xy = programmed_endpoint;
    state.cutter_comp_last_linear_direction = std::nullopt;
}

void initialize_state_from_parameters(MachineState& state) {
    for (int system_number = 1; system_number <= 9; ++system_number) {
        Position& coordinate_system_offset = state.coordinate_system_offsets.at(std::to_string(system_number));
        for (int axis_index = 0; axis_index < 6; ++axis_index) {
            position_axis_ref(coordinate_system_offset, axis_index) = parameter_length_value_in_current_units(
                state,
                parameter_index_for_coordinate_system_axis(system_number, axis_index)
            );
        }
    }

    for (int axis_index = 0; axis_index < 6; ++axis_index) {
        position_axis_ref(state.g92_axis_offsets, axis_index) = parameter_length_value_in_current_units(
            state,
            kG92XAxisOffsetParameter + axis_index
        );
    }

    const int selected_coordinate_system = round_if_close_to_integer(
        state.parameters[kSelectedCoordinateSystemParameter],
        "Parameter 5220 must be a whole number from 1 to 9"
    );
    if (selected_coordinate_system < 1 || selected_coordinate_system > 9) {
        throw InputError("Parameter 5220 must be a whole number from 1 to 9");
    }

    set_selected_coordinate_system(state, selected_coordinate_system);
}

void apply_tool_length_offset_change(MachineState& state, std::optional<int> new_index) {
    const double previous_offset = active_tool_length_offset_in_current_units(state);

    std::optional<double> new_offset_raw;
    std::optional<LengthUnit> new_offset_unit;
    if (new_index.has_value()) {
        if (*new_index == 0) {
            new_offset_raw = 0.0;
            new_offset_unit = state.current_length_unit;
        } else {
            const auto tool_entry = state.tool_table.find(*new_index);
            if (tool_entry == state.tool_table.end()) {
                throw InputError("G43 H number requires a matching tool-table entry");
            }
            if (tool_entry->second.tool_length_offset < 0.0) {
                throw InputError("Tool length offset must be non-negative");
            }

            new_offset_raw = tool_entry->second.tool_length_offset;
            new_offset_unit = state.current_length_unit;
        }
    }

    const double new_offset = new_offset_raw.value_or(0.0);
    state.machine_position.z += previous_offset - new_offset;
    state.tool_length_offset_index = new_index;
    state.active_tool_length_offset = new_offset_raw;
    state.active_tool_length_offset_unit = new_offset_unit;
}

void reset_g92_axis_offsets(MachineState& state, bool reset_parameters) {
    state.g92_axis_offsets = {};
    if (reset_parameters) {
        for (int axis_index = 0; axis_index < 6; ++axis_index) {
            set_parameter_value(
                state,
                kG92XAxisOffsetParameter + axis_index,
                0.0,
                axis_uses_length_units(axis_index) ? std::optional<LengthUnit>(state.current_length_unit)
                                                   : std::nullopt
            );
        }
    }
}

void restore_g92_axis_offsets_from_parameters(MachineState& state) {
    for (int axis_index = 0; axis_index < 6; ++axis_index) {
        position_axis_ref(state.g92_axis_offsets, axis_index) = parameter_length_value_in_current_units(
            state,
            kG92XAxisOffsetParameter + axis_index
        );
    }
}

double active_program_origin_offset_for_axis(const MachineState& state, int axis_index) {
    const Position& coordinate_system_offset =
        state.coordinate_system_offsets.at(state.selected_coordinate_system);
    return position_axis_value(coordinate_system_offset, axis_index)
        + position_axis_value(state.g92_axis_offsets, axis_index);
}

void apply_home_return(MachineState& state, const ParsedLine& parsed_line, bool secondary_home) {
    for (int axis_index = 0; axis_index < 6; ++axis_index) {
        apply_program_axis_value(
            parsed_line_axis_word(parsed_line, axis_index),
            position_axis_ref(state.machine_position, axis_index),
            state.coordinate_mode,
            active_program_origin_offset_for_axis(state, axis_index)
        );
    }

    for (int axis_index = 0; axis_index < 6; ++axis_index) {
        position_axis_ref(state.machine_position, axis_index) = parameter_length_value_in_current_units(
            state,
            parameter_index_for_home_axis(secondary_home, axis_index)
        );
    }
}

bool point_is_inside_probe_box(const Position& point, const ProbeBox& probe_box, LengthUnit current_unit) {
    const double x_min = convert_length_value(probe_box.x_min, probe_box.unit, current_unit);
    const double x_max = convert_length_value(probe_box.x_max, probe_box.unit, current_unit);
    const double y_min = convert_length_value(probe_box.y_min, probe_box.unit, current_unit);
    const double y_max = convert_length_value(probe_box.y_max, probe_box.unit, current_unit);
    const double z_min = convert_length_value(probe_box.z_min, probe_box.unit, current_unit);
    const double z_max = convert_length_value(probe_box.z_max, probe_box.unit, current_unit);

    return point.x >= x_min && point.x <= x_max && point.y >= y_min && point.y <= y_max
        && point.z >= z_min && point.z <= z_max;
}

std::optional<Position> find_probe_trip_point(
    const Position& start,
    const Position& programmed_point,
    const ProbeBox& probe_box,
    LengthUnit current_unit
) {
    const double x_min = convert_length_value(probe_box.x_min, probe_box.unit, current_unit);
    const double x_max = convert_length_value(probe_box.x_max, probe_box.unit, current_unit);
    const double y_min = convert_length_value(probe_box.y_min, probe_box.unit, current_unit);
    const double y_max = convert_length_value(probe_box.y_max, probe_box.unit, current_unit);
    const double z_min = convert_length_value(probe_box.z_min, probe_box.unit, current_unit);
    const double z_max = convert_length_value(probe_box.z_max, probe_box.unit, current_unit);

    double entry_t = 0.0;
    double exit_t = 1.0;
    const auto update_axis_range = [&](double start_axis, double end_axis, double box_min, double box_max) {
        const double delta = end_axis - start_axis;
        if (delta == 0.0) {
            return start_axis >= box_min && start_axis <= box_max;
        }

        double axis_entry_t = (box_min - start_axis) / delta;
        double axis_exit_t = (box_max - start_axis) / delta;
        if (axis_entry_t > axis_exit_t) {
            std::swap(axis_entry_t, axis_exit_t);
        }

        entry_t = std::max(entry_t, axis_entry_t);
        exit_t = std::min(exit_t, axis_exit_t);
        return entry_t <= exit_t;
    };

    if (!update_axis_range(start.x, programmed_point.x, x_min, x_max)
        || !update_axis_range(start.y, programmed_point.y, y_min, y_max)
        || !update_axis_range(start.z, programmed_point.z, z_min, z_max))
    {
        return std::nullopt;
    }

    if (entry_t < 0.0 || entry_t > 1.0) {
        return std::nullopt;
    }

    return Position{
        start.x + ((programmed_point.x - start.x) * entry_t),
        start.y + ((programmed_point.y - start.y) * entry_t),
        start.z + ((programmed_point.z - start.z) * entry_t),
        start.a,
        start.b,
        start.c,
    };
}

void apply_probe_motion(MachineState& state, const ParsedLine& parsed_line) {
    if (!state.probe_box.has_value()) {
        throw InputError("G38.2 requires --probe-box");
    }
    if (!state.probe_tool_number.has_value()) {
        throw InputError("G38.2 requires --probe-tool");
    }
    if (!state.tool_in_spindle.has_value() || *state.tool_in_spindle != *state.probe_tool_number) {
        throw InputError("G38.2 requires a probe in the spindle");
    }
    if (state.spindle_direction != SpindleDirection::kOff) {
        throw InputError("G38.2 requires the spindle to be stopped");
    }
    if (point_is_inside_probe_box(state.machine_position, *state.probe_box, state.current_length_unit)) {
        throw InputError("G38.2 cannot start with the probe already tripped");
    }

    const Position programmed_point{
        resolved_program_axis_endpoint(
            parsed_line.x,
            state.machine_position.x,
            state.coordinate_mode,
            active_program_origin_offset_for_axis(state, 0)
        ),
        resolved_program_axis_endpoint(
            parsed_line.y,
            state.machine_position.y,
            state.coordinate_mode,
            active_program_origin_offset_for_axis(state, 1)
        ),
        resolved_program_axis_endpoint(
            parsed_line.z,
            state.machine_position.z,
            state.coordinate_mode,
            active_program_origin_offset_for_axis(state, 2)
        ),
        position_axis_value(state.machine_position, 3),
        position_axis_value(state.machine_position, 4),
        position_axis_value(state.machine_position, 5),
    };

    const std::optional<Position> trip_point = find_probe_trip_point(
        state.machine_position,
        programmed_point,
        *state.probe_box,
        state.current_length_unit
    );
    if (!trip_point.has_value()) {
        throw InputError("G38.2 did not trip before the programmed point");
    }

    state.machine_position = *trip_point;
    set_parameter_value(state, kProbeTripXParameter, trip_point->x, state.current_length_unit);
    set_parameter_value(state, kProbeTripYParameter, trip_point->y, state.current_length_unit);
    set_parameter_value(state, kProbeTripZParameter, trip_point->z, state.current_length_unit);
    set_parameter_value(state, kProbeTripAParameter, state.machine_position.a);
    set_parameter_value(state, kProbeTripBParameter, state.machine_position.b);
    set_parameter_value(state, kProbeTripCParameter, state.machine_position.c);
}

struct CannedCycleAxes {
    int first_axis_index = 0;
    int second_axis_index = 1;
    int depth_axis_index = 2;
    char depth_axis_letter = 'Z';
};

CannedCycleAxes canned_cycle_axes_for_plane(Plane plane) {
    switch (plane) {
        case Plane::kXY:
            return CannedCycleAxes{0, 1, 2, 'Z'};
        case Plane::kXZ:
            return CannedCycleAxes{0, 2, 1, 'Y'};
        case Plane::kYZ:
            return CannedCycleAxes{1, 2, 0, 'X'};
    }

    throw std::runtime_error("Unsupported plane");
}

double position_axis_value(const Position& position, int axis_index) {
    switch (axis_index) {
        case 0:
            return position.x;
        case 1:
            return position.y;
        case 2:
            return position.z;
        case 3:
            return position.a;
        case 4:
            return position.b;
        case 5:
            return position.c;
        default:
            throw std::runtime_error("Unsupported axis index");
    }
}

double& position_axis_ref(Position& position, int axis_index) {
    switch (axis_index) {
        case 0:
            return position.x;
        case 1:
            return position.y;
        case 2:
            return position.z;
        case 3:
            return position.a;
        case 4:
            return position.b;
        case 5:
            return position.c;
        default:
            throw std::runtime_error("Unsupported axis index");
    }
}

std::optional<double> parsed_line_axis_word(const ParsedLine& parsed_line, int axis_index) {
    switch (axis_index) {
        case 0:
            return parsed_line.x;
        case 1:
            return parsed_line.y;
        case 2:
            return parsed_line.z;
        case 3:
            return parsed_line.a;
        case 4:
            return parsed_line.b;
        case 5:
            return parsed_line.c;
        default:
            throw std::runtime_error("Unsupported axis index");
    }
}

void apply_canned_cycle_motion(
    MachineState& state,
    const ParsedLine& parsed_line,
    std::string_view active_gcode,
    bool same_cycle_already_active
) {
    const CannedCycleAxes axes = canned_cycle_axes_for_plane(state.selected_plane);
    const std::optional<double> first_axis_word = parsed_line_axis_word(parsed_line, axes.first_axis_index);
    const std::optional<double> second_axis_word = parsed_line_axis_word(parsed_line, axes.second_axis_index);
    const std::optional<double> depth_axis_word = parsed_line_axis_word(parsed_line, axes.depth_axis_index);

    const double retract_word = parsed_line.r.has_value()
        ? *parsed_line.r
        : *state.canned_cycle_sticky_state.retract_word;
    const double depth_word = depth_axis_word.has_value()
        ? *depth_axis_word
        : *state.canned_cycle_sticky_state.depth_word;
    const double old_depth = position_axis_value(state.machine_position, axes.depth_axis_index);

    const double current_first = position_axis_value(state.machine_position, axes.first_axis_index);
    const double current_second = position_axis_value(state.machine_position, axes.second_axis_index);
    const double first_origin = active_program_origin_offset_for_axis(state, axes.first_axis_index);
    const double second_origin = active_program_origin_offset_for_axis(state, axes.second_axis_index);
    const double depth_origin = active_program_origin_offset_for_axis(state, axes.depth_axis_index);

    double retract_position = 0.0;
    double depth_position = 0.0;
    double final_first = current_first;
    double final_second = current_second;

    if (state.coordinate_mode == CoordinateMode::kAbsolute) {
        final_first = first_axis_word.has_value() ? first_origin + *first_axis_word : current_first;
        final_second =
            second_axis_word.has_value() ? second_origin + *second_axis_word : current_second;
        retract_position = depth_origin + retract_word;
        depth_position = depth_origin + depth_word;
    } else {
        final_first = current_first + (first_axis_word.value_or(0.0));
        final_second = current_second + (second_axis_word.value_or(0.0));
        retract_position = old_depth + retract_word;
        depth_position = retract_position + depth_word;

        const int repeat_count = parsed_line.l.has_value()
            ? round_if_close_to_integer(*parsed_line.l, "Canned cycle L word must be a positive integer")
            : 1;
        final_first = current_first + (first_axis_word.value_or(0.0) * repeat_count);
        final_second = current_second + (second_axis_word.value_or(0.0) * repeat_count);
    }

    if (retract_position < depth_position) {
        throw InputError("Canned cycle R position must not be below the depth position");
    }

    if (active_gcode == "G82") {
        (void)parsed_line.p;
    } else if (active_gcode == "G83") {
        (void)parsed_line.q;
    } else if (active_gcode == "G87") {
        (void)parsed_line.i;
        (void)parsed_line.j;
        (void)parsed_line.k;
    }

    const bool retract_to_old_position = !state.active_modal_g_codes.contains("10")
        || state.active_modal_g_codes.at("10") == "G98";
    const double clear_depth =
        retract_to_old_position && old_depth > retract_position ? old_depth : retract_position;

    position_axis_ref(state.machine_position, axes.first_axis_index) = final_first;
    position_axis_ref(state.machine_position, axes.second_axis_index) = final_second;
    position_axis_ref(state.machine_position, axes.depth_axis_index) = clear_depth;

    state.canned_cycle_sticky_state.retract_word = retract_word;
    state.canned_cycle_sticky_state.depth_axis_letter = axes.depth_axis_letter;
    state.canned_cycle_sticky_state.depth_word = depth_word;

    if (!same_cycle_already_active) {
        state.canned_cycle_sticky_state.depth_axis_letter = axes.depth_axis_letter;
    }
}

void apply_parameter_writes(const ParsedLine& parsed_line, MachineState& state) {
    for (const ParameterWrite& parameter_write : parsed_line.parameter_writes) {
        int system_number = 0;
        int axis_index = 0;
        bool secondary_home = false;
        if (decode_coordinate_system_axis_parameter(parameter_write.index, system_number, axis_index)) {
            // Direct writes to offset backing parameters update the stored offset data.
            set_coordinate_system_axis(state, system_number, axis_index, parameter_write.value);
            continue;
        }

        if (decode_home_axis_parameter(parameter_write.index, secondary_home, axis_index)) {
            set_parameter_value(
                state,
                parameter_write.index,
                parameter_write.value,
                state.current_length_unit
            );
            continue;
        }

        if (decode_g92_axis_parameter(parameter_write.index, axis_index)) {
            set_parameter_value(
                state,
                parameter_write.index,
                parameter_write.value,
                state.current_length_unit
            );
            continue;
        }

        set_parameter_value(state, parameter_write.index, parameter_write.value);
    }
}

void apply_g_code_value(double value, ParsedLine& parsed_line) {
    const int g_code_tenths = round_g_code_tenths_if_close(value);

    if (g_code_tenths == 382) {
        apply_g_code_word("G38.2", parsed_line);
        return;
    }
    if (g_code_tenths == 591) {
        apply_g_code_word("G59.1", parsed_line);
        return;
    }
    if (g_code_tenths == 592) {
        apply_g_code_word("G59.2", parsed_line);
        return;
    }
    if (g_code_tenths == 593) {
        apply_g_code_word("G59.3", parsed_line);
        return;
    }
    if (g_code_tenths == 611) {
        apply_g_code_word("G61.1", parsed_line);
        return;
    }
    if (g_code_tenths == 921) {
        apply_g_code_word("G92.1", parsed_line);
        return;
    }
    if (g_code_tenths == 922) {
        apply_g_code_word("G92.2", parsed_line);
        return;
    }
    if (g_code_tenths == 923) {
        apply_g_code_word("G92.3", parsed_line);
        return;
    }
    if (g_code_tenths % 10 != 0) {
        throw InputError("Unsupported G code value");
    }

    apply_g_code_word("G" + std::to_string(g_code_tenths / 10), parsed_line);
}

void apply_m_code_value(double value, ParsedLine& parsed_line) {
    apply_m_code_word(
        "M" + std::to_string(round_if_close_to_integer(value, "Unsupported M code value")),
        parsed_line
    );
}

void register_non_modal_g_code(ParsedLine& parsed_line, std::string_view active_gcode) {
    if (
        parsed_line.has_g4 || parsed_line.has_g10 || parsed_line.g92_command.has_value()
        || parsed_line.use_machine_coordinates || parsed_line.home_command.has_value()
    ) {
        throw InputError("Multiple G codes from the same modal group in the same block");
    }

    if (active_gcode == "G4") {
        parsed_line.has_g4 = true;
        return;
    }
    if (active_gcode == "G10") {
        parsed_line.has_g10 = true;
        return;
    }
    if (active_gcode == "G53") {
        parsed_line.use_machine_coordinates = true;
        return;
    }
    if (active_gcode == "G28" || active_gcode == "G30") {
        parsed_line.home_command = std::string(active_gcode);
        return;
    }

    parsed_line.g92_command = std::string(active_gcode);
}

void apply_g_code_word(const std::string& word, ParsedLine& parsed_line) {
    const std::string code = word.substr(1);

    if (code == "4") {
        register_non_modal_g_code(parsed_line, "G4");
        return;
    }
    if (code == "10") {
        register_non_modal_g_code(parsed_line, "G10");
        return;
    }
    if (code == "28") {
        register_non_modal_g_code(parsed_line, "G28");
        return;
    }
    if (code == "30") {
        register_non_modal_g_code(parsed_line, "G30");
        return;
    }
    if (code == "53") {
        register_non_modal_g_code(parsed_line, "G53");
        return;
    }
    if (code == "92" || code == "92.1" || code == "92.2" || code == "92.3") {
        register_non_modal_g_code(parsed_line, word);
        return;
    }
    if (
        code == "0" || code == "1" || code == "2" || code == "3" || code == "38.2"
        || code == "80" || code == "81" || code == "82" || code == "83" || code == "84"
        || code == "85" || code == "86" || code == "87" || code == "88" || code == "89"
    ) {
        register_modal_g_code(parsed_line, "1", word);
        return;
    }
    if (code == "17" || code == "18" || code == "19") {
        register_modal_g_code(parsed_line, "2", word);
        return;
    }
    if (code == "90" || code == "91") {
        register_modal_g_code(parsed_line, "3", word);
        return;
    }
    if (code == "93" || code == "94") {
        register_modal_g_code(parsed_line, "5", word);
        return;
    }
    if (code == "20" || code == "21") {
        register_modal_g_code(parsed_line, "6", word);
        return;
    }
    if (code == "40" || code == "41" || code == "42") {
        register_modal_g_code(parsed_line, "7", word);
        return;
    }
    if (code == "43" || code == "49") {
        register_modal_g_code(parsed_line, "8", word);
        return;
    }
    if (code == "98" || code == "99") {
        register_modal_g_code(parsed_line, "10", word);
        return;
    }
    if (
        code == "54" || code == "55" || code == "56" || code == "57" || code == "58"
        || code == "59" || code == "59.1" || code == "59.2" || code == "59.3"
    ) {
        register_modal_g_code(parsed_line, "12", word);
        return;
    }
    if (code == "61" || code == "61.1" || code == "64") {
        register_modal_g_code(parsed_line, "13", word);
        return;
    }

    throw InputError("Unsupported G code: " + word);
}

void apply_m_code_word(const std::string& word, ParsedLine& parsed_line) {
    const std::string code = word.substr(1);

    if (code == "0" || code == "1" || code == "2" || code == "30" || code == "60") {
        register_modal_m_code(parsed_line, "4", word);
        if (code == "2" || code == "30") {
            parsed_line.end_program = true;
        }
        return;
    }
    if (code == "6") {
        register_modal_m_code(parsed_line, "6", word);
        return;
    }
    if (code == "3" || code == "4" || code == "5") {
        register_modal_m_code(parsed_line, "7", word);
        if (code == "3") {
            parsed_line.spindle_direction = SpindleDirection::kClockwise;
        } else if (code == "4") {
            parsed_line.spindle_direction = SpindleDirection::kCounterClockwise;
        } else {
            parsed_line.spindle_direction = SpindleDirection::kOff;
        }
        return;
    }
    if (code == "7" || code == "8" || code == "9") {
        register_modal_m_code(parsed_line, "8", word);
        return;
    }
    if (code == "48" || code == "49") {
        register_modal_m_code(parsed_line, "9", word);
        return;
    }

    throw InputError("Unsupported M code: " + word);
}

void register_modal_g_code(
    ParsedLine& parsed_line,
    std::string_view group_number,
    std::string_view active_gcode
) {
    const std::string group_key(group_number);
    if (parsed_line.active_modal_g_codes.contains(group_key)) {
        throw InputError("Multiple G codes from the same modal group in the same block");
    }

    parsed_line.active_modal_g_codes.emplace(group_key, std::string(active_gcode));
}

void register_modal_m_code(
    ParsedLine& parsed_line,
    std::string_view group_number,
    std::string_view active_mcode
) {
    const std::string group_key(group_number);
    if (parsed_line.active_modal_m_codes.contains(group_key)) {
        throw InputError("Multiple M codes from the same modal group in the same block");
    }
    if (parsed_line.active_modal_m_codes.size() >= 4) {
        throw InputError("A line may have at most four M words");
    }

    parsed_line.active_modal_m_codes.emplace(group_key, std::string(active_mcode));
}

std::string coordinate_system_number_for_g_code(std::string_view active_gcode) {
    if (active_gcode == "G54") {
        return "1";
    }
    if (active_gcode == "G55") {
        return "2";
    }
    if (active_gcode == "G56") {
        return "3";
    }
    if (active_gcode == "G57") {
        return "4";
    }
    if (active_gcode == "G58") {
        return "5";
    }
    if (active_gcode == "G59") {
        return "6";
    }
    if (active_gcode == "G59.1") {
        return "7";
    }
    if (active_gcode == "G59.2") {
        return "8";
    }
    if (active_gcode == "G59.3") {
        return "9";
    }

    throw std::runtime_error("Unsupported coordinate system selection: " + std::string(active_gcode));
}

void reset_after_program_end(MachineState& state) {
    state.coordinate_mode = CoordinateMode::kAbsolute;
    state.selected_plane = Plane::kXY;
    state.active_modal_g_codes["1"] = "G1";
    state.active_modal_g_codes["2"] = "G17";
    state.active_modal_g_codes["3"] = "G90";
    state.active_modal_g_codes["5"] = "G94";
    state.active_modal_g_codes["7"] = "G40";
    state.active_modal_g_codes["13"] = "G64";
    deactivate_cutter_radius_compensation(state);
    set_selected_coordinate_system(state, 1);
    reset_g92_axis_offsets(state, false);
    state.active_modal_m_codes["7"] = "M5";
    state.active_modal_m_codes["8"] = "M9";
    state.active_modal_m_codes["9"] = "M48";
    state.spindle_direction = SpindleDirection::kOff;
}

std::string parse_g10_coordinate_system_number(const ParsedLine& parsed_line) {
    if (!parsed_line.l.has_value()) {
        throw InputError("G10 requires an L word");
    }
    if (std::floor(*parsed_line.l) != *parsed_line.l || *parsed_line.l != 2.0) {
        throw InputError("Only G10 L2 is supported");
    }
    if (!parsed_line.p.has_value()) {
        throw InputError("G10 L2 requires a P word");
    }
    if (std::floor(*parsed_line.p) != *parsed_line.p || *parsed_line.p < 1.0 || *parsed_line.p > 9.0)
    {
        throw InputError("G10 L2 P number must be an integer from 1 to 9");
    }

    return std::to_string(static_cast<int>(*parsed_line.p));
}

std::string strip_comments(std::string_view raw_line) {
    std::string cleaned;
    bool in_parenthetical_comment = false;

    for (const char raw_character : raw_line) {
        const auto character = static_cast<unsigned char>(raw_character);
        if (!in_parenthetical_comment && character == ';') {
            break;
        }
        if (character == '(') {
            if (in_parenthetical_comment) {
                throw InputError("Comments may not be nested");
            }
            in_parenthetical_comment = true;
            continue;
        }
        if (character == ')') {
            if (!in_parenthetical_comment) {
                throw InputError("Unmatched right parenthesis");
            }
            in_parenthetical_comment = false;
            continue;
        }
        if (in_parenthetical_comment) {
            if (character != '\t' && std::isprint(character) == 0) {
                throw InputError("Comments may contain only printable characters, space, and tab");
            }
            continue;
        }
        cleaned.push_back(static_cast<char>(character));
    }

    if (in_parenthetical_comment) {
        throw InputError("Unterminated parenthetical comment");
    }

    return cleaned;
}

std::string json_escape(std::string_view text) {
    std::string escaped;
    escaped.reserve(text.size());
    for (const char character : text) {
        switch (character) {
            case '\\':
                escaped += "\\\\";
                break;
            case '"':
                escaped += "\\\"";
                break;
            case '\n':
                escaped += "\\n";
                break;
            case '\r':
                escaped += "\\r";
                break;
            case '\t':
                escaped += "\\t";
                break;
            default:
                escaped.push_back(character);
                break;
        }
    }

    return escaped;
}

std::vector<std::string> split_words(std::string_view line) {
    std::vector<std::string> words;
    std::string current_word;

    for (const char raw_character : line) {
        const auto character = static_cast<unsigned char>(raw_character);
        if (std::isalpha(character) != 0) {
            if (!current_word.empty()) {
                words.push_back(current_word);
                current_word.clear();
            }
            current_word.push_back(static_cast<char>(std::toupper(character)));
            continue;
        }
        if (std::isspace(character) != 0) {
            if (!current_word.empty()) {
                words.push_back(current_word);
                current_word.clear();
            }
            continue;
        }
        if (!current_word.empty()) {
            current_word.push_back(static_cast<char>(character));
        }
    }

    if (!current_word.empty()) {
        words.push_back(current_word);
    }

    return words;
}

double parse_numeric_suffix(const std::string& word) {
    if (word.size() <= 1) {
        throw InputError("Missing numeric value for word: " + word);
    }

    try {
        std::size_t processed_length = 0;
        const double value = std::stod(word.substr(1), &processed_length);
        if (processed_length != word.size() - 1) {
            throw InputError("Invalid numeric value for word: " + word);
        }
        return value;
    } catch (const std::invalid_argument&) {
        throw InputError("Invalid numeric value for word: " + word);
    } catch (const std::out_of_range&) {
        throw InputError("Numeric value out of range for word: " + word);
    }
}

int parse_non_negative_integer_suffix(const std::string& word) {
    const double value = parse_numeric_suffix(word);
    if (std::floor(value) != value || value < 0.0) {
        throw InputError("Expected non-negative integer value for word: " + word);
    }

    return static_cast<int>(value);
}

std::string to_json(const MachineState& state, std::optional<std::string_view> error) {
    std::ostringstream output;
    output << std::setprecision(15) << std::defaultfloat;
    output << "{\n"
           << "  \"machine_position\": {\"x\": " << state.machine_position.x << ", \"y\": "
           << state.machine_position.y << ", \"z\": " << state.machine_position.z << ", \"a\": "
           << state.machine_position.a << ", \"b\": " << state.machine_position.b << ", \"c\": "
           << state.machine_position.c << "},\n"
           << "  \"feed_rate\": " << state.feed_rate << ",\n"
           << "  \"spindle_speed\": " << state.spindle_speed << ",\n"
           << "  \"spindle_direction\": \"" << to_string(state.spindle_direction) << "\",\n"
           << "  \"cutter_radius_compensation_number\": ";
    if (state.cutter_radius_compensation_number.has_value()) {
        output << *state.cutter_radius_compensation_number;
    } else {
        output << "null";
    }
    output << ",\n"
           << "  \"tool_length_offset_index\": ";
    if (state.tool_length_offset_index.has_value()) {
        output << *state.tool_length_offset_index;
    } else {
        output << "null";
    }
    output << ",\n"
           << "  \"selected_tool\": ";
    if (state.selected_tool.has_value()) {
        output << *state.selected_tool;
    } else {
        output << "null";
    }
    output << ",\n"
           << "  \"tool_in_spindle\": ";
    if (state.tool_in_spindle.has_value()) {
        output << *state.tool_in_spindle;
    } else {
        output << "null";
    }
    output << ",\n"
           << "  \"active_modal_g_codes\": {";

    bool is_first_modal_code = true;
    for (const auto& [group_number, active_gcode] : state.active_modal_g_codes) {
        if (!is_first_modal_code) {
            output << ", ";
        }
        output << "\"" << group_number << "\": \"" << active_gcode << "\"";
        is_first_modal_code = false;
    }

    output << "},\n"
           << "  \"active_modal_m_codes\": {";

    bool is_first_active_mcode = true;
    for (const auto& [group_number, active_mcode] : state.active_modal_m_codes) {
        if (!is_first_active_mcode) {
            output << ", ";
        }
        output << "\"" << group_number << "\": \"" << active_mcode << "\"";
        is_first_active_mcode = false;
    }

    output << "},\n"
           << "  \"coordinate_system_offsets\": {";

    bool is_first_coordinate_system = true;
    for (const auto& [system_number, offset] : state.coordinate_system_offsets) {
        if (!is_first_coordinate_system) {
            output << ", ";
        }
        output << "\"" << system_number << "\": "
               << "{\"x\": " << offset.x << ", \"y\": " << offset.y << ", \"z\": " << offset.z
               << ", \"a\": " << offset.a << ", \"b\": " << offset.b << ", \"c\": "
               << offset.c << "}";
        is_first_coordinate_system = false;
    }

    output << "},\n"
           << "  \"parameters\": {";

    bool is_first_parameter = true;
    for (int parameter_index = kMinParameterIndex; parameter_index <= kMaxParameterFileIndex; ++parameter_index) {
        if (!state.reported_parameters.at(parameter_index)) {
            continue;
        }
        if (!is_first_parameter) {
            output << ", ";
        }
        output << "\"" << parameter_index << "\": " << state.parameters.at(parameter_index);
        is_first_parameter = false;
    }

    output << "},\n"
           << "  \"error\": ";
    if (error.has_value()) {
        output << '"' << json_escape(*error) << '"';
    } else {
        output << "null";
    }
    output << "\n}\n";
    return output.str();
}

bool is_required_parameter(int parameter_index) {
    if (
        (parameter_index >= 5161 && parameter_index <= 5166)
        || (parameter_index >= 5181 && parameter_index <= 5186)
        || (parameter_index >= 5211 && parameter_index <= 5216)
        || parameter_index == 5220
    ) {
        return true;
    }

    int system_number = 0;
    int axis_index = 0;
    return decode_coordinate_system_axis_parameter(parameter_index, system_number, axis_index);
}

std::string to_parameter_file(const MachineState& state) {
    std::ostringstream output;
    output << "RS274 parameter file\n\n";

    for (int parameter_index = kMinParameterIndex; parameter_index <= kMaxParameterFileIndex; ++parameter_index) {
        if (
            !is_required_parameter(parameter_index)
            && !state.reported_parameters.at(parameter_index)
        ) {
            continue;
        }

        output << parameter_index << ' ' << state.parameters.at(parameter_index) << '\n';
    }

    return output.str();
}

std::string to_string(SpindleDirection direction) {
    switch (direction) {
        case SpindleDirection::kClockwise:
            return "CW";
        case SpindleDirection::kCounterClockwise:
            return "CCW";
        case SpindleDirection::kOff:
            return "OFF";
    }

    throw std::runtime_error("Unknown spindle direction");
}

void write_output_file(const std::string& output_path, const std::string& contents) {
    std::ofstream output_stream(output_path, std::ios::trunc);
    if (!output_stream.is_open()) {
        throw std::runtime_error("Could not open output file: " + output_path);
    }

    output_stream << contents;
}

}  // namespace

int main(int argc, char* argv[]) {
    ProgramOptions options;
    try {
        options = parse_command_line(argc, argv);
    } catch (const InputError& error) {
        std::cerr << error.what() << '\n';
        return static_cast<int>(ExitCode::kInvalidInput);
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return static_cast<int>(ExitCode::kInternalError);
    }

    try {
        const MachineState final_state = execute_program(
            options.input_path,
            options.block_delete,
            options.carousel_slots,
            options.parameter_input_path,
            options.tool_table_path,
            options.probe_box,
            options.probe_tool_number
        );
        write_output_file(options.output_path, to_json(final_state));
        if (options.parameter_output_path.has_value()) {
            write_output_file(*options.parameter_output_path, to_parameter_file(final_state));
        }
        return static_cast<int>(ExitCode::kSuccess);
    } catch (const InputError& error) {
        write_output_file(options.output_path, to_json(MachineState{}, error.what()));
        std::cerr << error.what() << '\n';
        return static_cast<int>(ExitCode::kInvalidInput);
    } catch (const std::exception& error) {
        write_output_file(options.output_path, to_json(MachineState{}, error.what()));
        std::cerr << error.what() << '\n';
        return static_cast<int>(ExitCode::kInternalError);
    }
}
