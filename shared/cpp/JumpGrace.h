#pragma once
#include <cmath>
namespace ArcoreGameCore
{
// Engine owns grounding and jump execution. One request per press; landing rearms.
class JumpGrace
{
public:
    explicit JumpGrace(double coyote = 0.10, double buffer = 0.12)
        : Coyote(ValidDuration(coyote)), Buffer(ValidDuration(buffer)) {}
    bool Update(bool grounded, bool pressed, double now)
    {
        if (!std::isfinite(now) || now < 0 || now < LastTime) return false;
        LastTime = now;
        if (grounded)
        {
            LastGround = now;
            if (!WasGrounded) Consumed = false;
        }
        if (pressed) Request = now;
        WasGrounded = grounded;
        if (Request >= 0 && now - Request > Buffer) Request = -1;
        if (!Consumed && Request >= 0 && LastGround >= 0 &&
            (grounded || now - LastGround <= Coyote))
        {
            Consumed = true;
            Request = -1;
            return true;
        }
        return false;
    }
    void Reset() { LastTime = LastGround = Request = -1; WasGrounded = Consumed = false; }
private:
    static double ValidDuration(double v) { return std::isfinite(v) && v >= 0 ? v : 0; }
    double Coyote, Buffer;
    double LastTime = -1, LastGround = -1, Request = -1;
    bool WasGrounded = false, Consumed = false;
};
}
