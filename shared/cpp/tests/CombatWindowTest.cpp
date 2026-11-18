#include "../CombatWindow.h"
#include <cassert>
#include <limits>
int main() {
 GameCore::CombatWindow w;
 assert(w.Progress(100)==0);
 assert(w.TryStart(2,2,4));
 assert(w.Progress(1)==0 && w.Progress(2)==0 && w.Progress(3)==.5);
 assert(w.Progress(4)==1 && w.Progress(100)==1);
 assert(w.Progress(std::numeric_limits<double>::quiet_NaN())==0);
 assert(w.Progress(std::numeric_limits<double>::infinity())==0);
 assert(!w.TryStart(3,1,1)); assert(w.Progress(3)==.5);
 w.Reset(); assert(w.Progress(100)==0);
 assert(w.TryStart(0,0,0)); assert(w.Progress(0)==1);
 w.Reset();
 assert(!w.Active(0));
 assert(!w.TryStart(-1,.2,1));
 assert(!w.TryStart(0,-1,1));
 assert(!w.TryStart(0,2,1));
 assert(!w.TryStart(std::numeric_limits<double>::quiet_NaN(),.2,1));
 assert(w.TryStart(10,.25,1));
 assert(w.Active(10)); assert(!w.Active(10.25)); assert(!w.Active(9));
 assert(!w.TryStart(10.5,.2,1)); assert(w.Remaining(10.5)==.5);
 assert(!w.TryStart(9,.2,1)); assert(w.TryStart(11,.2,1));
 w.Reset(); double now=12345.678901234;
 assert(w.TryStart(now,.22,.9)); assert(w.Active(now));
 assert(!w.Active(now+.22)); assert(w.Remaining(now+.9)==0);
 w.Reset(); assert(w.TryStart(0,0,0)); assert(!w.Active(0));
 w.Reset(); assert(!w.TryStart(1e308,1e308,1e308)); assert(w.TryStart(0,.2,1));
 w.Reset(); assert(w.ActiveRemaining(0)==0);
 assert(w.TryStart(10,.25,1));
 assert(w.ActiveRemaining(10)==.25);
 assert(w.ActiveRemaining(10.125)==.125);
 assert(w.ActiveRemaining(10.25)==0 && w.Remaining(10.25)==.75);
 assert(w.ActiveRemaining(9)==0);
 assert(w.ActiveRemaining(std::numeric_limits<double>::infinity())==0);
 assert(w.ActiveRemaining(std::numeric_limits<double>::quiet_NaN())==0);
 assert(!w.TryStart(10.1,.5,1) && w.ActiveRemaining(10.125)==.125);
 w.Reset(); assert(w.ActiveRemaining(10)==0);
 return 0;
}
