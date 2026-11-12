#pragma once
#include <cmath>
#include <cstddef>
#include <vector>

// Engine-neutral structural connectivity; edges are undirected joints.
namespace GameCore
{
struct SupportNode { float Health = 100.f; bool Anchored = false; bool Detached = false; };
struct SupportEdge { std::size_t A; std::size_t B; };
class SupportGraph
{
public:
    bool Configure(const std::vector<SupportNode>& InNodes, const std::vector<SupportEdge>& InEdges)
    {
        for (const auto& N : InNodes)
            if (!std::isfinite(N.Health) || N.Health <= 0.f || N.Detached) return false;
        for (const auto& E : InEdges)
            if (E.A >= InNodes.size() || E.B >= InNodes.size() || E.A == E.B) return false;
        Initial = InNodes; Nodes = InNodes; Edges = InEdges; Resolve(); return true;
    }
    bool Damage(std::size_t Index, float Amount)
    {
        if (Index >= Nodes.size() || !std::isfinite(Amount) || Amount <= 0.f || Nodes[Index].Detached) return false;
        auto& N = Nodes[Index]; N.Health = Amount >= N.Health ? 0.f : N.Health - Amount;
        Resolve(); return true;
    }
    void Reset() { Nodes = Initial; Resolve(); }
    const std::vector<SupportNode>& GetNodes() const { return Nodes; }
private:
    void Resolve()
    {
        std::vector<bool> Reached(Nodes.size(), false);
        std::vector<std::size_t> Queue;
        for (std::size_t I = 0; I < Nodes.size(); ++I)
            if (Nodes[I].Anchored && Nodes[I].Health > 0.f && !Nodes[I].Detached)
            { Reached[I] = true; Queue.push_back(I); }
        for (std::size_t Q = 0; Q < Queue.size(); ++Q)
            for (const auto& E : Edges)
            {
                const auto Other = E.A == Queue[Q] ? E.B : E.B == Queue[Q] ? E.A : Nodes.size();
                if (Other < Nodes.size() && !Reached[Other] && Nodes[Other].Health > 0.f && !Nodes[Other].Detached)
                { Reached[Other] = true; Queue.push_back(Other); }
            }
        for (std::size_t I = 0; I < Nodes.size(); ++I) Nodes[I].Detached = !Reached[I];
    }
    std::vector<SupportNode> Nodes, Initial;
    std::vector<SupportEdge> Edges;
};
}
