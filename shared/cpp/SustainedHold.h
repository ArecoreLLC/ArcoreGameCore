#pragma once
#include <cmath>

namespace GameCore
{
// Continuous eligibility is required. Completion emits once until reset;
// interruptions discard progress. The consumer owns authority and eligibility.
class SustainedHold
{
public:
    explicit SustainedHold(double duration) : Duration(duration) {}
    bool Advance(double seconds, bool eligible)
    {
        if (!eligible || !std::isfinite(Duration) || Duration <= 0.0
            || !std::isfinite(seconds) || seconds < 0.0)
        { Reset(); return false; }
        if (Elapsed >= Duration) return false;
        // Compare before adding to avoid overflow with large finite deltas.
        if (seconds >= Duration - Elapsed)
        { Elapsed = Duration; return true; }
        Elapsed += seconds;
        return false;
    }
    double Fraction() const
    { return std::isfinite(Duration) && Duration > 0.0 ? Elapsed / Duration : 0.0; }
    void Reset() { Elapsed = 0.0; }
private:
    double Duration;
    double Elapsed = 0.0;
};
}
