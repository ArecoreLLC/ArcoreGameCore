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
  LastTime = now; ActiveUntil = now + active; ReadyAt = now + recovery; Started = true; return true;
 }
 double ActiveRemaining(double now) const { return Active(now) ? ActiveUntil-now : 0.0; }
 bool Active(double now) const { return std::isfinite(now) && now >= LastTime && now < ActiveUntil; }
 double Remaining(double now) const { return std::isfinite(now) && now < ReadyAt ? ReadyAt-now : 0.0; }
 // Idle, invalid and pre-start queries return zero; completed windows return one.
 // A successfully started zero-duration action is immediately complete.
 double Progress(double now) const {
  if (!Started || !std::isfinite(now) || now < LastTime) return 0.0;
  if (now >= ActiveUntil) return 1.0;
  return (now - LastTime) / (ActiveUntil - LastTime);
 }
 // Elapsed fraction of the whole action/recovery interval, not just active work.
 double RecoveryProgress(double now) const {
  if (!Started || !std::isfinite(now) || now < LastTime) return 0.0;
  if (now >= ReadyAt) return 1.0;
  return (now - LastTime) / (ReadyAt - LastTime);
 }
 // Absolute caller-clock deadlines; idle/reset returns zero. Read-only for adapters.
 double ActiveDeadline() const { return ActiveUntil; }
 double ReadyDeadline() const { return ReadyAt; }
 void Reset() { ReadyAt=ActiveUntil=LastTime=0.0; Started=false; }
private:
 bool Started = false;
};
}
