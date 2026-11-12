#include "../ResonanceRule.h"
#include <cassert>
#include <limits>
int main()
{
    using namespace ArcoreGameCore;
    ResonanceRule rule(2, 3, 0.5);
    assert(rule.RequiredPulses() == 3);
    assert(rule.ReadyFraction(0) == 1);
    assert(rule.ReadyFraction(-1) == 0);
    assert(rule.ReadyFraction(std::numeric_limits<double>::quiet_NaN()) == 0);
    assert(rule.Apply(1, 0) == PulseResult::WrongTone);
    assert(rule.Apply(-1, 0) == PulseResult::Invalid);
    assert(rule.Apply(2, std::numeric_limits<double>::infinity()) == PulseResult::Invalid);
    assert(rule.Apply(2, std::numeric_limits<double>::quiet_NaN()) == PulseResult::Invalid);
    assert(rule.Progress() == 0);
    assert(rule.Apply(2, 0) == PulseResult::Accepted);
    assert(rule.ReadyFraction(0) == 0);
    assert(rule.ReadyFraction(0.25) == 0.5);
    assert(rule.ReadyFraction(0.5) == 1);
    assert(rule.Progress() == 1);
    for (int i=0; i<500; ++i) assert(rule.Apply(2, 0.001*i) == PulseResult::CoolingDown);
    assert(rule.Apply(2, 0.5) == PulseResult::Accepted);
    assert(rule.ReadyFraction(0.2) == 0);
    assert(rule.Apply(2, 0.2) == PulseResult::CoolingDown);
    assert(rule.Apply(2, 1) == PulseResult::Completed);
    for (int i=0; i<1000; ++i) assert(rule.Apply(2, 2+i) == PulseResult::AlreadyComplete);
    assert(rule.Progress() == 3);
    assert(rule.ReadyFraction(20) == 0);
    rule.Reset();
    assert(!rule.Complete() && rule.Progress() == 0);
    assert(rule.Apply(2, 0) == PulseResult::Accepted);
    ResonanceRule fallback(0, -1, -1);
    assert(fallback.Apply(0, 0) == PulseResult::Completed);
}
