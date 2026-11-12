#pragma once
#include <cmath>

namespace GameCore
{
// SI units. Engine adapters own transforms, water sampling and integration.
struct MassProperties
{
    double Mass = 0.0, XMoment = 0.0, YMoment = 0.0;
    bool Add(double kg, double x, double y)
    {
        if (!std::isfinite(kg) || !std::isfinite(x) || !std::isfinite(y) || kg <= 0.0)
            return false;
        const double m = Mass + kg, mx = XMoment + kg * x, my = YMoment + kg * y;
        if (!std::isfinite(m) || !std::isfinite(mx) || !std::isfinite(my)) return false;
        Mass = m; XMoment = mx; YMoment = my;
        return true;
    }
    double X() const { return Mass > 0.0 ? XMoment / Mass : 0.0; }
    double Y() const { return Mass > 0.0 ? YMoment / Mass : 0.0; }
};

// Unilateral, capped spring/damper: an immersed sample pushes upward only.
// Velocity is sample vertical velocity relative to the water (m/s).
inline double BuoyantForce(double depth, double relativeVelocity,
    double stiffness, double damping, double maximum)
{
    if (!std::isfinite(depth) || !std::isfinite(relativeVelocity) ||
        !std::isfinite(stiffness) || !std::isfinite(damping) || !std::isfinite(maximum) ||
        depth <= 0.0 || stiffness <= 0.0 || damping < 0.0 || maximum <= 0.0) return 0.0;
    const double force = depth * stiffness - relativeVelocity * damping;
    return force < 0.0 ? 0.0 : (force > maximum ? maximum : force);
}
}
