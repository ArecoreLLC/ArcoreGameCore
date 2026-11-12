#pragma once
#include <cmath>

namespace ArcoreGameCore
{
enum class PulseResult { Invalid, WrongTone, CoolingDown, Accepted, Completed, AlreadyComplete };

// Engine-neutral, deterministic charge rule. Time is monotonic seconds supplied by the caller.
// Rejected commands never consume cooldown or progress. Reset starts a fresh attempt.
class ResonanceRule
{
public:
    ResonanceRule(int tone = 0, int required = 3, double cooldown = 0.4)
        : Tone(tone), Required(required > 0 ? required : 1), Cooldown(std::isfinite(cooldown) && cooldown > 0 ? cooldown : 0) {}
    PulseResult Apply(int tone, double now)
    {
        if (tone < 0 || !std::isfinite(now) || now < 0) return PulseResult::Invalid;
        if (Complete()) return PulseResult::AlreadyComplete;
        if (tone != Tone) return PulseResult::WrongTone;
        if (HasPulse && (now < LastPulse || now - LastPulse < Cooldown)) return PulseResult::CoolingDown;
        LastPulse = now;
        HasPulse = true;
        ++Count;
        return Complete() ? PulseResult::Completed : PulseResult::Accepted;
    }
    void Reset() { Count = 0; LastPulse = 0; HasPulse = false; }
    int Progress() const { return Count; }
    int RequiredPulses() const { return Required; }
    // Non-mutating presentation query, using the same clock as Apply.
    // Invalid clocks and rollback are never presented as ready.
    double ReadyFraction(double now) const
    {
        if (!std::isfinite(now) || now < 0 || (HasPulse && now < LastPulse)) return 0;
        if (Complete()) return 0;
        if (!HasPulse || Cooldown == 0) return 1;
        const double elapsed = now - LastPulse;
        return elapsed >= Cooldown ? 1 : elapsed / Cooldown;
    }
    bool Complete() const { return Count >= Required; }
private:
    int Tone, Required, Count = 0;
    double Cooldown, LastPulse = 0;
    bool HasPulse = false;
};
}
