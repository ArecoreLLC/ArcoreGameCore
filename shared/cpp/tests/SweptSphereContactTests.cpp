#include "../SweptSphereContact.h"
#include <cassert>
#include <limits>
int main()
{
    using GameCore::SweptSphereContact;
    assert(SweptSphereContact({-400,0,0},{400,0,0},150));
    assert(SweptSphereContact({-400,150,0},{400,150,0},150));
    assert(!SweptSphereContact({-400,151,0},{400,151,0},150));
    assert(SweptSphereContact({150,0,0},{300,0,0},150));
    assert(SweptSphereContact({0,0,0},{0,0,0},0));
    assert(!SweptSphereContact({0,0,2},{0,0,2},1));
    assert(!SweptSphereContact({300,0,0},{400,0,0},150));
    assert(!SweptSphereContact({0,0,0},{0,0,0},-1));
    assert(!SweptSphereContact({0,0,0},{0,0,0},std::numeric_limits<double>::infinity()));
    assert(!SweptSphereContact({NAN,0,0},{0,0,0},1));
    // Synthetic tiny sensor and large-coordinate crossing: no game units assumed.
    assert(SweptSphereContact({-.001,0,0},{.001,0,0},.0001));
    assert(SweptSphereContact({-1e308,0,0},{1e308,0,0},1));
}
