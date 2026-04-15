// iges::ParamWriter — Implementation.

#include "param_writer.hpp"
#include "format.hpp"

namespace iges {

ParamWriter::ParamWriter(char param_delim, char record_delim)
    : pd_(param_delim), rd_(record_delim) {}

void ParamWriter::delimit() {
    if (need_delim_) buf_ += pd_;
    need_delim_ = true;
}

void ParamWriter::write_integer(int v) {
    delimit();
    buf_ += format_integer(v);
}

void ParamWriter::write_real(Real v) {
    delimit();
    buf_ += format_real(v);
}

void ParamWriter::write_string(std::string_view v) {
    delimit();
    buf_ += format_hollerith(v);
}

void ParamWriter::write_pointer(DEIndex idx) {
    delimit();
    buf_ += format_pointer(idx);
}

void ParamWriter::write_logical(bool v) {
    delimit();
    buf_ += format_logical(v);
}

void ParamWriter::end_record() {
    buf_ += rd_;
    need_delim_ = false;
}

} // namespace iges
