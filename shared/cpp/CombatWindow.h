#pragma once
#include <cmath>
namespace GameCore {
// Caller supplies monotonic simulation time, in seconds. A window is [start,end).
// Invalid times/durations never mutate state. Reset for a new simulation/run.
class CombatWindow {
 double ReadyAt = 0.0, ActiveUntil = 0.0, LastTime = 0.0;
public:
 bool TryStart(double now, double active, double recovery) {
  if (!std::isfinite(now) || !std::isfinite(active) || !std::isfinite(recovery)
      || now < LastTime || active < 0 || recovery < active || now < ReadyAt
      || !std::isfinite(now + recovery)) return false;
  LastTime = now; ActiveUntil = now + active; ReadyAt = now + recovery; return true;
 }
 bool Active(double now) const { return std::isfinite(now) && now >= LastTime && now < ActiveUntil; }
 double Remaining(double now) const { return std::isfinite(now) && now < ReadyAt ? ReadyAt-now : 0.0; }
 void Reset() { ReadyAt=ActiveUntil=LastTime=0.0; }
};
}
