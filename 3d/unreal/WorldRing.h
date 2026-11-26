#pragma once
#include "CoreMinimal.h"
#include "GameFramework/HUD.h"

namespace Arcore::Unreal {
// Canvas-backed planar ring: works without development-only debug drawing.
// Caller owns lifetime, color, world plane and HUD draw order. No retained objects.
inline void DrawWorldArc(AHUD& hud, const FVector& center, float radius,
    float startRadians, float sweepRadians, FLinearColor color,
    float thickness = 2.f, int32 segments = 48)
{
    if (center.ContainsNaN() || !FMath::IsFinite(radius) || radius <= 0 ||
        !FMath::IsFinite(thickness) || thickness <= 0 ||
        !FMath::IsFinite(startRadians) || !FMath::IsFinite(sweepRadians) ||
        FMath::Abs(sweepRadians) > 2.f * PI || sweepRadians == 0) return;
    segments = FMath::Clamp(segments, 8, 128);
    FVector previous = hud.Project(center + FVector(FMath::Cos(startRadians)*radius, FMath::Sin(startRadians)*radius, 0));
    for (int32 i = 1; i <= segments; ++i) {
        const float angle = startRadians + sweepRadians * i / segments;
        const FVector next = hud.Project(center + FVector(FMath::Cos(angle)*radius, FMath::Sin(angle)*radius, 0));
        if (previous.Z > 0 && next.Z > 0)
            hud.DrawLine(previous.X, previous.Y, next.X, next.Y, color, thickness);
        previous = next;
    }
}
inline void DrawWorldRing(AHUD& hud, const FVector& center, float radius,
    FLinearColor color, float thickness = 2.f, int32 segments = 48)
{
    DrawWorldArc(hud, center, radius, 0.f, 2.f * PI, color, thickness, segments);
}
// A normalized world-space meter. Invalid progress draws nothing; finite values
// clamp to [0,1]. The caller owns meaning, palette, timing and accessibility text.
inline void DrawWorldProgressRing(AHUD& hud, const FVector& center, float radius,
    float progress, FLinearColor foreground, FLinearColor track,
    float thickness = 2.f, int32 segments = 48)
{
    if (!FMath::IsFinite(progress)) return;
    DrawWorldRing(hud, center, radius, track, thickness, segments);
    DrawWorldArc(hud, center, radius, -PI / 2.f,
        2.f * PI * FMath::Clamp(progress, 0.f, 1.f), foreground, thickness, segments);
}
}
