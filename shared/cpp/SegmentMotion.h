#pragma once
#include <cmath>

namespace GameCore
{
struct SegmentStep
{
    double Distance = 0;
    double Seconds = 0;
    bool Arrived = false;
};

// Consume only the time needed to reach a waypoint. The adapter retains the
// remainder, resolves arrival events, and chooses the next speed and waypoint.
inline SegmentStep AdvanceSegment(double distance, double speed, double seconds)
{
    SegmentStep result;
    if (!std::isfinite(distance) || distance < 0 || !std::isfinite(speed) ||
        speed <= 0 || !std::isfinite(seconds) || seconds < 0) return result;
    const double needed = distance / speed;
    result.Arrived = needed <= seconds;
    result.Seconds = result.Arrived ? needed : seconds;
    result.Distance = result.Arrived ? distance : speed * seconds;
    return result;
}
}
