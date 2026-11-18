# Jump grace 0.1.0
Portable C++ jump request admission, default 100 ms ledge grace and 120 ms input buffer.
Call Update once per simulation tick with grounded state, a press edge and a monotonic seconds clock. A true result consumes the request; the adapter must execute the jump immediately. Ground-to-air-to-ground transition rearms; repeated grounded frames cannot double jump. Released buttons do not cancel a buffered tap. Reset on teleport/restart. Invalid/reversed clocks do not mutate state. Zero windows admit same-frame events only; invalid tuning clamps to zero.
Engine adapter owns collision, velocities, focus and press edges. No networking or second-engine parity claim. Echo-Forge supplies engine automation and traversal evidence.
