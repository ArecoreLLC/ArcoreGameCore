#pragma once
#include <cmath>

namespace GameCore
{
// Caller owns the serializable remainder and the simulation callback. Excess
// wall time is discarded, never banked. Invalid inputs leave state untouched.
// Configuration bounds work to at most 1024 callbacks per invocation.
template<class Step>
int AdvanceFixedSteps(double seconds, double quantum, int maxSteps,
                      double& remainder, Step step)
{
    if (!std::isfinite(seconds) || seconds <= 0 ||
        !std::isfinite(quantum) || quantum <= 0 || maxSteps < 1 || maxSteps > 1024 ||
        !std::isfinite(remainder) || remainder < 0 || remainder >= quantum ||
        !std::isfinite(quantum * maxSteps)) return 0;
    const double cap = quantum * maxSteps;
    // Work in units of steps to avoid overflow when adding large durations.
    double units = remainder / quantum + (seconds >= cap ? maxSteps : seconds / quantum);
    const double tolerance = 1e-10;
    int count = static_cast<int>(std::floor(units + tolerance));
    if (count > maxSteps) count = maxSteps;
    units -= count;
    remainder = units <= 0 ? 0 : units * quantum;
    // Adding a near-full remainder to an integer cap can round up to the
    // next integer. Preserve the strict remainder invariant in that case.
    if (remainder >= quantum) remainder = std::nextafter(quantum, 0.0);
    for (int i = 0; i < count; ++i) step(quantum);
    return count;
}
}
