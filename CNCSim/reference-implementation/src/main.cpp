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

enum class SpindleDirection {
    kClockwise,
    kCounterClockwise,
    kOff,
};

struct Position {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
};

struct ParameterWrite {
    int index = 0;
    double value = 0.0;
};

constexpr int kMinParameterIndex = 1;
constexpr int kMaxParameterIndex = 5399;
constexpr int kParameterCount = kMaxParameterIndex + 1;
constexpr int kSelectedCoordinateSystemParameter = 5220;
constexpr int kG92XAxisOffsetParameter = 5211;
constexpr int kG92YAxisOffsetParameter = 5212;
constexpr int kG92ZAxisOffsetParameter = 5213;
constexpr double kNearIntegerTolerance = 0.0001;

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

struct MachineState {
    std::map<std::string, std::string> active_modal_g_codes;
    std::map<std::string, std::string> active_modal_m_codes;
    std::map<std::string, Position> coordinate_system_offsets = make_default_coordinate_system_offsets();
    std::vector<double> parameters = make_default_parameters();
    std::vector<bool> reported_parameters = make_default_reported_parameters();
    Position machine_position{};
    Position g92_axis_offsets{};
    double feed_rate = 0.0;
    double spindle_speed = 0.0;
    SpindleDirection spindle_direction = SpindleDirection::kOff;
    std::optional<int> cutter_radius_compensation_number;
    std::optional<int> tool_length_offset_index;
    std::optional<int> selected_tool;
    CoordinateMode coordinate_mode = CoordinateMode::kAbsolute;
    Plane selected_plane = Plane::kXY;
    std::string selected_coordinate_system = "1";
};

struct ProgramOptions {
    std::string input_path;
    std::string output_path;
};

struct ParsedLine {
    std::map<std::string, std::string> active_modal_g_codes;
    std::map<std::string, std::string> active_modal_m_codes;
    std::vector<ParameterWrite> parameter_writes;
    std::optional<double> x;
    std::optional<double> y;
    std::optional<double> z;
    std::optional<double> d;
    std::optional<int> h;
    std::optional<double> i;
    std::optional<double> j;
    std::optional<double> k;
    std::optional<double> l;
    std::optional<double> p;
    std::optional<double> r;
    std::optional<int> t;
    std::optional<std::string> coordinate_system_offset_target;
    std::optional<std::string> g92_command;
    std::optional<double> feed_rate;
    std::optional<double> spindle_speed;
    std::optional<SpindleDirection> spindle_direction;
    bool has_g10 = false;
    bool end_program = false;
};

class InputError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

ProgramOptions parse_command_line(int argc, char* argv[]);
MachineState execute_program(const std::string& input_path);
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
bool is_arc_motion(std::string_view active_gcode);
bool is_linear_motion(std::string_view active_gcode);
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
void validate_linear_motion_command(const ParsedLine& parsed_line, const MachineState& state);
void validate_arc_command(const ParsedLine& parsed_line, const MachineState& state);
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
void set_parameter_value(MachineState& state, int parameter_index, double value);
void set_selected_coordinate_system(MachineState& state, int system_number);
void set_coordinate_system_axis(MachineState& state, int system_number, int axis_index, double value);
void set_g92_axis_offset(MachineState& state, int axis_index, double value);
void reset_g92_axis_offsets(MachineState& state, bool reset_parameters);
void restore_g92_axis_offsets_from_parameters(MachineState& state);
double active_program_origin_offset_for_axis(const MachineState& state, int axis_index);
void apply_parameter_writes(const ParsedLine& parsed_line, MachineState& state);
void reset_after_program_end(MachineState& state);
std::string parse_g10_coordinate_system_number(const ParsedLine& parsed_line);
std::string strip_comments(std::string_view raw_line);
std::string json_escape(std::string_view text);
std::string to_json(const MachineState& state, std::optional<std::string_view> error = std::nullopt);
std::string to_string(SpindleDirection direction);
void write_output_file(const std::string& output_path, const std::string& contents);

