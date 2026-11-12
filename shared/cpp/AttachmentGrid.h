#pragma once
#include <vector>
#include <cstdlib>

namespace gamecore {
struct GridCell { int x, y, z; };
inline bool SameCell(GridCell a, GridCell b) { return a.x == b.x && a.y == b.y && a.z == b.z; }
// Bounded face-connected graph. Empty, duplicate and out-of-range cells are invalid.
// No allocations proportional to coordinates; maximum 256 cells bounds graph traversal.
inline bool ValidAttachmentGrid(const std::vector<GridCell>& cells, int radius = 16) {
    if (cells.empty() || cells.size() > 256 || radius < 0 || radius > 1024) return false;
    for (size_t i = 0; i < cells.size(); ++i) {
        const auto a = cells[i];
        if (a.x < -radius || a.x > radius || a.y < -radius || a.y > radius || a.z < -radius || a.z > radius) return false;
        for (size_t j = 0; j < i; ++j) if (SameCell(a, cells[j])) return false;
    }
    std::vector<bool> seen(cells.size(), false);
    std::vector<size_t> queue{0}; seen[0] = true;
    for (size_t head = 0; head < queue.size(); ++head) {
        const auto a = cells[queue[head]];
        for (size_t j = 0; j < cells.size(); ++j) {
            const auto b = cells[j];
            if (!seen[j] && std::abs(a.x-b.x)+std::abs(a.y-b.y)+std::abs(a.z-b.z) == 1) {
                seen[j] = true; queue.push_back(j);
            }
        }
    }
    return queue.size() == cells.size();
}
// Transaction preview: original and remaining assemblies must both be valid.
// Root ownership and refunds belong to the consumer. Never mutates the input.
inline bool CanRemoveAttachmentCell(const std::vector<GridCell>& cells, GridCell removed, int radius = 16) {
    if (!ValidAttachmentGrid(cells, radius)) return false;
    std::vector<GridCell> remaining;
    bool found = false;
    for (auto cell : cells) {
        if (SameCell(cell, removed)) found = true;
        else remaining.push_back(cell);
    }
    return found && ValidAttachmentGrid(remaining, radius);
}
}
