#pragma once
#include "CoreMinimal.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"

namespace Arcore { namespace Unreal {
// Create once during initialization, then retain the returned instance for updates.
// The caller owns a cook-referenced parent exposing the named vector parameter.
inline UMaterialInstanceDynamic* CreateTint(UStaticMeshComponent& mesh,
    UMaterialInterface* parent, const FLinearColor& color, FName parameter = TEXT("Color"))
{
    if (!parent || !FMath::IsFinite(color.R) || !FMath::IsFinite(color.G) ||
        !FMath::IsFinite(color.B) || !FMath::IsFinite(color.A)) return nullptr;
    auto* material = UMaterialInstanceDynamic::Create(parent, &mesh);
    if (!material) return nullptr;
    material->SetVectorParameterValue(parameter, color);
    mesh.SetMaterial(0, material);
    return material;
}
}}
