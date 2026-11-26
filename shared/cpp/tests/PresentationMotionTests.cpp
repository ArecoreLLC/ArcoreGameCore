#include "../PresentationMotion.h"
#include <cassert>
#include <limits>
#include <cmath>
int main()
{
    using namespace GameCore;
    FiniteTransition door(2), split(2);
    assert(!door.Advance(10) && door.Value()==0);
    door.Start(); split.Start();
    assert(!door.Advance(.75));
    for (int i=0; i<75; ++i) split.Advance(.01);
    assert(std::abs(door.Value()-split.Value())<1e-10);
    const double before = door.Value();
    assert(!door.Advance(-1) && !door.Advance(0));
    assert(!door.Advance(std::numeric_limits<double>::quiet_NaN()));
    assert(!door.Advance(std::numeric_limits<double>::infinity()));
    assert(door.Value()==before);
    assert(door.Advance(100) && door.Value()==1 && !door.IsActive());
    assert(!door.Advance(1));
    door.Start(); assert(door.Value()==0 && door.IsActive());
    door.Reset(); assert(!door.IsActive() && door.Progress()==0);
    // Synthetic opacity reveal, independent of spatial transforms.
    FiniteTransition opacity(.1); opacity.Start(); opacity.Advance(.05);
    assert(std::abs(opacity.Value()-.5)<1e-10);
    assert(opacity.Advance(.05) && opacity.Value()==1);
    FiniteTransition invalidDuration(0); invalidDuration.Start();
    assert(invalidDuration.Advance(1));
    assert(SmoothStep01(-2)==0 && SmoothStep01(2)==1);
    assert(SmoothStep01(0)==0 && SmoothStep01(1)==1);
    assert(SmoothStep01(std::numeric_limits<double>::quiet_NaN())==0);
    assert(SmoothStep01(std::numeric_limits<double>::infinity())==0);
    double previous=0;
    for (int i=0; i<=100; ++i) {
        const double t=i/100.0, eased=SmoothStep01(t);
        assert(eased>=previous && eased<=1);
        assert(std::abs(eased+SmoothStep01(1-t)-1)<1e-12);
        const double descending=100-200*eased;
        assert(descending>=-100 && descending<=100);
        previous=eased;
    }
    assert(SmoothStep01(0.001)<0.00001);
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
    // Synthetic camera impulse: small events cannot erase a larger visible hit.
    p.Trigger(.8); p.Advance(.25); const double visible = p.Value();
    p.TriggerPeak(.1); assert(std::abs(p.Value()-visible)<1e-12);
    p.TriggerPeak(.9); assert(p.Value()==.9);
    p.TriggerPeak(-1); assert(p.Value()==.9);
    p.TriggerPeak(std::numeric_limits<double>::infinity()); assert(p.Value()==.9);
    p.Advance(2); p.TriggerPeak(.2); assert(p.Value()==.2);
    // Synthetic UI notification pulse with a different duration.
    FeedbackPulse ui(2); ui.TriggerPeak(.6); ui.Advance(1);
    ui.TriggerPeak(.1); assert(std::abs(ui.Value()-.3)<1e-12);
    FeedbackPulse invalid(-1); invalid.Trigger(); invalid.Advance(1);
    assert(invalid.Value()==0);
}
