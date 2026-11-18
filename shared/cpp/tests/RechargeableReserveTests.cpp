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
    RechargeableReserve timed(3);
    assert(timed.SpendFor(2, 1) == 1);
    assert(timed.SpendFor(2, 1) == .5 && timed.Empty());
    timed.RefillFor(2, .5); assert(timed.Remaining() == 1);
    timed.SpendFor(-1, 1); timed.RefillFor(1, -1);
    timed.SpendFor(1, std::numeric_limits<double>::infinity());
    assert(timed.Remaining() == 1);
    timed.RefillFor(std::numeric_limits<double>::max(), 2);
    assert(timed.Remaining() == 3);
    assert(timed.SpendFor(std::numeric_limits<double>::max(), 2) > 0);
    assert(timed.Empty());
}
