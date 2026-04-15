#pragma once
// iges::write_global_section — Serializes a GlobalSection to a
// free-format string suitable for the IGES Global section.

#include "../model/global_section.hpp"
#include <string>

namespace iges {

// Serialize the 26 global fields to a free-format parameter string.
// The result is one long string with Hollerith-encoded strings,
// comma delimiters, and a terminating semicolon.
std::string write_global_section(GlobalSection const& g);

} // namespace iges
