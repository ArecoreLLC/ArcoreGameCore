#pragma once
#include <cmath>
namespace GameCore {
// Refresh-on-add stacks sharing one expiry. Mutations require monotonic seconds.
// Reads are pure; end time is exclusive. Invalid mutations preserve all state.
class TimedStacks {
 int CountValue = 0;
 double ExpiresAt = 0, LastMutation = 0;
public:
 int Count(double now) const {
  return std::isfinite(now) && now >= LastMutation && now < ExpiresAt ? CountValue : 0;
 }
 bool Add(double now, double duration, int cap) {
  if (!std::isfinite(now) || now < LastMutation || !std::isfinite(duration)
      || duration <= 0 || cap <= 0 || !std::isfinite(now + duration)) return false;
  const int current = Count(now);
  CountValue = current >= cap ? cap : current + 1;
  ExpiresAt = now + duration; LastMutation = now; return true;
 }
 int Consume(double now) {
  if (!std::isfinite(now) || now < LastMutation) return 0;
  const int result = Count(now);
  CountValue = 0; ExpiresAt = now; LastMutation = now; return result;
 }
 void Reset() { CountValue = 0; ExpiresAt = LastMutation = 0; }
};
}
