#include "../AdaptiveMusic.h"
#include <cassert>
#include <cmath>
#include <limits>

using GameCore::AdaptiveMixer;
using GameCore::AdaptiveScore;
using GameCore::EngagementHold;
using GameCore::MusicBoundary;

static bool Near(double a, double b, double tolerance = 1e-5) { return std::abs(a - b) <= tolerance; }

static AdaptiveScore Score(MusicBoundary boundary = MusicBoundary::Bar)
{
    AdaptiveScore s;
    s.bpm = 120; s.beatsPerBar = 4; s.loopBars = 2; s.fadeBeats = 2; s.masterDb = -6;
    s.boundary = boundary;
    s.layerNames = {"Pad", "Drums"};
    s.stateNames = {"Explore", "Combat"};
    s.stateGainDb = {{0, -60}, {-6, 0}};
    return s;
}

int main()
{
    const AdaptiveScore s = Score();
    assert(s.Valid() && Near(s.BarSeconds(), 2) && Near(s.FadeSeconds(), 1) && Near(s.LoopSeconds(), 4));
    assert(Near(s.TargetGain(0, 0), std::pow(10.0, -6.0 / 20)) && s.TargetGain(0, 1) == 0);
    assert(s.TargetGain(5, 0) == 0 && s.TargetGain(0, -1) == 0 && s.StateIndex("Combat") == 1 && s.StateIndex("x") == -1);

    // Waits for the bar line, then fades with equal power from the bar line, not the frame.
    AdaptiveMixer m(s);
    m.Advance(1.5, 1);
    assert(m.State() == 0 && !m.IsFading() && Near(m.SecondsToBoundary(), 0.5));
    m.Advance(1.0, 1); // Crosses the bar at 2.0; the fade is 0.5 s in.
    assert(m.State() == 1 && m.IsFading());
    const double angle = 0.5 * 1.5707963267948966;
    assert(Near(m.Gain(1), s.TargetGain(1, 1) * std::sin(angle)));
    assert(Near(m.Gain(0), s.TargetGain(1, 0) + (s.TargetGain(0, 0) - s.TargetGain(1, 0)) * std::cos(angle)));
    m.Advance(0.5, 1);
    assert(!m.IsFading() && Near(m.Gain(0), s.TargetGain(1, 0)) && Near(m.Gain(1), s.TargetGain(1, 1)));

    // Frame partitioning does not change the result.
    AdaptiveMixer whole(s), split(s);
    whole.Advance(2.75, 1);
    for (int i = 0; i < 165; ++i) split.Advance(2.75 / 165, 1);
    assert(Near(whole.Gain(0), split.Gain(0), 1e-4) && Near(whole.Gain(1), split.Gain(1), 1e-4));

    // Hold (-1) and unknown states keep the current state across boundaries.
    m.Advance(10, -1); assert(m.State() == 1);
    m.Advance(10, 9); assert(m.State() == 1);

    // Audio-clock path: an earlier time resynchronizes without a transition.
    AdaptiveMixer clocked(s);
    clocked.AdvanceTo(1.9, 1); assert(clocked.State() == 0);
    clocked.AdvanceTo(0.5, 1); assert(clocked.State() == 0 && Near(clocked.MusicSeconds(), 0.5));
    clocked.AdvanceTo(3.0, 1); assert(clocked.State() == 1 && !clocked.IsFading());

    // Boundary kinds.
    AdaptiveMixer beat(Score(MusicBoundary::Beat));
    beat.Advance(0.4, 1); assert(beat.State() == 0);
    beat.Advance(0.2, 1); assert(beat.State() == 1);
    AdaptiveMixer phrase(Score(MusicBoundary::Phrase));
    phrase.Advance(3.9, 1); assert(phrase.State() == 0);
    phrase.Advance(0.2, 1); assert(phrase.State() == 1);
    AdaptiveMixer now(Score(MusicBoundary::Immediate));
    now.Advance(0, 1); assert(now.State() == 1 && now.SecondsToBoundary() == 0);
    AdaptiveScore cut = Score(); cut.fadeBeats = 0;
    AdaptiveMixer instant(cut);
    instant.Advance(2.01, 1); assert(Near(instant.Gain(1), cut.TargetGain(1, 1)));

    // Invalid input fails closed.
    const double nan = std::numeric_limits<double>::quiet_NaN();
    m.Advance(nan, 0); m.Advance(-1, 0); m.AdvanceTo(nan, 0); assert(m.State() == 1);
    AdaptiveScore bad = Score(); bad.stateGainDb[1].pop_back();
    AdaptiveMixer silent(bad);
    assert(!silent.Valid() && silent.Gain(0) == 0);
    silent.Advance(5, 1); assert(silent.State() == 0 && silent.Gain(0) == 0);
    bad = Score(); bad.bpm = nan; assert(!bad.Valid());
    bad = Score(); bad.stateGainDb[0][0] = 13; assert(!bad.Valid());
    AdaptiveMixer clamped(s, 7); assert(clamped.State() == 1);

    EngagementHold hold;
    assert(!hold.Active());
    hold.Trigger(6); hold.Trigger(2); assert(Near(hold.Seconds(), 6));
    hold.Advance(5); assert(hold.Active());
    hold.Advance(nan); hold.Advance(-1); assert(Near(hold.Seconds(), 1));
    hold.Advance(2); assert(!hold.Active() && hold.Seconds() == 0);
    hold.Trigger(nan); assert(!hold.Active());
    hold.Trigger(3); hold.Reset(); assert(!hold.Active());
    return 0;
}
