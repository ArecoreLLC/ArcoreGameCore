#pragma once
#include <algorithm>
#include <vector>

namespace ArcoreGameCore
{
// Reverse BFS for many agents sharing one goal. -1 means blocked/unreachable.
// Rebuild after occupancy changes; invalid input returns an empty field.
inline std::vector<int> BuildGridDistanceField(int Width, int Height,
    const std::vector<unsigned char>& Blocked, int Goal)
{
    if (Width <= 0 || Height <= 0 || Width > 4096 || Height > 4096 ||
        Blocked.size() != static_cast<std::size_t>(Width) * Height ||
        Goal < 0 || Goal >= Width * Height || Blocked[Goal]) return {};
    std::vector<int> Distance(Blocked.size(), -1), Queue{Goal};
    Distance[Goal] = 0;
    for (std::size_t Head = 0; Head < Queue.size(); ++Head)
    {
        const int Cell = Queue[Head], X = Cell % Width, Y = Cell / Width;
        const int Neighbours[] = {X+1<Width ? Cell+1 : -1, Y+1<Height ? Cell+Width : -1,
            Y>0 ? Cell-Width : -1, X>0 ? Cell-1 : -1};
        for (int Next : Neighbours)
            if (Next >= 0 && !Blocked[Next] && Distance[Next] < 0)
            { Distance[Next] = Distance[Cell] + 1; Queue.push_back(Next); }
    }
    return Distance;
}

// Deterministic right/down/up/left tie break. At goal returns current cell;
// invalid, unreachable or inconsistent local field returns -1.
inline int NextGridStep(int Width, int Height, const std::vector<int>& Distance, int Cell)
{
    if (Width <= 0 || Height <= 0 || Width > 4096 || Height > 4096 ||
        Distance.size() != static_cast<std::size_t>(Width) * Height ||
        Cell < 0 || Cell >= Width * Height || Distance[Cell] < 0) return -1;
    if (Distance[Cell] == 0) return Cell;
    const int X=Cell%Width, Y=Cell/Width;
    const int Neighbours[] = {X+1<Width ? Cell+1 : -1, Y+1<Height ? Cell+Width : -1,
        Y>0 ? Cell-Width : -1, X>0 ? Cell-1 : -1};
    for (int Next : Neighbours)
        if (Next >= 0 && Distance[Next] == Distance[Cell]-1) return Next;
    return -1;
}

// Trace a field built for Goal, including endpoints. Reject partial paths,
// wrong goals and malformed fields; work is bounded by the number of cells.
inline std::vector<int> TraceGridRoute(int Width, int Height,
    const std::vector<int>& Distance, int Start, int Goal)
{
    if (NextGridStep(Width, Height, Distance, Start) < 0 ||
        Goal < 0 || Goal >= static_cast<int>(Distance.size()) || Distance[Goal] != 0 ||
        Distance[Start] >= static_cast<int>(Distance.size())) return {};
    std::vector<int> Route;
    int Cell = Start;
    for (std::size_t I = 0; I < Distance.size(); ++I)
    {
        Route.push_back(Cell);
        if (Cell == Goal) return Route;
        const int Next = NextGridStep(Width, Height, Distance, Cell);
        if (Next < 0 || Next == Cell) return {};
        Cell = Next;
    }
    return {};
}

// Four-neighbour shortest route including endpoints; empty for invalid/unreachable.
inline std::vector<int> FindGridRoute(int Width, int Height,
    const std::vector<unsigned char>& Blocked, int Start, int Goal)
{
    if (Width <= 0 || Height <= 0 || Width > 4096 || Height > 4096 ||
        Blocked.size() != static_cast<size_t>(Width) * Height ||
        Start < 0 || Goal < 0 || Start >= Width * Height || Goal >= Width * Height ||
        Blocked[Start] || Blocked[Goal]) return {};
    std::vector<int> Parent(Blocked.size(), -1), Queue;
    Parent[Start] = Start;
    Queue.push_back(Start);
    for (size_t Head = 0; Head < Queue.size() && Parent[Goal] == -1; ++Head)
    {
        const int Cell = Queue[Head], X = Cell % Width, Y = Cell / Width;
        const int Neighbours[] = {X + 1 < Width ? Cell + 1 : -1,
            Y + 1 < Height ? Cell + Width : -1, Y > 0 ? Cell - Width : -1,
            X > 0 ? Cell - 1 : -1};
        for (int Next : Neighbours)
            if (Next >= 0 && !Blocked[Next] && Parent[Next] == -1)
            { Parent[Next] = Cell; Queue.push_back(Next); }
    }
    if (Parent[Goal] == -1) return {};
    std::vector<int> Route;
    for (int Cell = Goal;; Cell = Parent[Cell])
    { Route.push_back(Cell); if (Cell == Start) break; }
    std::reverse(Route.begin(), Route.end());
    return Route;
}
}
