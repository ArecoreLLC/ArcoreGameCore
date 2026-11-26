#pragma once
#include <cmath>

namespace GameCore
{
// Bounded cubic easing with zero endpoint velocity. Nonfinite input fails closed.
// Consumers own clocks, interpolation endpoints and spatial paths.
inline double SmoothStep01(double progress)
{
    if (!std::isfinite(progress) || progress <= 0.0) return 0.0;
    if (progress >= 1.0) return 1.0;
    return progress * progress * (3.0 - 2.0 * progress);
}

// Finite one-shot timeline. Advance returns true only on the completion edge.
// Idle/reset starts at zero; completed stays at one until explicitly restarted.
class FiniteTransition
{
public:
    explicit FiniteTransition(double duration = 1.0)
        : Duration(std::isfinite(duration) && duration > 0.0 ? duration : 1.0) {}
    void Start() { Elapsed = 0.0; Active = true; }
    void Reset() { Elapsed = 0.0; Active = false; }
    bool Advance(double seconds)
    {
        if (!Active || !std::isfinite(seconds) || seconds <= 0.0) return false;
        if (seconds >= Duration - Elapsed)
        {
            Elapsed = Duration; Active = false; return true;
        }
        Elapsed += seconds;
        return false;
    }
    bool IsActive() const { return Active; }
    double Progress() const { return Elapsed / Duration; }
    double Value() const { return SmoothStep01(Progress()); }
private:
    double Duration;
    double Elapsed = 0.0;
    bool Active = false;
};

// Exact exponential response for a stationary target. Apply to scalar or vector
// lerp in the engine adapter; zero/invalid time never advances presentation.
inline double ResponseAlpha(double seconds, double halfLife)
{
    if (!std::isfinite(seconds) || seconds <= 0.0 ||
        !std::isfinite(halfLife) || halfLife <= 0.0) return 0.0;
    return -std::expm1(-0.6931471805599453 * seconds / halfLife);
}

// Retriggerable, bounded one-shot feedback. Clock ownership (pause, slow motion)
// stays with the consumer. Invalid input is a no-op; no overshoot or backlog.
class FeedbackPulse
{
public:
    explicit FeedbackPulse(double duration = 0.6)
        : Duration(std::isfinite(duration) && duration > 0.0 ? duration : 0.6) {}
    // Nonpositive/invalid strength is a no-op; oversized events saturate.
    void Trigger(double strength = 1.0)
    {
        if (!std::isfinite(strength) || strength <= 0.0) return;
        Strength = strength > 1.0 ? 1.0 : strength;
        Remaining = Duration;
    }
    // Preserve the currently visible peak when clustered events retrigger.
    void TriggerPeak(double strength = 1.0)
    {
        if (!std::isfinite(strength) || strength <= 0.0) return;
        Trigger(strength > Value() ? strength : Value());
    }
    void Reset() { Remaining = 0.0; }
    void Advance(double seconds)
    {
        if (!std::isfinite(seconds) || seconds <= 0.0) return;
        Remaining = seconds >= Remaining ? 0.0 : Remaining - seconds;
    }
    // Linear phase for expanding rings and timelines; idle/expired returns 1.
    bool IsActive() const { return Remaining > 0.0; }
    double Progress() const { return 1.0 - Remaining / Duration; }
    double Value() const
    {
        const double t = Remaining / Duration;
        return Strength * t * t * (3.0 - 2.0 * t);
    }
private:
    double Duration;
    double Remaining = 0.0;
    double Strength = 1.0;
};
}
