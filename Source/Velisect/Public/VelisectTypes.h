#pragma once

#include "CoreMinimal.h"
#include "VelisectTypes.generated.h"

class USkeletalMeshComponent;
class UAnimSequenceBase;

/** A locomotion clip plus the ground speed (cm/s) it was authored at, used to scale playback. */
USTRUCT(BlueprintType)
struct FVelisectLocoClip
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	TSoftObjectPtr<UAnimSequenceBase> Anim;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	float NaturalSpeed = 300.f;
};

/** A first-person clip: the arms' take and the rifle's matching take (magazines, bolt), played together. */
USTRUCT(BlueprintType)
struct FVelisectViewmodelClip
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	TSoftObjectPtr<UAnimSequenceBase> Arms;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	TSoftObjectPtr<UAnimSequenceBase> Weapon;
};

namespace Velisect
{
	/** Mixamo bones import as "mixamorig:Name" or "mixamorig_Name"; find a bone by its unprefixed name. */
	FName FindBone(const USkeletalMeshComponent* Mesh, const TCHAR* ShortName);
}
