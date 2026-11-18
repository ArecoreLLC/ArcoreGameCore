#include "../InteractionRules.h"
#include <cassert>
#include <limits>
int main()
{
    using namespace Arcore::Interaction;
    assert(WithinFacing(0.5,0.5));
    assert(WithinFacing(1,0.5));
    assert(!WithinFacing(0.49,0.5));
    assert(!WithinFacing(-1,0));
    assert(!WithinFacing(1.01,0));
    assert(!WithinFacing(0,-1.01));
    assert(!WithinFacing(std::numeric_limits<double>::quiet_NaN(),0));
    assert(!WithinFacing(0,std::numeric_limits<double>::infinity()));
    assert(WithinRange(100,10));
    assert(!WithinRange(-1,10));
    assert(!WithinRange(std::numeric_limits<double>::quiet_NaN(),10));
    assert(!CooldownReady(1,2));
    assert(CooldownReady(2,2));
    assert(WithinSpeed(0,0));
    assert(WithinSpeed(300,300));
    assert(WithinSpeed(-300,300));
    assert(!WithinSpeed(301,300));
    assert(!WithinSpeed(-301,300));
    assert(!WithinSpeed(0,-1));
    assert(!WithinSpeed(std::numeric_limits<double>::quiet_NaN(),300));
    assert(!WithinSpeed(0,std::numeric_limits<double>::infinity()));
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
