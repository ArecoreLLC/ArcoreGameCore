#include "HoldRepeat.h"
#include <cassert>
#include <limits>
int main()
{
    using ArcoreGameCore::HoldRepeat;
    HoldRepeat repeat;
    assert(!repeat.Update(false, 0));
    assert(repeat.Update(true, 0));
    assert(!repeat.Update(true, 0));
    assert(!repeat.Update(true, 0.49));
    assert(repeat.Update(true, 0.5));
    assert(!repeat.Update(true, 0.1));
    assert(!repeat.Update(true, std::numeric_limits<double>::infinity()));
    assert(!repeat.Update(true, std::numeric_limits<double>::quiet_NaN()));
    assert(repeat.Update(true, 100)); // Hitch never replays missed events.
    assert(!repeat.Update(true, 100));
    assert(!repeat.Update(true, 100.25));
    repeat.CancelUntilRelease();
    assert(!repeat.IsActive());
    assert(!repeat.Update(true, 101));
    assert(!repeat.Update(false, 101));
    assert(repeat.Update(true, 0)); // New attempt may use a new clock.
    assert(!repeat.Update(false, 0.1));
    assert(repeat.Update(true, 0.1)); // Taps are immediate; ability owns cooldown.
    HoldRepeat invalid(-1);
    assert(!invalid.Update(true, -1));
    assert(invalid.Update(true, 0));
    assert(!invalid.Update(true, 0.49));
    assert(invalid.Update(true, 0.5));
}
