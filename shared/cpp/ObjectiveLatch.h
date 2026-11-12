#pragma once
#include <cstdint>
namespace GameCore
{
// Idempotent objective collection; consumer owns authority, range and visibility.
// Empty and invalid collections never complete. Supports up to 64 objectives.
class ObjectiveLatch
{
public:
    explicit ObjectiveLatch(unsigned count) : Count(count <= 64 ? count : 0) {}
    bool Activate(unsigned index)
    {
        if (index >= Count) return false;
        const std::uint64_t bit = std::uint64_t(1) << index;
        if ((Bits & bit) != 0) return false;
        Bits |= bit;
        ++Activated;
        return true;
    }
    bool IsActive(unsigned index) const
    {
        return index < Count && (Bits & (std::uint64_t(1) << index)) != 0;
    }
    unsigned Remaining() const { return Count - Activated; }
    bool IsComplete() const { return Count > 0 && Activated == Count; }
    void Reset() { Bits = 0; Activated = 0; }
private:
    unsigned Count = 0;
    unsigned Activated = 0;
    std::uint64_t Bits = 0;
};
}
