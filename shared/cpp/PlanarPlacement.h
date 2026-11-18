#pragma once
#include <cmath>

namespace Arcore::Rules
{
struct PlacementPoint { double X = 0; double Y = 0; };

// Bounded deterministic search. The caller owns legality/occupancy and commits
// a reservation only after success. Failure never changes the output.
template<class Accept>
bool FindPlanarPlacement(PlacementPoint Preferred, double Step, int Rings,
                         int Samples, Accept IsFree, PlacementPoint& Result)
{
    auto Finite = [](PlacementPoint P) { return std::isfinite(P.X) && std::isfinite(P.Y); };
    if (!Finite(Preferred) || !std::isfinite(Step) || Step <= 0 ||
        Rings < 0 || Rings > 64 || Samples < 1 || Samples > 256) return false;
    if (IsFree(Preferred)) { Result = Preferred; return true; }
    constexpr double Tau = 6.28318530717958647692;
    for (int Ring = 1; Ring <= Rings; ++Ring)
        for (int I = 0; I < Samples; ++I)
        {
            const double Angle = Tau * I / Samples;
            PlacementPoint Candidate{Preferred.X + std::cos(Angle) * Step * Ring,
                                     Preferred.Y + std::sin(Angle) * Step * Ring};
            if (Finite(Candidate) && IsFree(Candidate)) { Result = Candidate; return true; }
        }
    return false;
}
}
