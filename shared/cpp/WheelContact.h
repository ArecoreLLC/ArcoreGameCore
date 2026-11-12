#pragma once
#include <algorithm>
#include <cmath>

namespace gamecore {
// SI units throughout: metres, seconds, newtons. Compression velocity is positive
// when the suspension shortens. Unilateral contact never pulls the wheel down.
inline double SuspensionForce(double compression, double compressionVelocity,
                              double stiffness, double damping, double maxForce) {
    if (!std::isfinite(compression) || !std::isfinite(compressionVelocity) ||
        !std::isfinite(stiffness) || !std::isfinite(damping) || !std::isfinite(maxForce) ||
        compression <= 0 || stiffness < 0 || damping < 0 || maxForce <= 0) return 0;
    const double force = stiffness * compression + damping * compressionVelocity;
    if (!std::isfinite(force)) return 0;
    return std::max(0.0, std::min(maxForce, force));
}
struct TireForce { double longitudinal = 0; double lateral = 0; };
// Combined drive/braking/cornering shares one Coulomb friction circle.
inline TireForce LimitTireForce(double longitudinal, double lateral, double normalLoad, double friction) {
    if (!std::isfinite(longitudinal) || !std::isfinite(lateral) ||
        !std::isfinite(normalLoad) || !std::isfinite(friction) || normalLoad <= 0 || friction <= 0) return {};
    const double budget = normalLoad * friction;
    const double magnitude = std::hypot(longitudinal, lateral);
    if (!std::isfinite(budget) || !std::isfinite(magnitude)) return {};
    const double scale = magnitude > budget ? budget / magnitude : 1.0;
    return {longitudinal * scale, lateral * scale};
}
}
