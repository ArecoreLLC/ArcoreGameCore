#pragma once
#include <cmath>

namespace GameCore
{
enum class CaptureState { Locked, Ready, Capturing, Complete };

// Continuous uncontested occupancy. The engine owns eligibility and presence.
class CaptureObjective
{
public:
    bool Configure(double HoldSeconds)
    {
        if (!std::isfinite(HoldSeconds) || HoldSeconds <= 0) return false;
        Duration = HoldSeconds;
        Reset();
        return true;
    }
    void Reset() { State = CaptureState::Locked; Elapsed = 0; }
    void Update(bool Unlocked, bool Occupied, double Seconds)
    {
        if (!std::isfinite(Seconds) || Seconds < 0 || State == CaptureState::Complete) return;
        if (!Unlocked) { Reset(); return; }
        if (!Occupied) { Elapsed = 0; State = CaptureState::Ready; return; }
        State = CaptureState::Capturing;
        // Compare before addition to avoid overflow for very large finite steps.
        if (Seconds >= Duration - Elapsed) { Elapsed = Duration; State = CaptureState::Complete; }
        else Elapsed += Seconds;
    }
    CaptureState GetState() const { return State; }
    double GetProgress() const { return Elapsed / Duration; }
private:
    double Duration = 3;
    double Elapsed = 0;
    CaptureState State = CaptureState::Locked;
};
}
