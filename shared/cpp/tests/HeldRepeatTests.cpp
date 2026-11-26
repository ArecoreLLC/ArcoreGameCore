#include "../HeldRepeat.h"
#include <cassert>
#include <limits>
int main()
{
    GameCore::HeldRepeat dial(.4,.125);
    assert(!dial.Advance(10));
    assert(dial.Press() && !dial.Press());
    assert(!dial.Advance(.25));
    assert(!dial.Advance(-1));
    assert(!dial.Advance(std::numeric_limits<double>::quiet_NaN()));
    assert(!dial.Advance(std::numeric_limits<double>::infinity()));
    assert(dial.Advance(.151));
    assert(dial.Advance(10));
    assert(!dial.Advance(.0625));
    assert(dial.Advance(.0625));
    dial.Release(); assert(!dial.Advance(10)); assert(dial.Press());
    assert(!dial.Advance(.125));
    GameCore::HeldRepeat menu(1,.5);
    assert(menu.Press()); assert(!menu.Advance(.5)); assert(menu.Advance(.5));
    assert(menu.Advance(.5)); menu.Release(); assert(!menu.Advance(.5));
    GameCore::HeldRepeat fallback(-1,0);
    assert(fallback.Press()); assert(!fallback.Advance(.2)); assert(fallback.Advance(.2));
}
