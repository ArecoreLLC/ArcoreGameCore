#include "../AttachmentGrid.h"
#include <cassert>
#include <climits>
int main() {
    using namespace gamecore;
    const std::vector<GridCell> chain{{0,0,0},{1,0,0},{2,0,0}};
    assert(CanRemoveAttachmentCell(chain, {2,0,0}));
    assert(!CanRemoveAttachmentCell(chain, {1,0,0}));
    assert(!CanRemoveAttachmentCell(chain, {3,0,0}));
    assert(chain.size() == 3);
    assert(!CanRemoveAttachmentCell({{0,0,0}}, {0,0,0}));
    assert(!CanRemoveAttachmentCell({}, {0,0,0}));
    assert(!CanRemoveAttachmentCell({{0,0,0},{0,0,0}}, {0,0,0}));
    assert(!CanRemoveAttachmentCell({{0,0,0},{INT_MAX,0,0}}, {INT_MAX,0,0}));
    assert(!CanRemoveAttachmentCell({{0,0,0},{2,0,0}}, {2,0,0}));
    assert(!CanRemoveAttachmentCell(chain, {2,0,0}, -1));
    const std::vector<GridCell> loop{{0,0,0},{1,0,0},{1,1,0},{0,1,0}};
    assert(CanRemoveAttachmentCell(loop, {1,0,0}));
}
