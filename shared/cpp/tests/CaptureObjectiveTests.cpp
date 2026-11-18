#include "../CaptureObjective.h"
#include <cassert>
#include <limits>
int main()
{
    using namespace GameCore;
    CaptureObjective C;
    C.Update(false,true,10); assert(C.GetState()==CaptureState::Locked);
    C.Update(true,false,0); assert(C.GetState()==CaptureState::Ready);
    C.Update(true,true,1); assert(C.GetProgress()==1.0/3.0);
    C.Update(true,false,0); assert(C.GetProgress()==0);
    C.Update(true,true,2); C.Update(false,true,0);
    assert(C.GetState()==CaptureState::Locked && C.GetProgress()==0);
    assert(C.Configure(2));
    C.Update(true,true,1);
    assert(!C.Configure(0) && !C.Configure(-1));
    assert(!C.Configure(std::numeric_limits<double>::infinity()));
    assert(!C.Configure(std::numeric_limits<double>::quiet_NaN()));
    C.Update(false,false,-1);
    C.Update(false,false,std::numeric_limits<double>::quiet_NaN());
    C.Update(false,false,std::numeric_limits<double>::infinity());
    assert(C.GetProgress()==.5);
    C.Update(true,true,1); assert(C.GetState()==CaptureState::Complete);
    C.Update(false,false,100); assert(C.GetProgress()==1);
    C.Reset(); assert(C.GetState()==CaptureState::Locked && C.GetProgress()==0);
    C.Update(true,true,1); assert(C.GetProgress()==.5);
    C.Update(true,true,std::numeric_limits<double>::max()); assert(C.GetProgress()==1);
    assert(C.Configure(1)); assert(C.GetState()==CaptureState::Locked);
}
