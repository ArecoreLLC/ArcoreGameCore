#include "../RechargeableReserve.h"
#include <cassert>
#include <limits>
#include <cmath>
int main()
{
    using GameCore::RechargeableReserve;
    RechargeableReserve r(3);
    assert(r.Fraction() == 1);
    assert(r.Spend(2) == 1 && r.Remaining() == 1);
    assert(r.Spend(2) == .5 && r.Empty());
    assert(r.Spend(1) == 0);
    r.Refill(1);
    r.Spend(-2); r.Refill(-2);
    r.Spend(std::numeric_limits<double>::infinity());
    r.Refill(std::numeric_limits<double>::quiet_NaN());
    assert(r.Remaining() == 1);
    r.Refill(std::numeric_limits<double>::max());
    assert(r.Remaining() == 3);
    r.Spend(3); r.Reset(); assert(r.Fraction() == 1);
    RechargeableReserve invalid(-1), nan(std::numeric_limits<double>::quiet_NaN());
    assert(invalid.Empty() && nan.Fraction() == 0);
    RechargeableReserve a(3), b(3);
    for(int i=0;i<60;++i) a.Spend(1.0/60);
    for(int i=0;i<120;++i) b.Spend(1.0/120);
    assert(std::abs(a.Remaining()-b.Remaining()) < 1e-12);
}
