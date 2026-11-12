#include "../StockLedger.h"
#include <cassert>
#include <climits>
#include <random>

int main() {
    arcore::StockLedger<3> source(100), target(100);
    assert(source.Add(0,100));
    assert(!source.Add(0,1));
    assert(!source.Add(3,1));
    assert(!source.TransferTo(source,0,1));
    assert(!source.TransferTo(target,0,-1));
    assert(!source.TransferTo(target,0,101));
    assert(source.Total() == 100 && target.Total() == 0);
    std::mt19937 random(42);
    for (int n = 0; n < 10000; ++n) {
        const int amount = static_cast<int>(random()%110);
        if (random()%2) source.TransferTo(target,0,amount); else target.TransferTo(source,0,amount);
        assert(source.Total()+target.Total() == 100);
        assert(source.Total() >= 0 && target.Total() >= 0);
    }
    arcore::StockLedger<3> stock;
    assert(stock.Add(2,2));
    std::int32_t wallet = INT_MAX;
    assert(!stock.Sell(2,1,1,wallet));
    assert(wallet == INT_MAX && stock.Count(2) == 2);
    wallet = 0;
    assert(!stock.Sell(2,2,INT_MAX,wallet));
    assert(!stock.Sell(2,1,0,wallet));
    assert(!stock.Sell(2,1,-1,wallet));
    assert(stock.Sell(2,2,10,wallet));
    assert(wallet == 20 && stock.Total() == 0);
    assert(!stock.Sell(2,1,10,wallet));
    arcore::StockLedger<1> empty(-1);
    assert(!empty.Add(0));
    arcore::StockLedger<3> shelf(12), escrow(1);
    assert(shelf.Add(1,2));
    assert(shelf.TransferTo(escrow,1,1));
    assert(!shelf.TransferTo(escrow,1,1));
    assert(shelf.Total()+escrow.Total() == 2);
    assert(!escrow.Remove(3));
    assert(!escrow.Remove(1,0));
    assert(!escrow.Remove(1,-1));
    assert(!escrow.Remove(1,2));
    assert(escrow.Count(1) == 1);
    assert(escrow.TransferTo(shelf,1,1));
    assert(shelf.Count(1) == 2 && escrow.Total() == 0);
    assert(shelf.TransferTo(escrow,1,1));
    assert(escrow.Remove(1));
    assert(!escrow.Remove(1));
    assert(shelf.Total() == 1 && escrow.Total() == 0);
    return 0;
}
