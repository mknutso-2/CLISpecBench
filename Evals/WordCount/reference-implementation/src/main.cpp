#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

static bool is_ws(char c) {
    return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\f' || c == '\v';
}

static std::string to_lower(const std::string& s) {
    std::string result;
    result.reserve(s.size());
    for (char c : s) {
        result.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));
    }
    return result;
}

int main(int argc, char* argv[]) {
    std::string input_path;
    std::string output_path;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--input" && i + 1 < argc) {
            input_path = argv[++i];
        } else if (arg == "--output" && i + 1 < argc) {
            output_path = argv[++i];
        }
    }

    if (input_path.empty() || output_path.empty()) {
        std::cerr << "Usage: wordcount --input <file> --output <file>\n";
        return 1;
    }

    // Read entire input file
    std::ifstream ifs(input_path, std::ios::binary);
    if (!ifs) {
        std::cerr << "Cannot open input file: " << input_path << "\n";
        return 1;
    }
    std::string content((std::istreambuf_iterator<char>(ifs)),
                         std::istreambuf_iterator<char>());
    ifs.close();

    // Count characters (bytes)
    int characters = static_cast<int>(content.size());

    // Count lines
    int lines = 0;
    for (char c : content) {
        if (c == '\n') {
            ++lines;
        }
    }
    // If file is non-empty and doesn't end with newline, count the last line
    if (!content.empty() && content.back() != '\n') {
        ++lines;
    }

    // Extract words and count frequencies
    std::map<std::string, int> freq;
    int words = 0;
    std::string current_word;
    for (char c : content) {
        if (is_ws(c)) {
            if (!current_word.empty()) {
                ++words;
                freq[to_lower(current_word)]++;
                current_word.clear();
            }
        } else {
            current_word.push_back(c);
        }
    }
    if (!current_word.empty()) {
        ++words;
        freq[to_lower(current_word)]++;
    }

    int unique_words = static_cast<int>(freq.size());

    // Build sorted top_words
    std::vector<std::pair<std::string, int>> sorted_words(freq.begin(), freq.end());
    std::sort(sorted_words.begin(), sorted_words.end(),
        [](const auto& a, const auto& b) {
            if (a.second != b.second) return a.second > b.second;
            return a.first < b.first;
        });

    int top_n = std::min(static_cast<int>(sorted_words.size()), 10);

    // Write JSON output
    std::ofstream ofs(output_path);
    if (!ofs) {
        std::cerr << "Cannot open output file: " << output_path << "\n";
        return 2;
    }

    ofs << "{\n";
    ofs << "  \"lines\": " << lines << ",\n";
    ofs << "  \"words\": " << words << ",\n";
    ofs << "  \"characters\": " << characters << ",\n";
    ofs << "  \"unique_words\": " << unique_words << ",\n";
    ofs << "  \"top_words\": [";
    for (int i = 0; i < top_n; ++i) {
        if (i > 0) ofs << ",";
        ofs << "\n    {\"word\": \"" << sorted_words[i].first
            << "\", \"count\": " << sorted_words[i].second << "}";
    }
    if (top_n > 0) ofs << "\n  ";
    ofs << "]\n";
    ofs << "}\n";

    return 0;
}
