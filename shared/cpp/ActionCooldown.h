#pragma once
#include <cmath>

namespace GameCore
{
// Caller-clocked action admission. Repeated presses cannot bypass recovery;
// a hitch admits one action, never a backlog. Pause/authority belong to caller.
class ActionCooldown
{
public:
    explicit ActionCooldown(double interval = .25)
        : Interval(std::isfinite(interval) && interval > 0 ? interval : .25) {}
    bool TryConsume(double now)
    {
        if (!std::isfinite(now) || now < 0 || (Used && now - Last < Interval)) return false;
        Last = now; Used = true; return true;
    }
    double ReadyFraction(double now) const
    {
        if (!std::isfinite(now) || now < 0) return 0;
        if (!Used) return 1;
        const double elapsed = now - Last;
        return elapsed <= 0 ? 0 : elapsed >= Interval ? 1 : elapsed / Interval;
    }
    void Reset() { Used = false; Last = 0; }
private:
    double Interval, Last = 0;
    bool Used = false;
};
}
