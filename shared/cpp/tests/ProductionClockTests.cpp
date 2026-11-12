#include "../ProductionClock.h"
#include <cassert>
#include <limits>

int main()
{
    GameCore::ProductionClock restored(4.0);
    assert(restored.RestoreFraction(0.75));
    assert(!restored.RestoreFraction(1.0));
    assert(!restored.RestoreFraction(-0.1));
    assert(!restored.RestoreFraction(std::numeric_limits<double>::quiet_NaN()));
    assert(!restored.RestoreFraction(std::numeric_limits<double>::infinity()));
    assert(restored.Fraction() == 0.75);
    assert(restored.Advance(1.0, true));
    GameCore::ProductionClock clock(2.0);
    assert(!clock.Advance(1.0, true));
    assert(!clock.Advance(100.0, false));
    assert(clock.Fraction() == 0.5);
    assert(!clock.Advance(-1.0, true));
    assert(!clock.Advance(std::numeric_limits<double>::infinity(), true));
    assert(!clock.Advance(std::numeric_limits<double>::quiet_NaN(), true));
    assert(clock.Advance(1.0, true));
    assert(clock.Fraction() == 0.0);
    assert(clock.Advance(100.0, true));
    assert(!clock.Advance(0.0, true));
    assert(clock.Fraction() == 0.0);
    clock.Advance(1.0, true);
    clock.Reset();
    assert(clock.Fraction() == 0.0);
    GameCore::ProductionClock invalid(0.0);
    assert(!invalid.Advance(3.0, true));
    assert(invalid.Advance(1.0, true));
    return 0;
}
