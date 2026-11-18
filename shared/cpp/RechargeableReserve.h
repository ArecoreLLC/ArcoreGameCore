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
    // Rate-based adapters avoid overflowing rate * seconds on long frames.
    // Return the fraction of this interval that can be supplied at the rate.
    double SpendFor(double seconds, double rate)
    {
        if (!std::isfinite(seconds) || seconds <= 0 ||
            !std::isfinite(rate) || rate <= 0) return 0;
        const double availableSeconds = Value / rate;
        if (seconds >= availableSeconds) {
            Value = 0;
            return std::min(1.0, availableSeconds / seconds);
        }
        Value -= seconds * rate;
        return 1;
    }
    void RefillFor(double seconds, double rate)
    {
        if (!std::isfinite(seconds) || seconds <= 0 ||
            !std::isfinite(rate) || rate <= 0) return;
        if (seconds >= (Capacity - Value) / rate) Value = Capacity;
        else Value += seconds * rate;
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
