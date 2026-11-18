#include "../RateRamp.h"
#include <cassert>
#include <cmath>
#include <limits>
int main()
{
    using GameCore::RateRamp;
    RateRamp a, b;
    const double whole = a.Advance(2, 750, 1500);
    double split = 0;
    for (int i = 0; i < 240; ++i) split += b.Advance(1.0 / 120, 750, 1500);
    assert(std::abs(whole - 1312.5) < 1e-9);
    assert(std::abs(split - whole) < 1e-9 && a.Value() == b.Value());
    assert(a.Advance(1, 0, 1500) == 187.5 && a.Value() == 0);
    a.Reset(100);
    assert(a.Advance(0.5, 100, 10) == 50);
    const double nan = std::numeric_limits<double>::quiet_NaN();
    assert(a.Advance(nan, 5, 1) == 0 && a.Advance(1, nan, 1) == 0);
    assert(a.Advance(-1, 0, 1) == 0 && a.Advance(1, -1, 1) == 0);
    assert(a.Advance(1, 0, 0) == 0 && a.Value() == 100);
    a.Reset(nan); assert(a.Value() == 0);
    a.Reset(-1); assert(a.Value() == 0);
    a.Reset(1e308); assert(a.Advance(1e308, 1e308, 1) == 0 && a.Value() == 1e308);
    a.Reset(); assert(a.Value() == 0);
}
