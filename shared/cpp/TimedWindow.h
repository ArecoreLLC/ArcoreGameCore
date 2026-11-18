#pragma once
#include <algorithm>
#include <cmath>

namespace GameCore
{
// Caller-clocked, one-shot opportunity. Starts closed; expiry is exclusive.
class TimedWindow
{
public:
    explicit TimedWindow(double duration)
        : Duration(std::isfinite(duration) && duration > 0 ? duration : 0) {}
    void Refresh() { Remaining = Duration; }
    void Advance(double elapsed)
    {
        if (std::isfinite(elapsed) && elapsed > 0)
            Remaining = std::max(0.0, Remaining - elapsed);
    }
    bool IsOpen() const { return Remaining > 0; }
    bool Consume()
    {
        const bool open = IsOpen();
        Reset();
        return open;
    }
    // Failed eligibility preserves a pending request. Consume only on admission.
    bool TryConsume(bool eligible) { return eligible && Consume(); }
    void Reset() { Remaining = 0; }
private:
    double Duration;
    double Remaining = 0;
};
}
