#include "../GridRoute.h"
#include <cassert>
#include <cstdlib>

int main()
{
    using ArcoreGameCore::FindGridRoute;
    using ArcoreGameCore::TraceGridRoute;
    assert(TraceGridRoute(3,1,{2,1,0},0,2).size()==3);
    assert(TraceGridRoute(3,1,{2,-1,0},0,2).empty());
    assert(TraceGridRoute(3,1,{0,1,0},1,0).empty()); // deterministic step reaches wrong zero
    assert(TraceGridRoute(3,1,{0,1,0},1,2).empty()==false);
    assert(TraceGridRoute(3,1,{99,1,0},0,2).empty());
    assert(TraceGridRoute(3,1,{2,1,0},-1,2).empty());
    assert(TraceGridRoute(3,1,{2,1,0},0,3).empty());
    assert(TraceGridRoute(3,1,{2,1,0},0,1).empty());
    assert(TraceGridRoute(0,1,{},0,0).empty());
    assert(FindGridRoute(0,3,{},0,1).empty());
    assert(FindGridRoute(3,3,{0},0,1).empty());
    std::vector<unsigned char> Cells(9,0);
    assert(FindGridRoute(3,3,Cells,-1,8).empty());
    assert(FindGridRoute(3,3,Cells,0,9).empty());
    assert(FindGridRoute(3,3,Cells,2,3).size()==4);
    // Exhaust all 3x3 obstacle configurations and endpoint pairs. Compare against
    // independently relaxed distances, checking adjacency and obstacle avoidance.
    for (int Mask=0; Mask<512; ++Mask)
    {
        for (int I=0; I<9; ++I) Cells[I]=(Mask>>I)&1;
        for (int Start=0; Start<9; ++Start)
        {
            int Distance[9]; for (int& D:Distance) D=999;
            if (!Cells[Start]) Distance[Start]=0;
            for (int Pass=0; Pass<9; ++Pass)
                for (int A=0; A<9; ++A) for (int B=0; B<9; ++B)
                    if (!Cells[A] && !Cells[B] && std::abs(A%3-B%3)+std::abs(A/3-B/3)==1)
                        Distance[B]=std::min(Distance[B],Distance[A]+1);
            for (int Goal=0; Goal<9; ++Goal)
            {
                auto Route=FindGridRoute(3,3,Cells,Start,Goal);
                auto Field=ArcoreGameCore::BuildGridDistanceField(3,3,Cells,Goal);
                auto Traced=ArcoreGameCore::TraceGridRoute(3,3,Field,Start,Goal);
                assert(Traced.size()==Route.size());
                if (!Traced.empty()) {
                    assert(Traced.front()==Start && Traced.back()==Goal);
                    for (std::size_t I=1; I<Traced.size(); ++I) {
                        assert(!Cells[Traced[I]]);
                        assert(std::abs(Traced[I]%3-Traced[I-1]%3)+std::abs(Traced[I]/3-Traced[I-1]/3)==1);
                    }
                }
                if (Cells[Goal]) assert(Field.empty());
                else
                {
                    assert(Field[Start] == (Distance[Goal]==999 ? -1 : Distance[Goal]));
                    int Cursor=Start, Steps=0;
                    while (Cursor!=Goal && Cursor>=0 && Steps<10)
                    { Cursor=ArcoreGameCore::NextGridStep(3,3,Field,Cursor); ++Steps; }
                    if (Distance[Goal]!=999) assert(Cursor==Goal && Steps==Distance[Goal]);
                    else assert(Cursor==-1);
                }
                assert(Route.empty()==(Distance[Goal]==999));
                if (Route.empty()) continue;
                assert(Route.front()==Start && Route.back()==Goal);
                assert(static_cast<int>(Route.size())==Distance[Goal]+1);
                for (size_t I=0; I<Route.size(); ++I)
                {
                    assert(!Cells[Route[I]]);
                    if (I) assert(std::abs(Route[I]%3-Route[I-1]%3)+std::abs(Route[I]/3-Route[I-1]/3)==1);
                }
            }
        }
    }
    assert(ArcoreGameCore::BuildGridDistanceField(0,3,Cells,0).empty());
    assert(ArcoreGameCore::BuildGridDistanceField(3,3,Cells,9).empty());
    assert(ArcoreGameCore::NextGridStep(3,3,{},0)==-1);
    assert(ArcoreGameCore::NextGridStep(3,1,{2,-1,0},0)==-1);
}
