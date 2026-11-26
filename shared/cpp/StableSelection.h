#pragma once
#include <cmath>
#include <cstddef>

namespace GameCore
{
// Caller filters eligibility before offering candidates. Higher scores win.
// A fresh pass never keeps a missing target. Ties use the lowest identifier.
class StableSelection
{
public:
    struct Candidate { int Id; double Score; };
    int Select(const Candidate* candidates, std::size_t count, double margin)
    {
        int best = -1;
        double bestScore = 0, currentScore = 0;
        bool currentFound = false;
        if (!std::isfinite(margin) || margin < 0) margin = 0;
        if (candidates) for (std::size_t i = 0; i < count; ++i)
        {
            const auto& c = candidates[i];
            if (c.Id < 0 || !std::isfinite(c.Score)) continue;
            if (best < 0 || c.Score > bestScore || (c.Score == bestScore && c.Id < best))
            { best = c.Id; bestScore = c.Score; }
            if (c.Id == Current && (!currentFound || c.Score > currentScore))
            { currentFound = true; currentScore = c.Score; }
        }
        if (currentFound && bestScore - currentScore <= margin) return Current;
        return Current = best;
    }
    void Reset() { Current = -1; }
    int Get() const { return Current; }
private:
    int Current = -1;
};
}
