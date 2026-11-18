# StockDemand 0.1.0

`arcore::SelectStockDemand` selects the first available, unpromised catalog item
in circular order from `start`. The return value is the catalog size when none
is available. Arrays are read-only, counts are signed 32-bit, negative counts
are ineligible, and selection uses comparisons rather than overflowing subtraction.
The catalog must be nonempty. Arbitrarily large start indices are normalized.

Consumers snapshot their available inventory, count outstanding one-unit orders,
and advance the cursor after successful admission. Selection does not reserve,
transfer or consume inventory. Serialize admission with queue mutation. Recompute
promises from the live queue after fulfillment or cancellation. Exclude stolen or
otherwise unavailable stock. Subsequent losses may still make existing orders
unfulfillable; recovery, deadlines, UI and persistence remain consumer policy.

Initial consumer: Dungeon Dash Market (Unreal 5.8.4 / Win64). Portable boundary
tests are in `tests/StockDemandTests.cpp`; consumer runtime evidence is separate.

Validation on November 12, 2026: MSVC 14.44 C++14 standalone assertions passed, including 10,368 small-state combinations. Dungeon Dash Market built with the locked header; three Unreal automation tests, original loop smoke, rendered demand smoke and hazard smoke passed. Evidence: `X:/Projects/Games/Dungeon-Dash-Market/Docs/DEMAND_VALIDATION.json`. No visual/manual or packaged acceptance is claimed. The full registry audit remains blocked by pre-existing cooperative-task source/hash drift; selected module sync/check passed.
