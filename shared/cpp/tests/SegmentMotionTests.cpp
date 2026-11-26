#include "../SegmentMotion.h"
#include <cassert>
#include <cmath>
#include <limits>
int main()
{
    using GameCore::AdvanceSegment;
    auto step=AdvanceSegment(160,230,1);
    assert(step.Arrived && step.Distance==160);
    auto next=AdvanceSegment(160,100,1-step.Seconds);
    assert(!next.Arrived && std::abs(next.Distance-30.4347826087)<1e-8);
    double distance=160;
    for(int i=0;i<30;++i) distance-=AdvanceSegment(distance,100,.02).Distance;
    assert(std::abs(distance-100)<1e-9);
    assert(AdvanceSegment(0,10,0).Arrived);
    assert(!AdvanceSegment(1,0,1).Arrived);
    assert(AdvanceSegment(-1,1,1).Distance==0);
    assert(AdvanceSegment(1,1,-1).Seconds==0);
    assert(!AdvanceSegment(std::numeric_limits<double>::infinity(),1,1).Arrived);
    assert(!AdvanceSegment(1,std::numeric_limits<double>::quiet_NaN(),1).Arrived);
    auto conveyor=AdvanceSegment(.25,.5,2);
    assert(conveyor.Arrived && conveyor.Seconds==.5);
}
