#pragma once
#include <algorithm>
#include <cmath>
namespace GameCore
{
// Work is contributed only by present workers. No time is banked while blocked.
class CooperativeTask
{
public:
    explicit CooperativeTask(double requiredWork = 1.0, unsigned minimumWorkers = 1)
        : Required(std::isfinite(requiredWork) && requiredWork > 0 ? requiredWork : 1.0),
          Minimum(std::max(1u, minimumWorkers)) {}
    bool Advance(double seconds, unsigned workers, double workPerWorker = 1.0)
    {
        if (!CanWork(workers) || !std::isfinite(seconds) || seconds <= 0 ||
            !std::isfinite(workPerWorker) || workPerWorker <= 0) return false;
        const double work = seconds * workers * workPerWorker;
        Done += std::min(Required - Done, work);
        return Complete(); // true only on the completion edge
    }
    // Readiness is separate from progress: a completed lift can still need escorts.
    unsigned RequiredWorkers() const { return Minimum; }
    unsigned MissingWorkers(unsigned workers) const { return workers < Minimum ? Minimum - workers : 0; }
    bool CanWork(unsigned workers) const { return !Complete() && MissingWorkers(workers) == 0; }
    bool Complete() const { return Done >= Required; }
    double Fraction() const { return Done / Required; }
    void Reset() { Done = 0; }
private:
    double Required;
    unsigned Minimum;
    double Done = 0;
};
}
