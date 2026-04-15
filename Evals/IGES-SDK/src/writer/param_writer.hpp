#pragma once
// iges::ParamWriter — Builds free-format parameter data strings.
//
// The inverse of ParamTokenizer: accumulates typed fields into a
// comma-separated, semicolon-terminated PD string.

#include "../types.hpp"
#include <string>

namespace iges {

class ParamWriter {
public:
    explicit ParamWriter(char param_delim = ',', char record_delim = ';');

    void write_integer(int v);
    void write_real(Real v);
    void write_string(std::string_view v);
    void write_pointer(DEIndex idx);
    void write_logical(bool v);

    // Terminate the current record with the record delimiter.
    void end_record();

    // Get the accumulated string.
    std::string const& str() const { return buf_; }

private:
    std::string buf_;
    char pd_;
    char rd_;
    bool need_delim_ = false;

    void delimit();
};

} // namespace iges
