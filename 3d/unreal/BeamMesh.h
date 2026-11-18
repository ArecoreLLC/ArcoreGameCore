#pragma once
#include "CoreMinimal.h"
#include "Components/StaticMeshComponent.h"

// Unreal adapter. Mesh must be a centered cylinder, 100 units long along local Z,
// with a 100-unit diameter (the engine BasicShapes/Cylinder convention).
namespace Arcore { namespace Unreal {
inline void ConfigureBeam(UStaticMeshComponent& Mesh)
{
    Mesh.SetMobility(EComponentMobility::Movable);
    Mesh.SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Mesh.SetGenerateOverlapEvents(false);
    Mesh.SetCanEverAffectNavigation(false);
    Mesh.SetCastShadow(false);
    Mesh.SetVisibility(false);
}

// Invalid/degenerate segments hide the old visual instead of leaving stale light.
inline bool UpdateBeam(UStaticMeshComponent& Mesh, const FVector& Start,
    const FVector& End, double Radius)
{
    const FVector Delta=End-Start;
    const double Length=Delta.Size();
    if (Start.ContainsNaN() || End.ContainsNaN() || !FMath::IsFinite(Length) ||
        Length < 1.e-4 || !FMath::IsFinite(Radius) || Radius <= 0)
    {
        Mesh.SetVisibility(false);
        return false;
    }
    Mesh.SetWorldLocation(Start+Delta*.5);
    Mesh.SetWorldRotation(FQuat::FindBetweenNormals(FVector::UpVector,Delta/Length));
    Mesh.SetWorldScale3D(FVector(Radius/50.,Radius/50.,Length/100.));
    Mesh.SetVisibility(true);
    return true;
}
}}
