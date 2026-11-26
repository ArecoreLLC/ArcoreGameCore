#include "../FormationSlots.h"
#include <cassert>
#include <limits>
int main() {
 using GameCore::CenteredFormation;
 assert(CenteredFormation(0,1,6,60).X==0);
 assert(CenteredFormation(6,7,3,12).X==0);
 assert(CenteredFormation(6,7,3,12).Y==12);
 assert(CenteredFormation(0,0,3,12).X==0);
 assert(CenteredFormation(0,7,0,12).Y==0);
 assert(CenteredFormation(7,7,3,12).Y==0);
 assert(CenteredFormation(0,7,3,std::numeric_limits<double>::infinity()).X==0);
 for(unsigned n=1;n<=50;++n) {
  double sum=0;
  for(unsigned i=0;i<n;++i) {
   auto p=CenteredFormation(i,n,6,60); sum+=p.X;
   assert(std::abs(p.X)<=150 && std::abs(p.Y)<=240);
  }
  assert(std::abs(sum)<1e-9);
 }
}
