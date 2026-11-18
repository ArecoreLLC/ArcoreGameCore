#include "../PresentationMotion.h"
#include <cassert>
#include <limits>
#include <cmath>
int main()
{
    using namespace GameCore;
    assert(std::abs(ResponseAlpha(0.2, 0.2) - 0.5) < 1e-12);
    double remaining = 1;
    for (int i=0; i<60; ++i) remaining *= 1-ResponseAlpha(1.0/60, 0.2);
    assert(std::abs(remaining-(1-ResponseAlpha(1,0.2))) < 1e-12);
    assert(ResponseAlpha(-1, 0.2)==0 && ResponseAlpha(1, 0)==0);
    assert(ResponseAlpha(std::numeric_limits<double>::infinity(), 1)==0);
    assert(ResponseAlpha(1, std::numeric_limits<double>::quiet_NaN())==0);
    assert(ResponseAlpha(1000, 0.001)==1);
    FeedbackPulse p(1);
    assert(p.Value()==0);
    assert(!p.IsActive() && p.Progress()==1);
    p.Trigger(); assert(p.IsActive() && p.Progress()==0); p.Advance(0.5); assert(p.Progress()==0.5); assert(std::abs(p.Value()-0.5)<1e-12);
    p.Advance(-1); p.Advance(std::numeric_limits<double>::quiet_NaN());
    assert(std::abs(p.Value()-0.5)<1e-12);
    p.Trigger(); assert(p.Value()==1);
    p.Advance(100); assert(p.Value()==0);
    p.Trigger(); p.Reset(); assert(p.Value()==0);
    p.Trigger(0.25); assert(p.Value()==0.25 && p.Progress()==0);
    p.Advance(0.5); assert(std::abs(p.Value()-0.125)<1e-12);
    p.Trigger(0); p.Trigger(-1); p.Trigger(std::numeric_limits<double>::quiet_NaN());
    p.Trigger(std::numeric_limits<double>::infinity());
    assert(std::abs(p.Value()-0.125)<1e-12 && p.Progress()==0.5);
    p.Trigger(4); assert(p.Value()==1);
    p.Reset(); assert(p.Value()==0 && !p.IsActive());
    FeedbackPulse invalid(-1); invalid.Trigger(); invalid.Advance(1);
    assert(invalid.Value()==0);
}
