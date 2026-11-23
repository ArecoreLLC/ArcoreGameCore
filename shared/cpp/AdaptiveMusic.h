#pragma once
#include <algorithm>
#include <cmath>
#include <limits>
#include <string>
#include <utility>
#include <vector>

namespace GameCore
{
enum class MusicBoundary { Immediate, Beat, Bar, Phrase };

// Sonic Alchemist arcore-adaptive-v1 score: aligned looping layers, named states with
// per-layer gains in dB and one quantized transition rule. A layer gain at or below
// -60 dB is silent, matching a disabled layer in design.json.
struct AdaptiveScore
{
    double bpm = 120;
    int beatsPerBar = 4;
    int loopBars = 1;
    double fadeBeats = 0.25;
    MusicBoundary boundary = MusicBoundary::Bar;
    float masterDb = 0;
    std::vector<std::string> layerNames;
    std::vector<std::string> stateNames;
    std::vector<std::vector<float>> stateGainDb; // [state][layer]

    int Layers() const { return static_cast<int>(layerNames.size()); }
    int States() const { return static_cast<int>(stateNames.size()); }
    // Same limits as Sonic Alchemist's Design::validate.
    bool Valid() const
    {
        if (!std::isfinite(bpm) || bpm < 30 || bpm > 300 || beatsPerBar < 1 || beatsPerBar > 12 ||
            loopBars < 1 || loopBars > 32 || !std::isfinite(fadeBeats) || fadeBeats < 0 || fadeBeats > 4 ||
            !std::isfinite(masterDb) || masterDb < -60 || masterDb > 6 || layerNames.empty() ||
            layerNames.size() > 64 || stateNames.empty() || stateNames.size() > 16 ||
            stateGainDb.size() != stateNames.size()) return false;
        for (const auto& levels : stateGainDb)
        {
            if (levels.size() != layerNames.size()) return false;
            for (float db : levels) if (!std::isfinite(db) || db < -60 || db > 12) return false;
        }
        return true;
    }
    double BeatSeconds() const { return 60.0 / bpm; }
    double BarSeconds() const { return BeatSeconds() * beatsPerBar; }
    double LoopSeconds() const { return BarSeconds() * loopBars; }
    double FadeSeconds() const { return BeatSeconds() * fadeBeats; }
    double BoundarySeconds() const
    {
        switch (boundary)
        {
        case MusicBoundary::Immediate: return 0;
        case MusicBoundary::Beat: return BeatSeconds();
        case MusicBoundary::Phrase: return LoopSeconds();
        default: return BarSeconds();
        }
    }
    // Linear runtime gain with the master included; 0 for silent layers or bad indices.
    float TargetGain(int state, int layer) const
    {
        if (state < 0 || state >= States() || layer < 0 || layer >= Layers()) return 0;
        const float db = stateGainDb[state][layer];
        return db <= -60 ? 0.f : static_cast<float>(std::pow(10.0, (db + masterDb) / 20.0));
    }
    int StateIndex(const std::string& name) const
    {
        const auto found = std::find(stateNames.begin(), stateNames.end(), name);
        return found == stateNames.end() ? -1 : static_cast<int>(found - stateNames.begin());
    }
};

// Quantized layer mixer. A requested state waits for the next boundary of the music
// clock, then rising layers follow sin and falling layers cos over the fade (equal power,
// as Sonic Alchemist auditions it). Callers own the clock source, audio voices and state
// choice. Desired state -1 holds the current state. An invalid score keeps every layer silent.
class AdaptiveMixer
{
public:
    explicit AdaptiveMixer(AdaptiveScore score = AdaptiveScore(), int state = 0)
        : Score(std::move(score)), Ok(Score.Valid())
    {
        Reset(state);
    }
    void Reset(int state = 0, double musicSeconds = 0)
    {
        Current = Ok ? std::max(0, std::min(state, Score.States() - 1)) : 0;
        Clock = std::isfinite(musicSeconds) && musicSeconds > 0 ? musicSeconds : 0;
        FadeElapsed = std::numeric_limits<double>::infinity();
        From.assign(Ok ? Score.Layers() : 0, 0.f);
        for (int layer = 0; layer < static_cast<int>(From.size()); ++layer) From[layer] = Score.TargetGain(Current, layer);
        Now = From;
    }
    // Free-running clock, for tests or when no audio clock exists.
    void Advance(double seconds, int desired)
    {
        if (std::isfinite(seconds) && seconds >= 0) AdvanceTo(Clock + seconds, desired);
    }
    // Follow an audio clock: seconds since the layers started. Earlier times resynchronize
    // the clock without a transition (for example after the transport was reset).
    void AdvanceTo(double musicSeconds, int desired)
    {
        if (!Ok || !std::isfinite(musicSeconds)) return;
        if (musicSeconds < Clock) { Clock = musicSeconds; return; }
        const double delta = musicSeconds - Clock, period = Score.BoundarySeconds();
        bool boundary = true;
        double sinceBoundary = 0;
        if (period > 0)
        {
            const double line = std::floor(musicSeconds / period);
            boundary = line > std::floor(Clock / period);
            sinceBoundary = musicSeconds - line * period;
        }
        Clock = musicSeconds;
        if (boundary && desired >= 0 && desired < Score.States() && desired != Current)
        {
            From = Now;
            Current = desired;
            // The fade began on the boundary, which may lie part-way through this step.
            FadeElapsed = std::min(sinceBoundary, delta);
        }
        else FadeElapsed += delta;
        const double fade = Score.FadeSeconds();
        const double progress = fade > 0 ? std::min(1.0, FadeElapsed / fade) : 1.0;
        const double angle = progress * 1.5707963267948966;
        for (int layer = 0; layer < Score.Layers(); ++layer)
        {
            const float to = Score.TargetGain(Current, layer), from = From[layer];
            Now[layer] = to >= from ? static_cast<float>(from + (to - from) * std::sin(angle))
                                    : static_cast<float>(to + (from - to) * std::cos(angle));
        }
    }
    int State() const { return Current; }
    float Gain(int layer) const { return layer >= 0 && layer < static_cast<int>(Now.size()) ? Now[layer] : 0.f; }
    bool IsFading() const { return Ok && FadeElapsed < Score.FadeSeconds(); }
    double MusicSeconds() const { return Clock; }
    // Seconds until a newly requested state could begin; 0 for immediate transitions.
    double SecondsToBoundary() const
    {
        const double period = Score.BoundarySeconds();
        return Ok && period > 0 ? period - std::fmod(Clock, period) : 0;
    }
    bool Valid() const { return Ok; }
    const AdaptiveScore& Definition() const { return Score; }
private:
    AdaptiveScore Score;
    bool Ok = false;
    int Current = 0;
    double Clock = 0, FadeElapsed = 0;
    std::vector<float> From, Now;
};

// Keeps music engaged for a while after activity so states do not flap between bursts.
// Callers decide what counts as activity and whether pause stops the countdown.
class EngagementHold
{
public:
    void Reset() { Remaining = 0; }
    void Trigger(double seconds)
    {
        if (std::isfinite(seconds) && seconds > 0) Remaining = std::max(Remaining, seconds);
    }
    void Advance(double seconds)
    {
        if (std::isfinite(seconds) && seconds > 0) Remaining = std::max(0.0, Remaining - seconds);
    }
    bool Active() const { return Remaining > 0; }
    double Seconds() const { return Remaining; }
private:
    double Remaining = 0;
};
}
