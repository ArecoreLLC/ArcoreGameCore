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
inline bool CooldownReady(double Now, double ReadyAt)
{
    return std::isfinite(Now) && std::isfinite(ReadyAt) && Now >= ReadyAt;
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
