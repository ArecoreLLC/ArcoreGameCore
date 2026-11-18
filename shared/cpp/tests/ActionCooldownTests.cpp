#include "../ActionCooldown.h"
#include <cassert>
#include <limits>
int main()
{
    GameCore::ActionCooldown gate(.25);
    assert(gate.ReadyFraction(0) == 1 && gate.TryConsume(0));
    assert(!gate.TryConsume(0) && !gate.TryConsume(.249));
    assert(gate.ReadyFraction(.125) == .5);
    assert(gate.TryConsume(.25));
    assert(!gate.TryConsume(.1));
    assert(!gate.TryConsume(std::numeric_limits<double>::infinity()));
    assert(!gate.TryConsume(std::numeric_limits<double>::quiet_NaN()));
    assert(!gate.TryConsume(-1));
    assert(gate.TryConsume(100) && !gate.TryConsume(100));
    assert(gate.ReadyFraction(99) == 0 && gate.ReadyFraction(101) == 1);
    gate.Reset(); assert(gate.TryConsume(0));
    GameCore::ActionCooldown invalid(-1);
    assert(invalid.TryConsume(0) && !invalid.TryConsume(.2) && invalid.TryConsume(.25));
}
