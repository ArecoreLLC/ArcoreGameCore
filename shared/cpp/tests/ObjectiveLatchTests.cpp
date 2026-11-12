#include "../ObjectiveLatch.h"
#include <cassert>
int main()
{
    GameCore::ObjectiveLatch objectives(3);
    assert(!objectives.IsComplete());
    assert(!objectives.Activate(3));
    assert(objectives.Activate(2));
    assert(!objectives.Activate(2));
    assert(objectives.Remaining() == 2);
    assert(objectives.Activate(0));
    assert(objectives.Activate(1));
    assert(objectives.IsComplete());
    objectives.Reset();
    assert(!objectives.IsComplete() && !objectives.IsActive(2));
    assert(objectives.Remaining() == 3);
    GameCore::ObjectiveLatch empty(0), invalid(65), full(64);
    assert(!empty.IsComplete() && !empty.Activate(0));
    assert(!invalid.IsComplete() && !invalid.Activate(0));
    for (unsigned i=0; i<64; ++i) assert(full.Activate(i));
    assert(full.IsComplete() && full.IsActive(63));
    assert(!full.IsActive(64) && !full.Activate(~0u));
}
