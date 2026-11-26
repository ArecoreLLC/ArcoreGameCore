#include "../StableSelection.h"
#include <cassert>
#include <limits>
int main() {
    using C = GameCore::StableSelection::Candidate;
    GameCore::StableSelection s;
    C a[]={{2,.95},{1,.96}};
    assert(s.Select(a,2,.02)==1);
    a[0].Score=.97; assert(s.Select(a,2,.02)==1);
    a[0].Score=.99; assert(s.Select(a,2,.02)==2);
    assert(s.Select(a+1,1,.02)==1); // obstruction removes previous target
    assert(s.Select(nullptr,10,.02)==-1);
    C priorities[]={{7,-20},{3,-20},{9,-30}};
    assert(s.Select(priorities,3,5)==3);
    priorities[0].Score=-16; assert(s.Select(priorities,3,5)==3);
    priorities[0].Score=-14; assert(s.Select(priorities,3,5)==7);
    s.Reset(); assert(s.Get()==-1);
    C bad[]={{0,std::numeric_limits<double>::quiet_NaN()},{-2,100}};
    assert(s.Select(bad,2,0)==-1);
    C duplicate[]={{1,2},{1,5},{2,4}};
    assert(s.Select(duplicate,3,-1)==1);
    assert(s.Select(duplicate,0,0)==-1);
}
