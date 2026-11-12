#include "../Buoyancy.h"
#include <cassert>
#include <limits>

int main()
{
    GameCore::MassProperties mass;
    assert(mass.X() == 0 && mass.Y() == 0);
    assert(mass.Add(100, 1, -2));
    assert(mass.Add(100, -1, 2));
    assert(mass.Mass == 200 && mass.X() == 0 && mass.Y() == 0);
    assert(!mass.Add(0, 0, 0));
    assert(!mass.Add(-1, 0, 0));
    assert(!mass.Add(std::numeric_limits<double>::infinity(), 0, 0));
    assert(!mass.Add(1, std::numeric_limits<double>::quiet_NaN(), 0));
    assert(mass.Mass == 200);
    assert(GameCore::BuoyantForce(1, 0, 1000, 100, 2000) == 1000);
    assert(GameCore::BuoyantForce(0, -10, 1000, 100, 2000) == 0);
    assert(GameCore::BuoyantForce(-1, 0, 1000, 100, 2000) == 0);
    assert(GameCore::BuoyantForce(1, 20, 1000, 100, 2000) == 0);
    assert(GameCore::BuoyantForce(10, -20, 1000, 100, 2000) == 2000);
    assert(GameCore::BuoyantForce(1, 0, -1, 100, 2000) == 0);
    assert(GameCore::BuoyantForce(1, 0, 1000, -1, 2000) == 0);
    assert(GameCore::BuoyantForce(1, 0, 1000, 100, -1) == 0);
    assert(GameCore::BuoyantForce(std::numeric_limits<double>::quiet_NaN(), 0, 1000, 100, 2000) == 0);
}
