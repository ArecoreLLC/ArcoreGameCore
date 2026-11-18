#include "../RateRamp.h"
#include <cassert>
#include <limits>
int main() {
    GameCore::SignedRateRamp whole(200), split(200);
    double distance = whole.Advance(2, -200, 200), pieces = 0;
    for (int i=0; i<200; ++i) pieces += split.Advance(.01, -200, 200);
    assert(std::abs(distance) < 1e-9);
    assert(std::abs(distance-pieces) < 1e-8);
    assert(std::abs(whole.Value()-split.Value()) < 1e-8);
    assert(whole.Advance(1,-200,200) == -200);
    assert(whole.Advance(-1,100,100) == 0 && whole.Value() == -200);
    assert(whole.Advance(1,std::numeric_limits<double>::infinity(),100) == 0);
    whole.Reset(100);
    assert(whole.Advance(2,0,100) == 50 && whole.Value() == 0);
    whole.Reset(std::numeric_limits<double>::max());
    assert(whole.Advance(1,-std::numeric_limits<double>::max(),1) == 0);
    assert(whole.Value() == std::numeric_limits<double>::max());
    GameCore::RateRamp legacy(100);
    assert(legacy.Advance(1,-100,100) == 0 && legacy.Value() == 100);
}
