#pragma once
#include <cmath>
#include <limits>

namespace GameCore
{
// Absolute caller-clock deadlines: peers may sample one replicated deadline.
struct DeadlineCountdown
{
    static bool HasElapsed(double deadline, double now)
    {
        return std::isfinite(deadline) && std::isfinite(now) && now >= deadline;
    }
    static int SecondsLeft(double deadline, double now)
    {
        if (!std::isfinite(deadline) || !std::isfinite(now) || now >= deadline) return 0;
        const double seconds = std::ceil(deadline - now);
        const int maximum = std::numeric_limits<int>::max();
        return seconds >= maximum ? maximum : static_cast<int>(seconds);
    }
};
}
