#include "../Buoyancy.h"
#include <cassert>
#include <limits>
#include <initializer_list>

int main()
{
    double depth = -123;
    assert(GameCore::TryEquilibriumDepth(100, 1000, 2000, depth));
    assert(std::abs(depth - .981) < 1e-12);
    assert(GameCore::TryEquilibriumDepth(200, 1000, 2000, depth, 10));
    assert(depth == 2); // inclusive force cap
    assert(!GameCore::TryEquilibriumDepth(201, 1000, 2000, depth, 10));
    assert(depth == 2); // rejected query preserves caller output
    assert(GameCore::TryEquilibriumDepth(0, 1000, 2000, depth));
    assert(depth == 0);
    for (double bad : {-1.0, std::numeric_limits<double>::infinity(), std::numeric_limits<double>::quiet_NaN()})
    {
        assert(!GameCore::TryEquilibriumDepth(bad, 1000, 2000, depth));
        assert(!GameCore::TryEquilibriumDepth(100, bad, 2000, depth));
        assert(!GameCore::TryEquilibriumDepth(100, 1000, bad, depth));
        assert(!GameCore::TryEquilibriumDepth(100, 1000, 2000, depth, bad));
    }
    assert(!GameCore::TryEquilibriumDepth(100, 0, 2000, depth));
    assert(!GameCore::TryEquilibriumDepth(100, 1000, 0, depth));
    assert(!GameCore::TryEquilibriumDepth(100, 1000, 2000, depth, 0));
    assert(!GameCore::TryEquilibriumDepth(std::numeric_limits<double>::max(), 1000, 2000, depth));
    assert(!GameCore::TryEquilibriumDepth(100, std::numeric_limits<double>::min(), 2000, depth));
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
