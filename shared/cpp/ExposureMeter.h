#pragma once
#include <algorithm>
#include <cmath>
namespace Arcore { namespace Stealth {
// Engine-neutral detection accumulation. Terminal capture is owned by the game.
class ExposureMeter
{
    double Amount = 0;
public:
    double Value() const { return Amount; }
    bool Full() const { return Amount >= 1.0; }
    void Reset() { Amount = 0; }
    bool Step(bool visible, double seconds, double detectionSeconds, double recoverySeconds)
    {
        if (!std::isfinite(seconds) || seconds < 0 ||
            !std::isfinite(detectionSeconds) || detectionSeconds <= 0 ||
            !std::isfinite(recoverySeconds) || recoverySeconds <= 0) return false;
        const double change = seconds / (visible ? detectionSeconds : recoverySeconds);
        Amount = visible ? std::min(1.0, Amount + change) : std::max(0.0, Amount - change);
        return true;
    }
};
}}
