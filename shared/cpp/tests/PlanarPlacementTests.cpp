#include "PlanarPlacement.h"
#include <cassert>
#include <limits>
#include <initializer_list>

int main()
{
    using namespace Arcore::Rules;
    PlacementPoint Out{99,99}; int Calls = 0;
    assert(FindPlanarPlacement({0,0},260,4,16,[](auto){return true;},Out));
    assert(Out.X == 0 && Out.Y == 0);
    assert(FindPlanarPlacement({0,0},260,4,16,[](auto P){return P.X >= 250;},Out));
    assert(Out.X == 260 && Out.Y == 0);
    assert(!FindPlanarPlacement({0,0},260,4,16,[&](auto){++Calls;return false;},Out));
    assert(Calls == 65 && Out.X == 260 && Out.Y == 0);
    Calls=0;
    assert(!FindPlanarPlacement({std::numeric_limits<double>::infinity(),0},260,4,16,[&](auto){++Calls;return true;},Out));
    assert(!FindPlanarPlacement({0,0},260,65,16,[&](auto){++Calls;return true;},Out));
    assert(!FindPlanarPlacement({0,0},0,4,16,[&](auto){++Calls;return true;},Out));
    assert(Calls == 0);
    const double NaN=std::numeric_limits<double>::quiet_NaN();
    for(double Step : {NaN, std::numeric_limits<double>::infinity(), -1.0})
        assert(!FindPlanarPlacement({0,0},Step,4,16,[&](auto){++Calls;return true;},Out));
    for(int Samples : {0,257})
        assert(!FindPlanarPlacement({0,0},260,4,Samples,[&](auto){++Calls;return true;},Out));
    assert(!FindPlanarPlacement({0,NaN},260,4,16,[&](auto){++Calls;return true;},Out));
    assert(!FindPlanarPlacement({0,0},260,-1,16,[&](auto){++Calls;return true;},Out));
    assert(Calls == 0);
    assert(!FindPlanarPlacement({0,0},260,0,16,[](auto){return false;},Out));
    // An occupied preferred point must not become a fallback on exhaustion.
    assert(Out.X == 260 && Out.Y == 0);
}
