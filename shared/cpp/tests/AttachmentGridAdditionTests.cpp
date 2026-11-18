#include "../AttachmentGrid.h"
#include <cassert>
#include <climits>
int main() {
    using namespace gamecore;
    const std::vector<GridCell> seed{{0,0,0}};
    for (auto cell : std::vector<GridCell>{{1,0,0},{-1,0,0},{0,1,0},{0,-1,0},{0,0,1},{0,0,-1}})
        assert(CanAddAttachmentCell(seed, cell));
    assert(!CanAddAttachmentCell(seed, {0,0,0}));
    assert(!CanAddAttachmentCell(seed, {1,1,0}));
    assert(!CanAddAttachmentCell(seed, {2,0,0}));
    assert(!CanAddAttachmentCell({}, {0,0,0}));
    assert(!CanAddAttachmentCell({{0,0,0},{2,0,0}}, {1,0,0}));
    assert(!CanAddAttachmentCell({{0,0,0},{0,0,0}}, {1,0,0}));
    assert(!CanAddAttachmentCell(seed, {INT_MIN,INT_MAX,0}));
    assert(!CanAddAttachmentCell(seed, {1,0,0}, 0));
    assert(!CanAddAttachmentCell(seed, {1,0,0}, -1));
    assert(!CanAddAttachmentCell(seed, {1,0,0}, 1025));
    assert(seed.size() == 1 && SameCell(seed[0], {0,0,0}));
    std::vector<GridCell> full;
    for (int i=0; i<255; ++i) full.push_back({i,0,0});
    assert(CanAddAttachmentCell(full, {255,0,0}, 256));
    full.push_back({255,0,0});
    assert(!CanAddAttachmentCell(full, {256,0,0}, 256));
    assert(full.size() == 256);
}
