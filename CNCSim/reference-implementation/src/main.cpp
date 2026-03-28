#include <cctype>
#include <fstream>
#include <iomanip>
#include <iostream>
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

struct MachineState {
    Position position{};
    double feed_rate = 0.0;
    double spindle_speed = 0.0;
    SpindleDirection spindle_direction = SpindleDirection::kOff;
    std::string motion_mode = "G0";
    CoordinateMode coordinate_mode = CoordinateMode::kAbsolute;
};

struct ProgramOptions {
    std::string input_path;
    std::string output_path;
};

struct ParsedLine {
    std::optional<std::string> motion_mode;
    std::optional<CoordinateMode> coordinate_mode;
    std::optional<double> x;
    std::optional<double> y;
    std::optional<double> z;
    std::optional<double> feed_rate;
    std::optional<double> spindle_speed;
    std::optional<SpindleDirection> spindle_direction;
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
void reset_after_program_end(MachineState& state);
std::string strip_comments(std::string_view raw_line);
std::vector<std::string> split_words(std::string_view line);
double parse_numeric_suffix(const std::string& word);
std::string to_json(const MachineState& state);
std::string to_string(CoordinateMode mode);
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
            case 'F':
                parsed_line.feed_rate = parse_numeric_suffix(word);
                break;
            case 'G': {
                const double code = parse_numeric_suffix(word);
                if (code == 0.0 || code == 1.0) {
                    if (parsed_line.motion_mode.has_value()) {
                        throw InputError("Multiple motion G codes in the same block");
                    }
                    parsed_line.motion_mode = code == 0.0 ? "G0" : "G1";
                    break;
                }
                if (code == 90.0 || code == 91.0) {
                    if (parsed_line.coordinate_mode.has_value()) {
                        throw InputError("Multiple coordinate mode G codes in the same block");
                    }
                    parsed_line.coordinate_mode =
                        code == 90.0 ? CoordinateMode::kAbsolute : CoordinateMode::kIncremental;
                    break;
                }

                throw InputError("Unsupported G code: " + word);
            }
            case 'M': {
                const double code = parse_numeric_suffix(word);
                if (code == 2.0 || code == 30.0) {
                    parsed_line.end_program = true;
                    break;
                }
                if (code == 3.0) {
                    parsed_line.spindle_direction = SpindleDirection::kClockwise;
                    break;
                }
                if (code == 4.0) {
                    parsed_line.spindle_direction = SpindleDirection::kCounterClockwise;
                    break;
                }
                if (code == 5.0) {
                    parsed_line.spindle_direction = SpindleDirection::kOff;
                    break;
                }

                throw InputError("Unsupported M code: " + word);
            }
            case 'N':
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

    return parsed_line;
}

void apply_line(const ParsedLine& parsed_line, MachineState& state) {
    if (parsed_line.coordinate_mode.has_value()) {
        state.coordinate_mode = *parsed_line.coordinate_mode;
    }
    if (parsed_line.motion_mode.has_value()) {
        state.motion_mode = *parsed_line.motion_mode;
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

    apply_axis_value(parsed_line.x, state.position.x, state.coordinate_mode);
    apply_axis_value(parsed_line.y, state.position.y, state.coordinate_mode);
    apply_axis_value(parsed_line.z, state.position.z, state.coordinate_mode);

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

void reset_after_program_end(MachineState& state) {
    state.coordinate_mode = CoordinateMode::kAbsolute;
    state.motion_mode = "G1";
    state.spindle_direction = SpindleDirection::kOff;
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
           << "  \"active_modal_codes\": {\"1\": \"" << state.motion_mode << "\", \"3\": \""
           << to_string(state.coordinate_mode) << "\"},\n"
           << "  \"error\": null\n"
           << "}\n";
    return output.str();
}

std::string to_string(CoordinateMode mode) {
    return mode == CoordinateMode::kAbsolute ? "G90" : "G91";
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
