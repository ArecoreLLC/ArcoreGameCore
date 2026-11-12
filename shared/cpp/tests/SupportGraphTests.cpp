#include "SupportGraph.h"
#include <cassert>
#include <limits>
#include <iostream>

int main()
{
    GameCore::SupportGraph Graph;
    assert(Graph.Configure({{100,true,false},{100,false,false},{100,false,false}},{{0,1},{1,2}}));
    assert(Graph.Damage(0,25));
    assert(!Graph.GetNodes()[2].Detached);
    assert(Graph.Damage(0,75));
    assert(Graph.GetNodes()[2].Detached);
    assert(!Graph.Damage(2,25));
    Graph.Reset();
    assert(Graph.GetNodes()[0].Health == 100 && !Graph.GetNodes()[2].Detached);
    Graph.Damage(1,100);
    assert(!Graph.GetNodes()[0].Detached && Graph.GetNodes()[2].Detached);
    assert(Graph.Configure({{100,true,false},{100,true,false},{100,false,false}},{{0,2},{1,2}}));
    Graph.Damage(0,100);
    assert(!Graph.GetNodes()[2].Detached);
    Graph.Damage(1,1000);
    assert(Graph.GetNodes()[2].Detached && Graph.GetNodes()[1].Health == 0);
    Graph.Reset();
    assert(!Graph.Damage(99,1) && !Graph.Damage(0,-1) && !Graph.Damage(0,0));
    assert(!Graph.Damage(0,std::numeric_limits<float>::infinity()));
    assert(!Graph.Damage(0,std::numeric_limits<float>::quiet_NaN()));
    assert(!Graph.Configure({{100,true,false}},{{0,9}}));
    assert(!Graph.Configure({{100,true,false}},{{0,0}}));
    assert(!Graph.Configure({{0,true,false}},{}));
    assert(Graph.GetNodes().size() == 3 && Graph.GetNodes()[0].Health == 100);
    assert(Graph.Configure({{100,false,false},{100,false,false},{100,false,false}},{{0,1},{1,2},{2,0}}));
    assert(Graph.GetNodes()[0].Detached && Graph.GetNodes()[1].Detached && Graph.GetNodes()[2].Detached);
    assert(Graph.Configure({{100,true,false},{100,false,false},{100,false,false}},{{0,1},{1,2},{2,0},{0,1}}));
    assert(!Graph.GetNodes()[2].Detached);
    assert(Graph.Configure({},{}));
    Graph.Reset();
    assert(!Graph.Damage(0,1));
    std::cout << "SupportGraph regression checks passed\n";
}
