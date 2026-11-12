#include "../CombatWindow.h"
#include <cassert>
#include <limits>
int main() {
 GameCore::CombatWindow w;
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
 return 0;
}
