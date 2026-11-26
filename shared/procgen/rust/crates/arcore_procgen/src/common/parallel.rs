//! Deterministic fork-join helpers. Work is split into contiguous index ranges
//! and results come back in range order, so callers that concatenate them get
//! the same output for any thread count.

use std::ops::Range;

/// Split `0..n` into at most `threads` contiguous ranges.
pub fn split_ranges(n: usize, threads: usize) -> Vec<Range<usize>> {
    let per = n.div_ceil(threads.clamp(1, n.max(1))).max(1);
    (0..n).step_by(per).map(|a| a..(a + per).min(n)).collect()
}

/// Run `work` on each range in parallel and return the results in range order.
pub fn par_ranges<T: Send>(n: usize, threads: usize, work: impl Fn(Range<usize>) -> T + Sync) -> Vec<T> {
    let ranges = split_ranges(n, threads);
    if ranges.len() <= 1 {
        return ranges.into_iter().map(&work).collect();
    }
    std::thread::scope(|scope| {
        let work = &work;
        let handles: Vec<_> = ranges.into_iter().map(|r| scope.spawn(move || work(r))).collect();
        handles.into_iter().map(|h| h.join().expect("worker panicked")).collect()
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ranges_cover_everything_in_order() {
        for (n, threads) in [(0, 4), (1, 4), (10, 3), (10, 64), (7, 1)] {
            let flat: Vec<usize> = split_ranges(n, threads).into_iter().flatten().collect();
            assert_eq!(flat, (0..n).collect::<Vec<_>>());
            let sums = par_ranges(n, threads, |r| r.collect::<Vec<_>>()).concat();
            assert_eq!(sums, flat);
        }
    }
}
