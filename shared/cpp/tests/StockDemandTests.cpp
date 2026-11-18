#include "../StockDemand.h"
#include <cassert>
#include <limits>
int main() {
    using Counts = std::array<std::int32_t, 3>;
    const Counts stock{0, 2, 1};
    Counts promised{};
    assert(arcore::SelectStockDemand(stock, promised) == 1);
    assert(arcore::SelectStockDemand(stock, promised, 2) == 2);
    promised = {0, 2, 1};
    assert(arcore::SelectStockDemand(stock, promised) == 3);
    promised[1] = 1;
    assert(arcore::SelectStockDemand(stock, promised, 2) == 1);
    assert(arcore::SelectStockDemand(Counts{-1, 0, 0}, Counts{}) == 3);
    assert(arcore::SelectStockDemand(stock, Counts{0, -1, 1}) == 3);
    assert(arcore::SelectStockDemand(Counts{INT32_MAX, 0, 0}, Counts{INT32_MAX-1, 0, 0}, SIZE_MAX) == 0);
    // Exhaust every small inventory/promise pairing and cursor.
    for (int a=0; a<27; ++a) for (int b=0; b<64; ++b) for (unsigned start=0; start<6; ++start) {
        Counts s{a%3, a/3%3, a/9}, p{b%4, b/4%4, b/16};
        auto result = arcore::SelectStockDemand(s,p,start);
        std::size_t expected=3;
        for (unsigned offset=0; offset<3; ++offset) {
            auto i=(start+offset)%3;
            if (s[i]>p[i]) { expected=i; break; }
        }
        assert(result==expected);
    }
}
