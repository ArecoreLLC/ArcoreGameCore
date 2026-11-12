#pragma once
#include <algorithm>
#include <cmath>
namespace GameCore
{
// Finite rechargeable reserve. Consumers decide when spending/refilling is allowed.
// Spend returns the fraction of the requested amount supplied (zero for invalid input).
class RechargeableReserve
{
public:
    explicit RechargeableReserve(double capacity)
        : Capacity(std::isfinite(capacity) && capacity > 0 ? capacity : 0), Value(Capacity) {}
    double Spend(double amount)
    {
        if (!std::isfinite(amount) || amount <= 0) return 0;
        const double supplied = std::min(Value, amount);
        Value -= supplied;
        return supplied / amount;
    }
    void Refill(double amount)
    {
        if (!std::isfinite(amount) || amount <= 0) return;
        // Subtract before addition to avoid overflowing on huge finite input.
        Value += std::min(Capacity - Value, amount);
    }
    double Fraction() const { return Capacity > 0 ? Value / Capacity : 0; }
    double Remaining() const { return Value; }
    bool Empty() const { return Value <= 0; }
    void Reset() { Value = Capacity; }
private:
    double Capacity;
    double Value;
};
}
