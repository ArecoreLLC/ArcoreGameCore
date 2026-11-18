#include "JumpGrace.h"
#include <cassert>
#include <limits>
int main() {
 using ArcoreGameCore::JumpGrace;
 JumpGrace j;
 assert(!j.Update(true,false,0));
 assert(j.Update(false,true,0.08));
 assert(!j.Update(false,true,0.09));
 assert(!j.Update(true,false,0.30));
 assert(j.Update(true,true,0.31));
 assert(!j.Update(true,true,0.32));
 j.Reset();
 assert(!j.Update(false,true,1));
 assert(j.Update(true,false,1.1));
 j.Reset();
 assert(!j.Update(false,true,2));
 assert(!j.Update(true,false,2.2));
 assert(!j.Update(false,true,std::numeric_limits<double>::quiet_NaN()));
 assert(!j.Update(false,true,1));
 j.Reset();
 assert(!j.Update(true,false,0));
 assert(!j.Update(false,true,0.11));
 j.Reset();
 assert(!j.Update(false,false,0));
 assert(!j.Update(true,false,0.01));
 JumpGrace zero(0,0);
 assert(zero.Update(true,true,0));
}
