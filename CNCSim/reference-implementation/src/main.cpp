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

struct MachineState {
    std::map<std::string, std::string> active_modal_g_codes;
    std::map<std::string, std::string> active_modal_m_codes;
    std::map<std::string, Position> coordinate_system_offsets = make_default_coordinate_system_offsets();
    Position position{};
    double feed_rate = 0.0;
    double spindle_speed = 0.0;
    SpindleDirection spindle_direction = SpindleDirection::kOff;
    CoordinateMode coordinate_mode = CoordinateMode::kAbsolute;
};

struct ProgramOptions {
    std::string input_path;
    std::string output_path;
};

struct ParsedLine {
    std::map<std::string, std::string> active_modal_g_codes;
    std::map<std::string, std::string> active_modal_m_codes;
    std::optional<double> x;
    std::optional<double> y;
    std::optional<double> z;
    std::optional<double> l;
    std::optional<double> p;
    std::optional<std::string> coordinate_system_offset_target;
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
ParsedLine parse_line(std::string_view raw_line);
void apply_line(const ParsedLine& parsed_line, MachineState& state);
void apply_axis_value(std::optional<double> value, double& axis, CoordinateMode coordinate_mode);
void apply_coordinate_system_axis_value(std::optional<double> value, double& axis);
void apply_g_code_word(const std::string& word, ParsedLine& parsed_line);
void apply_m_code_word(const std::string& word, ParsedLine& parsed_line);
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
void reset_after_program_end(MachineState& state);
std::string parse_g10_coordinate_system_number(const ParsedLine& parsed_line);
std::string strip_comments(std::string_view raw_line);
std::vector<std::string> split_words(std::string_view line);
double parse_numeric_suffix(const std::string& word);
std::string to_json(const MachineState& state);
std::string to_string(SpindleDirection direction);

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
        const ParsedLine parsed_line = parse_line(line);
        apply_line(parsed_line, state);
        if (parsed_line.end_program) {
            break;
        }
    }

    return state;
}

ParsedLine parse_line(std::string_view raw_line) {
    ParsedLine parsed_line;

    for (const std::string& word : split_words(strip_comments(raw_line))) {
        if (word.empty()) {
            continue;
        }

        const char letter = word.front();
        switch (letter) {
            case 'D':
            case 'H':
            case 'I':
            case 'J':
            case 'K':
            case 'R':
                static_cast<void>(parse_numeric_suffix(word));
                break;
            case 'F':
                parsed_line.feed_rate = parse_numeric_suffix(word);
                break;
            case 'G':
                apply_g_code_word(word, parsed_line);
                break;
            case 'L':
                parsed_line.l = parse_numeric_suffix(word);
                break;
            case 'M':
                apply_m_code_word(word, parsed_line);
                break;
            case 'N':
                break;
            case 'P':
                parsed_line.p = parse_numeric_suffix(word);
                break;
            case 'S':
                parsed_line.spindle_speed = parse_numeric_suffix(word);
                break;
            case 'X':
                parsed_line.x = parse_numeric_suffix(word);
                break;
            case 'Y':
                parsed_line.y = parse_numeric_suffix(word);
                break;
            case 'Z':
                parsed_line.z = parse_numeric_suffix(word);
                break;
            default:
                throw InputError("Unsupported word: " + word);
        }
    }

    if (!parsed_line.has_g10 && (parsed_line.l.has_value() || parsed_line.p.has_value())) {
        throw InputError("Unsupported L or P word without G10");
    }
    if (parsed_line.has_g10) {
        parsed_line.coordinate_system_offset_target = parse_g10_coordinate_system_number(parsed_line);
    }

    return parsed_line;
}

