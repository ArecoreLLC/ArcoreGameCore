#pragma once
#include <cmath>

namespace Arcore { namespace Light {
struct Vector { double x, y, z; };
inline bool Normalize(Vector value, Vector& result)
{
    const double length = std::hypot(std::hypot(value.x, value.y), value.z);
    if (!std::isfinite(length) || length < 1e-9) return false;
    result = {value.x / length, value.y / length, value.z / length};
    return true;
}
// Accepts either normal orientation. Invalid input leaves output unchanged.
inline bool Reflect(Vector incident, Vector normal, Vector& result)
{
    Vector d, n;
    if (!Normalize(incident, d) || !Normalize(normal, n)) return false;
    const double dot = d.x*n.x + d.y*n.y + d.z*n.z;
    result = {d.x - 2*dot*n.x, d.y - 2*dot*n.y, d.z - 2*dot*n.z};
    return true;
}
}}
