#pragma once
#include <cmath>

namespace ArcoreGameCore
{
// Poll with a monotonic clock. Emits once on press, then at most once per poll.
// Consumers still validate range, resources and ability cooldowns.
class HoldRepeat
{
public:
    explicit HoldRepeat(double interval = 0.5)
        : Interval(std::isfinite(interval) && interval > 0 ? interval : 0.5) {}

    bool Update(bool held, double now)
    {
        if (!held) { Active = false; Blocked = false; return false; }
        if (Blocked || !std::isfinite(now) || now < 0) return false;
        if (Active && (now < Last || now - Last < Interval)) return false;
        Active = true;
        Last = now;
        return true;
    }
    // Restart, respawn and context transitions require a fresh release/press.
    void CancelUntilRelease() { Active = false; Blocked = true; }
    bool IsActive() const { return Active; }
private:
    double Interval, Last = 0;
    bool Active = false, Blocked = false;
};
}