void apply_line(const ParsedLine& parsed_line, MachineState& state) {
    for (const auto& [group_number, active_gcode] : parsed_line.active_modal_g_codes) {
        state.active_modal_g_codes[group_number] = active_gcode;
        if (group_number == "3") {
            state.coordinate_mode =
                active_gcode == "G90" ? CoordinateMode::kAbsolute : CoordinateMode::kIncremental;
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

    if (parsed_line.coordinate_system_offset_target.has_value()) {
        Position& coordinate_system_offset =
            state.coordinate_system_offsets.at(*parsed_line.coordinate_system_offset_target);
        apply_coordinate_system_axis_value(parsed_line.x, coordinate_system_offset.x);
        apply_coordinate_system_axis_value(parsed_line.y, coordinate_system_offset.y);
        apply_coordinate_system_axis_value(parsed_line.z, coordinate_system_offset.z);
    } else {
        apply_axis_value(parsed_line.x, state.position.x, state.coordinate_mode);
        apply_axis_value(parsed_line.y, state.position.y, state.coordinate_mode);
        apply_axis_value(parsed_line.z, state.position.z, state.coordinate_mode);
    }

    if (parsed_line.end_program) {
        reset_after_program_end(state);
    }
}

void apply_axis_value(std::optional<double> value, double& axis, CoordinateMode coordinate_mode) {
    if (!value.has_value()) {
        return;
    }

    if (coordinate_mode == CoordinateMode::kAbsolute) {
        axis = *value;
        return;
    }

    axis += *value;
}

void apply_coordinate_system_axis_value(std::optional<double> value, double& axis) {
    if (!value.has_value()) {
        return;
    }

    axis = *value;
}

void apply_g_code_word(const std::string& word, ParsedLine& parsed_line) {
    const std::string code = word.substr(1);

    if (code == "10") {
        parsed_line.has_g10 = true;
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

    parsed_line.active_modal_m_codes.emplace(group_key, std::string(active_mcode));
}

void reset_after_program_end(MachineState& state) {
    state.coordinate_mode = CoordinateMode::kAbsolute;
    state.active_modal_g_codes["1"] = "G1";
    state.active_modal_g_codes["2"] = "G17";
    state.active_modal_g_codes["3"] = "G90";
    state.active_modal_g_codes["5"] = "G94";
    state.active_modal_g_codes["7"] = "G40";
    state.active_modal_g_codes["12"] = "G54";
    state.active_modal_g_codes["13"] = "G64";
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

    for (const char character : raw_line) {
        if (!in_parenthetical_comment && character == ';') {
            break;
        }
        if (character == '(') {
            in_parenthetical_comment = true;
            continue;
        }
        if (character == ')') {
            in_parenthetical_comment = false;
            continue;
        }
        if (!in_parenthetical_comment) {
            cleaned.push_back(character);
        }
    }

    return cleaned;
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

std::string to_json(const MachineState& state) {
    std::ostringstream output;
    output << std::setprecision(15) << std::defaultfloat;
    output << "{\n"
           << "  \"final_position\": {\"x\": " << state.position.x << ", \"y\": " << state.position.y
           << ", \"z\": " << state.position.z << "},\n"
           << "  \"feed_rate\": " << state.feed_rate << ",\n"
           << "  \"spindle_speed\": " << state.spindle_speed << ",\n"
           << "  \"spindle_direction\": \"" << to_string(state.spindle_direction) << "\",\n"
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
           << "  \"error\": null\n"
           << "}\n";
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

}  // namespace

int main(int argc, char* argv[]) {
    try {
        const ProgramOptions options = parse_command_line(argc, argv);
        const MachineState final_state = execute_program(options.input_path);

        std::ofstream output_stream(options.output_path, std::ios::trunc);
        if (!output_stream.is_open()) {
            throw std::runtime_error("Could not open output file: " + options.output_path);
        }
        output_stream << to_json(final_state);
        return static_cast<int>(ExitCode::kSuccess);
    } catch (const InputError& error) {
        std::cerr << error.what() << '\n';
        return static_cast<int>(ExitCode::kInvalidInput);
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return static_cast<int>(ExitCode::kInternalError);
    }
}
