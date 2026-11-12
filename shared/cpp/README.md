# Portable C++ rules

Browse the portable rules with `python tools/gamecore.py modules` from the repository
root. The [module registry](../modules.json) records versions, source hashes,
documentation, tests and consumers. Follow the [installation and common build/test
guide](../module-registry.md) to install pinned copies in a consumer.

## Stock ledger

Version 0.2.0 adds `Remove(item, quantity)` for consumption or loss without currency. It rejects invalid IDs, nonpositive quantities and insufficient stock without mutation. Model temporary ownership with a separate ledger: transfer into it, then transfer back for recovery or remove once on loss. Tests cover full temporary storage, recovery, invalid removal and duplicate removal. Existing transfer/sale behavior is unchanged.

`StockLedger.h` is a header-only C++14 fixed-catalog inventory and sale primitive, independent of Unreal and Godot. Consumers own stable catalog ordering, authority, prices, save schemas and IO. Invalid IDs, nonpositive quantities/prices, capacity failures, self-transfers and wallet overflow fail without mutation. Transfer and sale are synchronous, not thread-safe or durable transactions.

Install a pinned local header through the module workflow above; shipped binaries need no sibling checkout. Keep engine adapters in consumers. Dungeon Dash Market is the first Unreal consumer, with automation coverage for capacity, failed-transfer atomicity, invalid inputs, overflow, consumption and conservation. Broader engine parity is not claimed.

Standalone regression (C++14 or newer, assertions enabled): compile and run `tests/StockLedgerTests.cpp` with your host C++ compiler. It includes 10,000 deterministic randomized transfers to check conservation. For example: `c++ -std=c++14 tests/StockLedgerTests.cpp -o ledger-tests` then `./ledger-tests`. Do not define `NDEBUG` for this test.

