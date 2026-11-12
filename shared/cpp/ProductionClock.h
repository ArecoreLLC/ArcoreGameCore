#pragma once
#include <cmath>

namespace GameCore
{
// Engine-neutral recipe clock. One tick can finish at most one recipe; elapsed
// time beyond completion is intentionally discarded, never banked while blocked.
class ProductionClock
{
public:
    explicit ProductionClock(double duration = 4.0)
        : Duration(std::isfinite(duration) && duration > 0.0 ? duration : 4.0) {}
    bool Advance(double seconds, bool canWork)
    {
        if (!canWork || !std::isfinite(seconds) || seconds <= 0.0) return false;
        Elapsed += seconds;
        if (Elapsed < Duration) return false;
        Elapsed = 0.0;
        return true;
    }
    double Fraction() const { return Elapsed / Duration; }
    // Restore only an unfinished recipe. Reject invalid data without mutation.
    bool RestoreFraction(double fraction)
    {
        if (!std::isfinite(fraction) || fraction < 0.0 || fraction >= 1.0) return false;
        const double restored = fraction * Duration;
        if (restored >= Duration) return false;
        Elapsed = restored;
        return true;
    }
    void Reset() { Elapsed = 0.0; }
private:
    double Duration;
    double Elapsed = 0.0;
};
}
