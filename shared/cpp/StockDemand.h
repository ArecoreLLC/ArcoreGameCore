#pragma once
#include <array>
#include <cstddef>
#include <cstdint>

namespace arcore {
// Read-only round-robin selection. N means no eligible item. Counts describe
// available inventory and outstanding promises, not ownership transfers.
template <std::size_t N>
std::size_t SelectStockDemand(const std::array<std::int32_t, N>& available,
                            const std::array<std::int32_t, N>& promised,
                            std::size_t start = 0) {
    static_assert(N > 0, "Catalog must not be empty");
    std::size_t item = start % N;
    for (std::size_t visited = 0; visited < N; ++visited) {
        // Invalid counts fail closed for this item; comparison avoids overflow.
        if (promised[item] >= 0 && available[item] > promised[item]) return item;
        item = item == N - 1 ? 0 : item + 1;
    }
    return N;
}
}
