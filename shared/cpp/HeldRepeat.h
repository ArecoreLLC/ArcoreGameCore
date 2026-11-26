#pragma once
#include <cmath>

namespace GameCore
{
// Input lifecycle only. The caller owns action eligibility and target identity.
class HeldRepeat
{
public:
    explicit HeldRepeat(double delay = .4, double interval = .18)
        : Delay(std::isfinite(delay) && delay > 0 ? delay : .4),
          Interval(std::isfinite(interval) && interval > 0 ? interval : .18) {}
    bool Press()
    {
        if (Held) return false;
        Held = true; Remaining = Delay; return true;
    }
    void Release() { Held = false; Remaining = 0; }
    bool Advance(double seconds)
    {
        if (!Held || !std::isfinite(seconds) || seconds <= 0) return false;
        if (seconds < Remaining) { Remaining -= seconds; return false; }
        // Never replay an accumulated burst after a stall.
        Remaining = Interval; return true;
    }
private:
    double Delay, Interval, Remaining = 0;
    bool Held = false;
};
}
