#include "../CooperativeTask.h"
#include <cassert>
#include <limits>
int main()
{
    GameCore::CooperativeTask work(12,3);
    assert(work.RequiredWorkers()==3 && work.MissingWorkers(1)==2);
    assert(work.MissingWorkers(std::numeric_limits<unsigned>::max())==0);
    assert(!work.CanWork(2) && work.CanWork(3));
    assert(!work.Advance(100,2) && work.Fraction()==0);
    assert(!work.Advance(1,3) && work.Fraction()==.25);
    assert(!work.Advance(-1,3));
    assert(!work.Advance(std::numeric_limits<double>::quiet_NaN(),3));
    assert(!work.Advance(1,3,std::numeric_limits<double>::infinity()));
    assert(work.Fraction()==.25);
    assert(work.Advance(3,3) && work.Complete());
    assert(!work.Advance(3,3) && work.Fraction()==1);
    assert(!work.CanWork(3) && work.MissingWorkers(1)==2);
    work.Reset(); assert(work.CanWork(3)); assert(work.Fraction()==0);
    assert(work.Advance(std::numeric_limits<double>::max(),3));
    GameCore::CooperativeTask invalid(0,0);
    assert(invalid.Advance(1,1));
    GameCore::CooperativeTask scaled(10,2);
    assert(!scaled.Advance(1,2,2.5) && scaled.Fraction()==.5);
    assert(scaled.Advance(1,2,2.5));
}
