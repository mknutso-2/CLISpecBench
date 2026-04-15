#pragma once
// iges::ConnectPointEntity — Type 132.
//
// §4.26: "A Connect Point Entity specifies the location of a
//   connection point and its attributes."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>
#include <string>

namespace iges {

struct ConnectPointEntity {
    Vec3 location;                      // 1-3: X, Y, Z
    DEIndex display_symbol;             // 4: PTR — display symbol geometry DE
    int tf = 0;                         // 5: TF — Type flag
    int ff = 0;                         // 6: FF — Function flag (0/1/2)
    std::string cid;                    // 7: CID — Function identifier
    DEIndex pttcid;                     // 8: PTTCID — Text Display Template for CID
    std::string cfn;                    // 9: CFN — Connection Point Function Name
    DEIndex pttcfn;                     // 10: PTTCFN — Text Display Template for CFN
    int cpid = 0;                       // 11: CPID — Unique Connect Point Identifier
    int fc = 0;                         // 12: FC — Connect Point Function Code
    int sf = 0;                         // 13: SF — Swap Flag (0=may swap, 1=may not)
    DEIndex psfi;                       // 14: PSFI — Pointer to owner
};

std::expected<ConnectPointEntity, Diagnostic>
parse_connect_point_entity(ParamTokenizer& tok);

} // namespace iges
