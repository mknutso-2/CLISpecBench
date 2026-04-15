// iges::Entity — Matrix math implementations.

#include "entity.hpp"

namespace iges {

Real determinant(Matrix3x3 const& m) {
    return m(0,0) * (m(1,1)*m(2,2) - m(1,2)*m(2,1))
         - m(0,1) * (m(1,0)*m(2,2) - m(1,2)*m(2,0))
         + m(0,2) * (m(1,0)*m(2,1) - m(1,1)*m(2,0));
}

Matrix3x3 multiply(Matrix3x3 const& a, Matrix3x3 const& b) {
    Matrix3x3 r;
    for (int i = 0; i < 3; ++i)
        for (int j = 0; j < 3; ++j) {
            r(i,j) = 0;
            for (int k = 0; k < 3; ++k)
                r(i,j) += a(i,k) * b(k,j);
        }
    return r;
}

Matrix3x3 transpose(Matrix3x3 const& m) {
    Matrix3x3 r;
    for (int i = 0; i < 3; ++i)
        for (int j = 0; j < 3; ++j)
            r(i,j) = m(j,i);
    return r;
}

} // namespace iges
