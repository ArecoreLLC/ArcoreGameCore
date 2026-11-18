#pragma once
#include <cmath>

namespace Arcore::Interaction
{
// Distances must use one consistent unit (Unreal consumers use centimeters).
// Invalid inputs fail closed so NaN cannot bypass a server-side range check.
inline bool WithinRange(double DistanceSquared, double Radius)
{
    return std::isfinite(DistanceSquared) && std::isfinite(Radius)
        && DistanceSquared >= 0.0 && Radius >= 0.0
        && std::sqrt(DistanceSquared) <= Radius;
}
// Signed scalar speed and nonnegative limit must use the same units.
// Reverse motion is gated by magnitude; invalid telemetry fails closed.
inline bool WithinSpeed(double Speed, double MaximumSpeed)
{
    return std::isfinite(Speed) && std::isfinite(MaximumSpeed)
        && MaximumSpeed >= 0.0 && std::abs(Speed) <= MaximumSpeed;
}
inline bool CooldownReady(double Now, double ReadyAt)
{
    return std::isfinite(Now) && std::isfinite(ReadyAt) && Now >= ReadyAt;
}
// Inclusive cone gate for an already normalized facing dot product. Coincident
// targets may pass 1.0; consumers own normalization, range and occlusion.
inline bool WithinFacing(double FacingDot, double MinimumDot)
{
    return std::isfinite(FacingDot) && std::isfinite(MinimumDot)
        && FacingDot >= -1.0 && FacingDot <= 1.0
        && MinimumDot >= -1.0 && MinimumDot <= 1.0 && FacingDot >= MinimumDot;
}
// Keep the first candidate on ties. Callers supply stable iteration order and
// filter ownership/visibility before consideration. No engine pointers retained.
struct NearestCandidate
{
    int Index = -1;
    double DistanceSquared = 0.0;
    bool Consider(int CandidateIndex, double CandidateDistanceSquared, double Radius, bool Eligible = true)
    {
        if (CandidateIndex < 0 || !Eligible || !WithinRange(CandidateDistanceSquared, Radius)) return false;
        if (Index >= 0 && CandidateDistanceSquared >= DistanceSquared) return false;
        Index = CandidateIndex;
        DistanceSquared = CandidateDistanceSquared;
        return true;
    }
};
}
