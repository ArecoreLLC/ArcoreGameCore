#include "../WheelContact.h"
#include <cassert>
#include <limits>
int main() {
    using namespace gamecore;
    assert(SuspensionForce(.1,0,20000,2000,8000) == 2000);
    assert(SuspensionForce(.1,1,20000,2000,8000) == 4000);
    assert(SuspensionForce(.1,-2,20000,2000,8000) == 0);
    assert(SuspensionForce(0,4,20000,2000,8000) == 0);
    assert(SuspensionForce(1,4,20000,2000,8000) == 8000);
    assert(SuspensionForce(.1,0,-1,2000,8000) == 0);
    assert(SuspensionForce(std::numeric_limits<double>::quiet_NaN(),0,1,1,1) == 0);
    assert(SuspensionForce(1,std::numeric_limits<double>::infinity(),1,1,1) == 0);
    const auto combined = LimitTireForce(3000,4000,1000,1);
    assert(std::abs(combined.longitudinal-600)<1e-9 && std::abs(combined.lateral-800)<1e-9);
    assert(LimitTireForce(100,100,0,1).longitudinal == 0);
    assert(LimitTireForce(100,100,100,-1).lateral == 0);
    assert(LimitTireForce(100,std::numeric_limits<double>::infinity(),100,1).longitudinal == 0);
    for (double hz : {30.0,60.0,120.0}) {
        double height=.65, velocity=0, dt=1/hz;
        for(int i=0;i<int(8*hz);++i) {
            const double force=SuspensionForce(.65-height,-velocity,20000,2200,8000);
            velocity+=(force/150-9.81)*dt; height+=velocity*dt;
            assert(std::isfinite(height) && height>0 && height<1);
        }
        assert(std::abs(height-(.65-150*9.81/20000))<.002);
        assert(std::abs(velocity)<.002);
    }
}
