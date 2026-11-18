#pragma once
#include <algorithm>
#include <cmath>

namespace GameCore
{
// Nonnegative rate with exact distance integration while accelerating toward a
// constant target. Consumers own collision, units and changes of destination.
class RateRamp
{
public:
    explicit RateRamp(double rate = 0) { Reset(rate); }
    void Reset(double rate = 0) { Rate = std::isfinite(rate) && rate >= 0 ? rate : 0; }
    double Value() const { return Rate; }
    double Advance(double seconds, double target, double acceleration)
    {
        if (!std::isfinite(seconds) || seconds <= 0 || !std::isfinite(target) || target < 0 ||
            !std::isfinite(acceleration) || acceleration <= 0) return 0;
        const double difference = target - Rate;
        const double rampTime = std::min(seconds, std::abs(difference) / acceleration);
        const double next = rampTime == seconds
            ? Rate + std::copysign(acceleration * rampTime, difference) : target;
        const double distance = (Rate * .5 + next * .5) * rampTime + target * (seconds - rampTime);
        // Fail closed on unrepresentable integration, preserving the previous rate.
        if (!std::isfinite(distance) || !std::isfinite(next)) return 0;
        Rate = next;
        return distance;
    }
private:
    double Rate = 0;
};

// Signed counterpart for vehicles, scrolling and reversible machinery. Existing
// nonnegative RateRamp semantics stay unchanged. Travel can cross zero.
class SignedRateRamp
{
public:
    explicit SignedRateRamp(double rate = 0) { Reset(rate); }
    void Reset(double rate = 0) { Rate = std::isfinite(rate) ? rate : 0; }
    double Value() const { return Rate; }
    double Advance(double seconds, double target, double acceleration)
    {
        if (!std::isfinite(seconds) || seconds <= 0 || !std::isfinite(target) ||
            !std::isfinite(acceleration) || acceleration <= 0) return 0;
        const double difference = target - Rate;
        if (!std::isfinite(difference)) return 0;
        const double rampTime = std::min(seconds, std::abs(difference) / acceleration);
        const double next = rampTime == seconds
            ? Rate + std::copysign(acceleration * rampTime, difference) : target;
        const double distance = (Rate * .5 + next * .5) * rampTime + target * (seconds - rampTime);
        if (!std::isfinite(distance) || !std::isfinite(next)) return 0;
        Rate = next;
        return distance;
    }
private:
    double Rate = 0;
};
}
