#pragma once
#include "CoreMinimal.h"
#include "AdaptiveMusic.h"
#include "Components/AudioComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Misc/App.h"
#include "Quartz/AudioMixerClockHandle.h"
#include "Quartz/QuartzSubsystem.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Sound/SoundWave.h"
#include "UObject/GCObject.h"

namespace Arcore::Unreal {
// Parse a Sonic Alchemist arcore-adaptive-v1 design.json (export or Design.json) into a
// portable score. Returns false with a reason for malformed or out-of-range designs.
inline bool ParseAdaptiveDesign(const FString& Json, GameCore::AdaptiveScore& Out, FString* Error = nullptr)
{
    auto Fail = [Error](const TCHAR* Reason) { if (Error) *Error = Reason; return false; };
    TSharedPtr<FJsonObject> D;
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json), D) || !D.IsValid()) return Fail(TEXT("Unreadable JSON"));
    FString Schema;
    if (!D->TryGetStringField(TEXT("schema"), Schema) || Schema != TEXT("arcore-adaptive-v1")) return Fail(TEXT("Expected schema arcore-adaptive-v1"));
    GameCore::AdaptiveScore S;
    double Number = 0;
    if (!D->TryGetNumberField(TEXT("bpm"), S.bpm) || !D->TryGetNumberField(TEXT("beatsPerBar"), S.beatsPerBar) ||
        !D->TryGetNumberField(TEXT("bars"), S.loopBars) || !D->TryGetNumberField(TEXT("masterDb"), Number)) return Fail(TEXT("Missing tempo, bars or master gain"));
    S.masterDb = static_cast<float>(Number);
    // Sonic Alchemist's legacy default when a design predates transitions.
    S.fadeBeats = 0.25; S.boundary = GameCore::MusicBoundary::Bar;
    const TSharedPtr<FJsonObject>* Transition = nullptr;
    if (D->TryGetObjectField(TEXT("transition"), Transition))
    {
        FString Boundary;
        (*Transition)->TryGetStringField(TEXT("boundary"), Boundary);
        (*Transition)->TryGetNumberField(TEXT("fadeBeats"), S.fadeBeats);
        if (Boundary == TEXT("immediate")) S.boundary = GameCore::MusicBoundary::Immediate;
        else if (Boundary == TEXT("beat")) S.boundary = GameCore::MusicBoundary::Beat;
        else if (Boundary == TEXT("phrase")) S.boundary = GameCore::MusicBoundary::Phrase;
        else if (Boundary != TEXT("bar")) return Fail(TEXT("Unknown transition boundary"));
    }
    const TArray<TSharedPtr<FJsonValue>>* Layers = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* States = nullptr;
    if (!D->TryGetArrayField(TEXT("layers"), Layers) || !D->TryGetArrayField(TEXT("states"), States)) return Fail(TEXT("Missing layers or states"));
    for (const auto& Layer : *Layers)
        S.layerNames.push_back(TCHAR_TO_UTF8(*Layer->AsObject()->GetStringField(TEXT("name"))));
    for (const auto& State : *States)
    {
        const TSharedPtr<FJsonObject> Item = State->AsObject();
        S.stateNames.push_back(TCHAR_TO_UTF8(*Item->GetStringField(TEXT("name"))));
        std::vector<float> Gains;
        for (const auto& Level : Item->GetArrayField(TEXT("levels")))
        {
            const TSharedPtr<FJsonObject> L = Level->AsObject();
            Gains.push_back(L->GetBoolField(TEXT("enabled")) ? static_cast<float>(L->GetNumberField(TEXT("gainDb"))) : -60.f);
        }
        S.stateGainDb.push_back(MoveTemp(Gains));
    }
    if (!S.Valid()) return Fail(TEXT("Design is outside Sonic Alchemist limits or has mismatched levels"));
    Out = MoveTemp(S);
    return true;
}

// Plays aligned looping stems as one adaptive score. Every stem is queued on a stopped Quartz
// clock and fires when the clock starts, so all voices begin on the same sample at transport 0;
// the mixer then follows the Quartz transport, which advances with rendered audio.
// The owner actor keeps the audio components alive; this object references them and the
// clock handle for GC. Callers choose the state each tick and own pause/ducking policy.
class FAdaptiveMusicPlayer : public FGCObject
{
public:
    explicit FAdaptiveMusicPlayer(GameCore::AdaptiveScore Score) : Mixer(MoveTemp(Score)) {}
    virtual ~FAdaptiveMusicPlayer() override { Stop(); }

