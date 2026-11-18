#include "../TimedWindow.h"
#include <cassert>
#include <limits>

int main()
{
    GameCore::TimedWindow window(.125);
    assert(!window.Consume());
    window.Refresh();
    assert(!window.TryConsume(false) && window.IsOpen());
    assert(window.TryConsume(true) && !window.TryConsume(true));
    window.Refresh(); window.Advance(.125);
    assert(!window.TryConsume(true));
    window.Refresh();
    window.Advance(.0625);
    assert(window.IsOpen());
    assert(window.Consume());
    assert(!window.Consume());
    window.Refresh();
    window.Advance(.125);
    assert(!window.IsOpen());
    window.Refresh();
    window.Advance(-1);
    window.Advance(std::numeric_limits<double>::quiet_NaN());
    window.Advance(std::numeric_limits<double>::infinity());
    assert(window.IsOpen());
    window.Advance(std::numeric_limits<double>::max());
    assert(!window.IsOpen());
    window.Refresh();
    window.Reset();
    assert(!window.IsOpen());
    GameCore::TimedWindow a(.25), b(.25);
    a.Refresh(); b.Refresh();
    a.Advance(.125);
    for (int i = 0; i < 8; ++i) b.Advance(.015625);
    assert(a.Consume() && b.Consume());
    for (double invalid : {0.0, -1.0, std::numeric_limits<double>::infinity(), std::numeric_limits<double>::quiet_NaN()})
    {
        GameCore::TimedWindow inert(invalid);
        inert.Refresh();
        assert(!inert.Consume());
    }
}
