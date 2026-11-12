#pragma once
#include <algorithm>
#include <cmath>

namespace GameCore
{
enum class MoveOrderState { Idle, Moving, Blocked, Arrived };
struct PlanarStep { double X = 0; double Y = 0; };

// Order state belongs to the unit, not the controller currently viewing it.
// Consumers supply actual post-collision positions to Observe, never predicted ones.
class PlanarMoveOrder
{
public:
    bool Issue(double X, double Y)
    {
        if (!Valid(X) || !Valid(Y)) return false;
        Goal = {X,Y}; State = MoveOrderState::Moving; return true;
    }
    void Cancel() { State = MoveOrderState::Idle; Goal = {}; }
    PlanarStep Step(double X, double Y, double Speed, double Seconds) const
    {
        if (!Active() || !Valid(X) || !Valid(Y) || !std::isfinite(Speed) || Speed <= 0 ||
            !std::isfinite(Seconds) || Seconds <= 0) return {};
        const double DX = Goal.X-X, DY = Goal.Y-Y, Distance = std::hypot(DX,DY);
        if (Distance == 0) return {};
        // Compare before multiplying: even very large finite time/speed cannot overflow.
        const double Travel = Seconds >= Distance/Speed ? Distance : Speed*Seconds;
        return {DX/Distance*Travel, DY/Distance*Travel};
    }
    bool Observe(double X, double Y, bool CollisionBlocked, double ArrivalRadius = 5)
    {
        if (!Active() || !Valid(X) || !Valid(Y) || !std::isfinite(ArrivalRadius) || ArrivalRadius < 0) return false;
        State = std::hypot(Goal.X-X, Goal.Y-Y) <= ArrivalRadius ? MoveOrderState::Arrived :
            CollisionBlocked ? MoveOrderState::Blocked : MoveOrderState::Moving;
        return true;
    }
    bool Active() const { return State == MoveOrderState::Moving || State == MoveOrderState::Blocked; }
    MoveOrderState GetState() const { return State; }
    PlanarStep GetGoal() const { return Goal; }
private:
    // Bounded coordinates prevent distance/subtraction overflow; unit convention is consumer-owned.
    static bool Valid(double Value) { return std::isfinite(Value) && std::abs(Value) <= 1.e9; }
    PlanarStep Goal;
    MoveOrderState State = MoveOrderState::Idle;
};
}