    // Stems must be in score layer order. The clock starts after LeadSeconds so streamed
    // stems can prepare. Without an audio device or Quartz, stems start directly and the
    // mixer runs on frame time. Returns false when nothing could be started.
    bool Start(AActor& Owner, TConstArrayView<USoundWave*> Waves, FName ClockName,
        float LeadSeconds = .25f, float FadeInSeconds = -1.f)
    {
        Stop();
        Mixer.Reset(Mixer.State());
        UWorld* World = Owner.GetWorld();
        if (!World || World->GetNetMode() == NM_DedicatedServer || !FApp::CanEverRenderAudio() ||
            !Mixer.Valid() || Waves.Num() != Mixer.Definition().Layers()) return false;
        for (USoundWave* Wave : Waves) if (!Wave) return false;
        OwnerActor = &Owner;
        if (UQuartzSubsystem* Quartz = UQuartzSubsystem::Get(World))
            Clock = Quartz->CreateNewClock(&Owner, ClockName, FQuartzClockSettings(), true);
        UQuartzClockHandle* Handle = Clock;
        FOnQuartzCommandEventBP NoEvent;
        if (Handle)
        {
            FQuartzQuantizationBoundary Immediately(EQuartzCommandQuantization::None);
            Handle->SetBeatsPerMinute(&Owner, Immediately, NoEvent, Handle, static_cast<float>(Mixer.Definition().bpm));
        }
        FQuartzQuantizationBoundary OnStart(EQuartzCommandQuantization::Bar, 1.f, EQuarztQuantizationReference::TransportRelative, true);
        const float Fade = FadeInSeconds >= 0 ? FadeInSeconds : static_cast<float>(Mixer.Definition().BarSeconds());
        for (int32 Layer = 0; Layer < Waves.Num(); ++Layer)
        {
            USoundWave* Wave = Waves[Layer];
            Wave->bLooping = true;
            Wave->VirtualizationMode = EVirtualizationMode::PlayWhenSilent;
            UAudioComponent* Stem = NewObject<UAudioComponent>(&Owner);
            Stem->bAutoActivate = false;
            Stem->bAutoDestroy = false;
            Stem->bAllowSpatialization = false;
            Stem->SetSound(Wave);
            Stem->VolumeMultiplier = FMath::Max(1e-4f, Mixer.Gain(Layer));
            Stem->RegisterComponent();
            if (Handle) Stem->PlayQuantized(&Owner, Handle, OnStart, NoEvent, 0.f, Fade, 1.f, EAudioFaderCurve::SCurve);
            else Stem->FadeIn(Fade, 1.f, 0.f, EAudioFaderCurve::SCurve);
            Stems.Add(Stem);
        }
        ClockDelay = Handle ? FMath::Max(0.f, LeadSeconds) : 0.f;
        bClockRunning = false;
        return true;
    }

    // Level scales every stem (user volume times ducking); 0 silences. DesiredState -1 holds.
    void Tick(float DeltaSeconds, int32 DesiredState, float Level)
    {
        if (Stems.IsEmpty()) return;
        AActor* Owner = OwnerActor.Get();
        if (Clock && Owner)
        {
            if (!bClockRunning && (ClockDelay -= DeltaSeconds) <= 0)
            {
                UQuartzClockHandle* Handle = Clock;
                Handle->StartClock(Owner, Handle);
                bClockRunning = true;
            }
            if (bClockRunning)
            {
                const FQuartzTransportTimeStamp Stamp = Clock->GetCurrentTimestamp(Owner);
                if (Stamp.Bars > 0)
                {
                    const GameCore::AdaptiveScore& S = Mixer.Definition();
                    Mixer.AdvanceTo((Stamp.Bars - 1) * S.BarSeconds() + (FMath::Max(1, Stamp.Beat) - 1 + Stamp.BeatFraction) * S.BeatSeconds(), DesiredState);
                }
            }
        }
        else Mixer.Advance(DeltaSeconds, DesiredState);
        Level = FMath::IsFinite(Level) ? FMath::Clamp(Level, 0.f, 1.f) : 0.f;
        for (int32 Layer = 0; Layer < Stems.Num(); ++Layer) if (UAudioComponent* Stem = Stems[Layer])
        {
            // PlayWhenSilent keeps silent voices running in sync; the floor avoids zero-volume edge cases.
            const float Volume = Level > 0 ? FMath::Max(1e-4f, Mixer.Gain(Layer) * Level) : 0.f;
            if (!FMath::IsNearlyEqual(Stem->VolumeMultiplier, Volume, 1e-4f)) Stem->SetVolumeMultiplier(Volume);
        }
    }

    void Stop()
    {
        for (UAudioComponent* Stem : Stems) if (IsValid(Stem)) Stem->Stop();
        Stems.Empty();
        if (UQuartzClockHandle* Handle = Clock) if (AActor* Owner = OwnerActor.Get()) Handle->StopClock(Owner, true, Handle);
        Clock = nullptr;
        bClockRunning = false;
    }

    int32 PlayingStems() const
    {
        int32 Count = 0;
        for (const UAudioComponent* Stem : Stems) Count += IsValid(Stem) && Stem->IsPlaying();
        return Count;
    }
    bool IsClockLocked() const { return Clock != nullptr; }
    bool IsClockRunning() const { return bClockRunning; }
    const GameCore::AdaptiveMixer& State() const { return Mixer; }

    virtual void AddReferencedObjects(FReferenceCollector& Collector) override
    {
        Collector.AddReferencedObject(Clock);
        Collector.AddReferencedObjects(Stems);
    }
    virtual FString GetReferencerName() const override { return TEXT("Arcore::Unreal::FAdaptiveMusicPlayer"); }

private:
    GameCore::AdaptiveMixer Mixer;
    TObjectPtr<UQuartzClockHandle> Clock = nullptr;
    TArray<TObjectPtr<UAudioComponent>> Stems;
    TWeakObjectPtr<AActor> OwnerActor;
    float ClockDelay = 0;
    bool bClockRunning = false;
};
}
