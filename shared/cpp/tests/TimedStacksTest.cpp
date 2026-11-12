#include "../TimedStacks.h"
#include <cassert>
#include <limits>
int main() {
 GameCore::TimedStacks s;
 assert(s.Count(0)==0); assert(!s.Add(-1,5,3));
 assert(s.Add(10,5,3)); assert(s.Add(11,5,3)); assert(s.Count(15)==2);
 assert(s.Add(12,5,3)); assert(s.Add(13,5,3)); assert(s.Count(17)==3);
 assert(!s.Add(12,5,3)); assert(!s.Add(14,0,3)); assert(!s.Add(14,5,0));
 assert(!s.Add(1e308,1e308,3)); assert(!s.Add(std::numeric_limits<double>::quiet_NaN(),5,3));
 assert(s.Count(18)==0); assert(s.Add(18,5,3)); assert(s.Consume(18)==1); assert(s.Consume(18)==0);
 assert(s.Add(19,5,3)); assert(s.Consume(18)==0); assert(s.Count(19)==1);
 s.Reset(); assert(s.Add(0,1,3)); assert(s.Consume(1)==0);
}
