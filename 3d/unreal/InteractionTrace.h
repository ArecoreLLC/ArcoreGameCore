#pragma once
#include "CoreMinimal.h"
#include "Engine/World.h"

namespace Arcore::Unreal
{
struct InteractionFocus
{
    FHitResult Hit;
    bool bInReach = false;
};

// Return the first blocking surface, including non-interactable occluders.
// Consumers filter actor type AFTER tracing, never by ignoring world blockers.
// Distances are measured from the view origin to the surface in world units.
inline InteractionFocus TraceInteraction(UWorld* World, const FVector& Origin,
    const FVector& Direction, double Reach, double PreviewRange,
    const AActor* Ignore = nullptr, ECollisionChannel Channel = ECC_Visibility)
{
    InteractionFocus Result;
    if (!World || Origin.ContainsNaN() || Direction.ContainsNaN()
        || !FMath::IsFinite(Reach) || !FMath::IsFinite(PreviewRange)
        || Reach < 0 || PreviewRange <= 0 || Reach > PreviewRange) return Result;
    const FVector Unit = Direction.GetSafeNormal();
    if (Unit.IsNearlyZero() || Unit.ContainsNaN()) return Result;
    const FVector End = Origin + Unit * PreviewRange;
    if (End.ContainsNaN()) return Result;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(ArcoreInteraction), false);
    if (Ignore) Params.AddIgnoredActor(Ignore);
    if (World->LineTraceSingleByChannel(Result.Hit, Origin, End, Channel, Params))
        Result.bInReach = !Result.Hit.bStartPenetrating && Result.Hit.Distance <= Reach;
    return Result;
}
}
