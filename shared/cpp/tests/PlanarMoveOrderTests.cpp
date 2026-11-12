#include "../PlanarMoveOrder.h"
#include <cassert>
#include <limits>
int main()
{
    using namespace GameCore;
    PlanarMoveOrder O;
    assert(!O.Active() && O.Step(0,0,10,1).X == 0);
    assert(O.Issue(3,4));
    const auto S = O.Step(0,0,2,1);
    assert(std::abs(S.X-1.2)<1e-9 && std::abs(S.Y-1.6)<1e-9);
    assert(O.GetState() == MoveOrderState::Moving); // Proposal is not arrival evidence.
    assert(O.Observe(0,0,true,0) && O.GetState() == MoveOrderState::Blocked);
    assert(O.Step(0,0,100,100).X == 3);
    assert(O.Observe(1,1,false,0) && O.GetState() == MoveOrderState::Moving);
    assert(!O.Issue(std::numeric_limits<double>::infinity(),0));
    assert(!O.Issue(1.e10,0) && O.GetGoal().X == 3);
    assert(!O.Observe(0,0,false,-1));
    assert(!O.Observe(std::numeric_limits<double>::quiet_NaN(),0,false));
    assert(O.Step(0,0,-1,1).X == 0 && O.Step(0,0,1,0).X == 0);
    assert(O.Step(0,0,std::numeric_limits<double>::infinity(),1).X == 0);
    assert(O.Step(0,0,1,std::numeric_limits<double>::quiet_NaN()).X == 0);
    const auto Huge = O.Step(0,0,1.e308,1.e308);
    assert(Huge.X == 3 && Huge.Y == 4);
    assert(O.Observe(3,4,true,0) && O.GetState() == MoveOrderState::Arrived);
    assert(!O.Observe(0,0,false) && O.Step(0,0,1,1).X == 0);
    assert(O.Issue(-10,20));
    O.Cancel();
    assert(O.GetState() == MoveOrderState::Idle && O.GetGoal().X == 0);
}