ProgramOptions parse_command_line(int argc, char* argv[]) {
    ProgramOptions options;

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

        throw InputError("Usage: cncsim_reference --input <gcode_file> --output <result_file>");
    }

    if (options.input_path.empty() || options.output_path.empty()) {
        throw InputError("Usage: cncsim_reference --input <gcode_file> --output <result_file>");
    }

    return options;
}

MachineState execute_program(const std::string& input_path) {
    std::ifstream input_stream(input_path);
    if (!input_stream.is_open()) {
        throw InputError("Could not open input file: " + input_path);
    }

    MachineState state;
    std::string line;
    while (std::getline(input_stream, line)) {
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
        case 'D':
            assign_unique_word(
                parsed_line.d,
                parse_real_value(text, position, state),
                std::string_view("D")
            );
            return;
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
            assign_unique_word(
                parsed_line.h,
                require_non_negative_integer(
                    parse_real_value(text, position, state),
                    std::string_view("H")
                ),
                std::string_view("H")
            );
            return;
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
            assign_unique_word(
                parsed_line.t,
                require_non_negative_integer(
                    parse_real_value(text, position, state),
                    std::string_view("T")
                ),
                std::string_view("T")
            );
            return;
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

    if (!parsed_line.has_g10 && (parsed_line.l.has_value() || parsed_line.p.has_value())) {
        throw InputError("Unsupported L or P word without G10");
    }
    if (parsed_line.has_g10) {
        parsed_line.coordinate_system_offset_target = parse_g10_coordinate_system_number(parsed_line);
    }
    if (parsed_line.g92_command.has_value() && *parsed_line.g92_command == "G92"
        && !has_linear_axis_word(parsed_line))
    {
        throw InputError("G92 requires at least one axis word");
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
    for (const auto& [group_number, active_gcode] : parsed_line.active_modal_g_codes) {
        state.active_modal_g_codes[group_number] = active_gcode;
        if (group_number == "3") {
            state.coordinate_mode =
                active_gcode == "G90" ? CoordinateMode::kAbsolute : CoordinateMode::kIncremental;
        } else if (group_number == "2") {
            state.selected_plane = plane_for_g_code(active_gcode);
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

    if (parsed_line.feed_rate.has_value()) {
        state.feed_rate = *parsed_line.feed_rate;
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

    if (parsed_line.active_modal_g_codes.contains("7")) {
        const std::string_view active_crc = parsed_line.active_modal_g_codes.at("7");
        if (active_crc == "G40") {
            state.cutter_radius_compensation_number = std::nullopt;
        } else if (parsed_line.d.has_value()) {
            state.cutter_radius_compensation_number = static_cast<int>(*parsed_line.d);
        }
    }
    if (parsed_line.active_modal_g_codes.contains("8")) {
        const std::string_view active_tlo = parsed_line.active_modal_g_codes.at("8");
        if (active_tlo == "G49") {
            state.tool_length_offset_index = std::nullopt;
        } else if (parsed_line.h.has_value()) {
            state.tool_length_offset_index = *parsed_line.h;
        }
    }

    if (parsed_line.coordinate_system_offset_target.has_value()) {
        const int system_number = std::stoi(*parsed_line.coordinate_system_offset_target);
        if (parsed_line.x.has_value()) {
            set_coordinate_system_axis(state, system_number, 0, *parsed_line.x);
        }
        if (parsed_line.y.has_value()) {
            set_coordinate_system_axis(state, system_number, 1, *parsed_line.y);
        }
        if (parsed_line.z.has_value()) {
            set_coordinate_system_axis(state, system_number, 2, *parsed_line.z);
        }
    } else if (parsed_line.g92_command.has_value()) {
        const std::string& g92_command = *parsed_line.g92_command;
        if (g92_command == "G92") {
            const Position& coordinate_system_offset =
                state.coordinate_system_offsets.at(state.selected_coordinate_system);
            if (parsed_line.x.has_value()) {
                set_g92_axis_offset(
                    state,
                    0,
                    state.machine_position.x - coordinate_system_offset.x - *parsed_line.x
                );
            }
            if (parsed_line.y.has_value()) {
                set_g92_axis_offset(
                    state,
                    1,
                    state.machine_position.y - coordinate_system_offset.y - *parsed_line.y
                );
            }
            if (parsed_line.z.has_value()) {
                set_g92_axis_offset(
                    state,
                    2,
                    state.machine_position.z - coordinate_system_offset.z - *parsed_line.z
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
    } else {
        validate_linear_motion_command(parsed_line, state);
        validate_arc_command(parsed_line, state);
        apply_program_axis_value(
            parsed_line.x,
            state.machine_position.x,
            state.coordinate_mode,
            active_program_origin_offset_for_axis(state, 0)
        );
        apply_program_axis_value(
            parsed_line.y,
            state.machine_position.y,
            state.coordinate_mode,
            active_program_origin_offset_for_axis(state, 1)
        );
        apply_program_axis_value(
            parsed_line.z,
            state.machine_position.z,
            state.coordinate_mode,
            active_program_origin_offset_for_axis(state, 2)
        );
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
    return parsed_line.x.has_value() || parsed_line.y.has_value() || parsed_line.z.has_value();
}

bool line_has_motion_axis_word(const ParsedLine& parsed_line) {
    return has_linear_axis_word(parsed_line);
}

void validate_linear_motion_command(const ParsedLine& parsed_line, const MachineState& state) {
    const auto current_motion = state.active_modal_g_codes.find("1");
    if (current_motion == state.active_modal_g_codes.end()) {
        return;
    }

    const bool explicit_motion = parsed_line.active_modal_g_codes.contains("1");
    const std::string_view effective_motion = explicit_motion
        ? std::string_view(parsed_line.active_modal_g_codes.at("1"))
        : std::string_view(current_motion->second);
    const bool implicit_motion = !explicit_motion && line_has_motion_axis_word(parsed_line);

    if (explicit_motion && is_linear_motion(effective_motion) && !has_linear_axis_word(parsed_line)) {
        throw InputError("G0/G1 requires at least one axis word");
    }

    const auto feed_rate_mode = state.active_modal_g_codes.find("5");
    const bool inverse_time_feed_rate = feed_rate_mode != state.active_modal_g_codes.end()
        && feed_rate_mode->second == "G93";
    if (!inverse_time_feed_rate) {
        return;
    }

    if ((explicit_motion || implicit_motion) && is_feed_rate_motion(effective_motion)
        && !parsed_line.feed_rate.has_value())
    {
        throw InputError("Inverse time feed rate motion requires an F word");
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
    if (parameter_index < 5221 || parameter_index > 5383) {
        return false;
    }

    const int relative_index = parameter_index - 5221;
    const int within_system_block = relative_index % 20;
    if (within_system_block < 0 || within_system_block > 2) {
        return false;
    }

    system_number = (relative_index / 20) + 1;
    axis_index = within_system_block;
    return system_number >= 1 && system_number <= 9;
}

void set_parameter_value(MachineState& state, int parameter_index, double value) {
    state.parameters[parameter_index] = value;
    state.reported_parameters[parameter_index] = true;
}

void set_selected_coordinate_system(MachineState& state, int system_number) {
    state.selected_coordinate_system = std::to_string(system_number);
    set_parameter_value(state, kSelectedCoordinateSystemParameter, static_cast<double>(system_number));
    state.active_modal_g_codes["12"] = active_g_code_for_coordinate_system_number(system_number);
}

void set_coordinate_system_axis(MachineState& state, int system_number, int axis_index, double value) {
    Position& coordinate_system_offset = state.coordinate_system_offsets.at(std::to_string(system_number));
    switch (axis_index) {
        case 0:
            coordinate_system_offset.x = value;
            break;
        case 1:
            coordinate_system_offset.y = value;
            break;
        case 2:
            coordinate_system_offset.z = value;
            break;
        default:
            throw std::runtime_error("Unsupported coordinate system axis");
    }

    set_parameter_value(state, parameter_index_for_coordinate_system_axis(system_number, axis_index), value);
}

void set_g92_axis_offset(MachineState& state, int axis_index, double value) {
    switch (axis_index) {
        case 0:
            state.g92_axis_offsets.x = value;
            set_parameter_value(state, kG92XAxisOffsetParameter, value);
            return;
        case 1:
            state.g92_axis_offsets.y = value;
            set_parameter_value(state, kG92YAxisOffsetParameter, value);
            return;
        case 2:
            state.g92_axis_offsets.z = value;
            set_parameter_value(state, kG92ZAxisOffsetParameter, value);
            return;
        default:
            throw std::runtime_error("Unsupported G92 axis");
    }
}

void reset_g92_axis_offsets(MachineState& state, bool reset_parameters) {
    state.g92_axis_offsets = {};
    if (reset_parameters) {
        set_parameter_value(state, kG92XAxisOffsetParameter, 0.0);
        set_parameter_value(state, kG92YAxisOffsetParameter, 0.0);
        set_parameter_value(state, kG92ZAxisOffsetParameter, 0.0);
    }
}

void restore_g92_axis_offsets_from_parameters(MachineState& state) {
    state.g92_axis_offsets.x = state.parameters[kG92XAxisOffsetParameter];
    state.g92_axis_offsets.y = state.parameters[kG92YAxisOffsetParameter];
    state.g92_axis_offsets.z = state.parameters[kG92ZAxisOffsetParameter];
}

double active_program_origin_offset_for_axis(const MachineState& state, int axis_index) {
    const Position& coordinate_system_offset =
        state.coordinate_system_offsets.at(state.selected_coordinate_system);
    switch (axis_index) {
        case 0:
            return coordinate_system_offset.x + state.g92_axis_offsets.x;
        case 1:
            return coordinate_system_offset.y + state.g92_axis_offsets.y;
        case 2:
            return coordinate_system_offset.z + state.g92_axis_offsets.z;
        default:
            throw std::runtime_error("Unsupported axis index");
    }
}

void apply_parameter_writes(const ParsedLine& parsed_line, MachineState& state) {
    for (const ParameterWrite& parameter_write : parsed_line.parameter_writes) {
        set_parameter_value(state, parameter_write.index, parameter_write.value);

        int system_number = 0;
        int axis_index = 0;
        if (decode_coordinate_system_axis_parameter(parameter_write.index, system_number, axis_index)) {
            // Direct writes to offset backing parameters update the stored offset data.
            set_coordinate_system_axis(state, system_number, axis_index, parameter_write.value);
        }
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
    if (parsed_line.has_g10 || parsed_line.g92_command.has_value()) {
        throw InputError("Multiple G codes from the same modal group in the same block");
    }

    if (active_gcode == "G10") {
        parsed_line.has_g10 = true;
        return;
    }

    parsed_line.g92_command = std::string(active_gcode);
}

void apply_g_code_word(const std::string& word, ParsedLine& parsed_line) {
    const std::string code = word.substr(1);

    if (code == "10") {
        register_non_modal_g_code(parsed_line, "G10");
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
           << state.machine_position.y << ", \"z\": " << state.machine_position.z << "},\n"
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
               << "}";
        is_first_coordinate_system = false;
    }

    output << "},\n"
           << "  \"parameters\": {";

    bool is_first_parameter = true;
    for (int parameter_index = kMinParameterIndex; parameter_index <= kMaxParameterIndex; ++parameter_index) {
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
        const MachineState final_state = execute_program(options.input_path);
        write_output_file(options.output_path, to_json(final_state));
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
