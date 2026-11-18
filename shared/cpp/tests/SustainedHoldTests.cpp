#include "../SustainedHold.h"
#include <cassert>
#include <limits>
int main()
{
    GameCore::SustainedHold hold(3);
    assert(!hold.Advance(1, true));
    assert(hold.Fraction() > 0);
    assert(!hold.Advance(1, false));
    assert(hold.Fraction() == 0);
    assert(!hold.Advance(2, true));
    assert(hold.Advance(1, true));
    assert(hold.Fraction() == 1);
    assert(!hold.Advance(10, true));
    hold.Reset();
    assert(!hold.Advance(1, true));
    assert(!hold.Advance(std::numeric_limits<double>::quiet_NaN(), true));
    assert(hold.Fraction() == 0);
    assert(!hold.Advance(-1, true));
    assert(!hold.Advance(std::numeric_limits<double>::infinity(), true));
    assert(hold.Advance(std::numeric_limits<double>::max(), true));
    GameCore::SustainedHold invalid(0);
    assert(!invalid.Advance(10, true));
    assert(invalid.Fraction() == 0);
}
