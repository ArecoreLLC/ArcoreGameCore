# Bounded order admission 0.1.0

Engine-neutral C++17 policy for commands that either replace current work or append
to a bounded pending queue. Call `GameCore::AdmitOrder(append, pending, capacity)`
before changing any destination, target, path or queue. `RejectFull` must leave all
of those unchanged. An explicit replacement remains permitted at capacity.
Zero capacity rejects every append; counts beyond capacity also reject without
arithmetic overflow. The caller owns authorization, payload validation, queue
storage, feedback, and dispatch. This policy does not execute orders or make a
batch atomic. Consumers decide whether partial group admission is appropriate.

Compile `tests/BoundedOrderAdmissionTests.cpp` as C++17 or later; static assertions
cover empty, last-slot, full, over-capacity, zero-capacity and maximum-size counts.
Scorched Frontier additionally exercises real unit queues in editor and packaged
UI smoke fixtures. Test sources alone are not evidence of a fresh test run.
