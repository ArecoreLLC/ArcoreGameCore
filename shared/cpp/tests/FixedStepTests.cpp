#include "../FixedStep.h"
#include <cassert>
#include <limits>
#include <cmath>
int main()
{
    double a = 0, b = 0;
    int na = 0, nb = 0;
    for (int i=0;i<100;++i) GameCore::AdvanceFixedSteps(0.1,0.05,5,a,[&](double){++na;});
    for (int i=0;i<600;++i) GameCore::AdvanceFixedSteps(1.0/60,0.05,5,b,[&](double){++nb;});
    assert(na == 200 && nb == na && std::abs(a-b)<1e-10);
    assert(GameCore::AdvanceFixedSteps(1000,0.05,5,a,[](double){}) == 5);
    a=std::nextafter(0.05,0.0);
    assert(GameCore::AdvanceFixedSteps(1000,0.05,5,a,[](double){})==5);
    assert(a>=0 && a<0.05);
    assert(GameCore::AdvanceFixedSteps(0.05,0.05,5,a,[](double){})>0);
    a=0.025;
    assert(GameCore::AdvanceFixedSteps(0,0.05,5,a,[](double){})==0 && a==0.025);
    assert(GameCore::AdvanceFixedSteps(std::numeric_limits<double>::infinity(),0.05,5,a,[](double){})==0);
    assert(GameCore::AdvanceFixedSteps(1,0.05,0,a,[](double){})==0);
    assert(GameCore::AdvanceFixedSteps(1,0.05,1025,a,[](double){})==0);
    a=-1;
    assert(GameCore::AdvanceFixedSteps(1,0.05,5,a,[](double){})==0 && a==-1);
    // Synthetic second adapter: 60 Hz movement, different cap and callback.
    double remainder=0, distance=0;
    for(int i=0;i<120;++i)
        GameCore::AdvanceFixedSteps(1.0/120,1.0/60,8,remainder,[&](double dt){distance+=3*dt;});
    assert(std::abs(distance-3)<1e-10);
}
