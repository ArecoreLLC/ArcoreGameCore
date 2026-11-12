#include "../InteractionRules.h"
#include <cassert>
#include <limits>
int main()
{
    using namespace Arcore::Interaction;
    assert(WithinRange(100,10));
    assert(!WithinRange(-1,10));
    assert(!WithinRange(std::numeric_limits<double>::quiet_NaN(),10));
    assert(!CooldownReady(1,2));
    assert(CooldownReady(2,2));
    NearestCandidate candidate;
    assert(!candidate.Consider(-1,0,10));
    assert(!candidate.Consider(0,1,10,false));
    assert(!candidate.Consider(0,101,10));
    assert(candidate.Index == -1);
    assert(candidate.Consider(3,100,10));
    assert(candidate.Consider(4,25,10));
    assert(!candidate.Consider(5,25,10));
    assert(!candidate.Consider(6,std::numeric_limits<double>::infinity(),10));
    assert(candidate.Index == 4);
    assert(candidate.DistanceSquared == 25);
}
