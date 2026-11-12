#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>

namespace arcore {
// Engine-neutral fixed-catalog inventory. Catalog ordering is owned/versioned by consumers.
// All failures leave both ledgers and the wallet unchanged. Not thread safe: authority
// must serialize transactions. Persistence and networking remain engine responsibilities.
template <std::size_t ItemCount>
class StockLedger {
public:
    explicit StockLedger(std::int32_t capacity = 12) : Capacity(capacity > 0 ? capacity : 0) {}
    std::int32_t Count(std::size_t item) const { return item < ItemCount ? Counts[item] : 0; }
    std::int32_t Total() const { std::int32_t result = 0; for (auto n : Counts) result += n; return result; }
    bool Add(std::size_t item, std::int32_t quantity = 1) {
        if (item >= ItemCount || quantity <= 0 || quantity > Capacity - Total()) return false;
        Counts[item] += quantity; return true;
    }
    bool TransferTo(StockLedger& destination, std::size_t item, std::int32_t quantity) {
        if (&destination == this || item >= ItemCount || quantity <= 0 || Count(item) < quantity) return false;
        if (!destination.Add(item, quantity)) return false;
        Counts[item] -= quantity; return true;
    }
    // Explicit consumption/loss. Does not award currency; invalid requests are atomic.
    bool Remove(std::size_t item, std::int32_t quantity = 1) {
        if (item >= ItemCount || quantity <= 0 || Count(item) < quantity) return false;
        Counts[item] -= quantity; return true;
    }
    bool Sell(std::size_t item, std::int32_t quantity, std::int32_t unitPrice, std::int32_t& wallet) {
        if (item >= ItemCount || quantity <= 0 || Count(item) < quantity || unitPrice <= 0 || wallet < 0) return false;
        const std::int64_t proceeds = static_cast<std::int64_t>(quantity) * unitPrice;
        if (proceeds > std::numeric_limits<std::int32_t>::max() - wallet) return false;
        Counts[item] -= quantity; wallet += static_cast<std::int32_t>(proceeds); return true;
    }
private:
    std::array<std::int32_t, ItemCount> Counts{};
    std::int32_t Capacity;
};
}
