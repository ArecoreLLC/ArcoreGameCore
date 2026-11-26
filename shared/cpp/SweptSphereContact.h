#pragma once
#include <algorithm>
#include <array>
#include <cmath>

namespace GameCore
{
// Relative motion of two centers against their combined radius. Endpoints and
// tangencies are inclusive. Callers split curved motion and exclude teleports.
inline bool SweptSphereContact(const std::array<double, 3>& from,
    const std::array<double, 3>& to, double radius)
{
    if (!std::isfinite(radius) || radius < 0) return false;
    double scale = radius;
    for (int i = 0; i < 3; ++i) {
        if (!std::isfinite(from[i]) || !std::isfinite(to[i])) return false;
        scale = std::max({scale, std::abs(from[i]), std::abs(to[i])});
    }
    if (scale == 0) return true;
    // Normalize before subtracting or squaring to avoid finite-input overflow.
    std::array<double, 3> a{}, d{};
    double length2 = 0, dot = 0;
    for (int i = 0; i < 3; ++i) {
        a[i] = from[i] / scale;
        d[i] = to[i] / scale - a[i];
        length2 += d[i] * d[i]; dot += a[i] * d[i];
    }
    const double t = length2 > 0 ? std::clamp(-dot / length2, 0.0, 1.0) : 0;
    double distance2 = 0;
    for (int i = 0; i < 3; ++i) {
        const double v = a[i] + t * d[i]; distance2 += v * v;
    }
    const double r = radius / scale;
    return distance2 <= r * r;
}
}
