#include "../DeadlineCountdown.h"
#include <cassert>
#include <initializer_list>
#include <limits>
int main()
{
    using C = GameCore::DeadlineCountdown;
    assert(C::SecondsLeft(103,100)==3);
    assert(C::SecondsLeft(103,100.01)==3);
    assert(C::SecondsLeft(103,101)==2);
    assert(C::SecondsLeft(103,102.99)==1);
    assert(!C::HasElapsed(103,102.99));
    assert(C::HasElapsed(103,103));
    assert(C::SecondsLeft(103,103)==0);
    assert(C::SecondsLeft(103,110)==0 && C::HasElapsed(103,110));
    for(double invalid : {std::numeric_limits<double>::infinity(), std::numeric_limits<double>::quiet_NaN()})
    {
        assert(!C::HasElapsed(invalid,100) && C::SecondsLeft(invalid,100)==0);
        assert(!C::HasElapsed(103,invalid) && C::SecondsLeft(103,invalid)==0);
    }
    assert(C::SecondsLeft(std::numeric_limits<double>::max(),-std::numeric_limits<double>::max())==std::numeric_limits<int>::max());
}
