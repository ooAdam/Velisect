#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "VelisectAnimInstance.generated.h"

class UAnimSequenceBase;

/** Base drives the whole skeleton; Upper overrides UpperBodyRootBone and its children. */
UENUM(BlueprintType)
enum class EVelisectAnimLayer : uint8
{
	Base,
	Upper
};

/** One clip playing inside a layer. Channels cross-fade by weight. */
struct FVelisectAnimChannel
{
	UAnimSequenceBase* Anim = nullptr;
	float Time = 0.f;
	float PlayRate = 1.f;
	float Weight = 0.f;
	float BlendSpeed = 5.f;
	bool bLoop = true;
};

struct FVelisectAnimLayer
{
	/** The last channel is the active one; earlier channels fade out. */
	TArray<FVelisectAnimChannel> Channels;
};

/**
 * Puts the left hand on the weapon carried by the right hand, whatever the clip does with the arms: it holds Grip the
 * way the right hand holds GripPivot (the pistol grip), mirrored across the weapon's centre plane, fingers included.
 */
struct FVelisectLeftHandIK
{
	FName RightHand;
	FName UpperArm;
	FName ForeArm;
	FName Hand;
	/** (left, right) finger bones; each left finger takes its right twin's rotation, mirrored. */
	TArray<TPair<FName, FName>> Fingers;
	/** Weapon relative to the right hand bone. */
	FTransform WeaponGrip;
	/** Where the left hand holds and where the right hand holds, in weapon mesh space. */
	FVector Grip = FVector::ZeroVector;
	FVector GripPivot = FVector::ZeroVector;
	/** Turns the mirrored hold about Grip (weapon space), e.g. to stand a raked grip's hold upright. */
	FQuat Twist = FQuat::Identity;
	/** Component-space nudge from the clip's elbow towards where the elbow should swing (the IK pole). */
	FVector ElbowHint = FVector::ZeroVector;
};

/** Thread-safe copy of a channel handed to the proxy for evaluation. */
struct FVelisectPoseSample
{
	const UAnimSequenceBase* Anim = nullptr;
	float Time = 0.f;
	float Weight = 0.f;
	bool bLoop = true;
};

struct FVelisectAnimInstanceProxy : public FAnimInstanceProxy
{
	FVelisectAnimInstanceProxy() = default;
	explicit FVelisectAnimInstanceProxy(UAnimInstance* InAnimInstance) : FAnimInstanceProxy(InAnimInstance) {}

	virtual void PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds) override;
	virtual bool Evaluate(FPoseContext& Output) override;

private:
	static void BlendSamples(const TArray<FVelisectPoseSample>& Samples, FPoseContext& Output);
	void ApplyUpperBody(FPoseContext& Output) const;
	void ApplyAimRotation(FPoseContext& Output) const;
	void ApplyLeftHandIK(FPoseContext& Output) const;

	TArray<FVelisectPoseSample> BaseSamples;
	TArray<FVelisectPoseSample> UpperSamples;
	float UpperAlpha = 0.f;
	FName UpperBodyRootBone;
	TArray<FName> AimBones;
	FQuat AimRotation = FQuat::Identity;
	FVelisectLeftHandIK LeftHand;
	float LeftHandAlpha = 0.f;
};

/**
 * Code-driven animation instance: no Anim Blueprint graph. Gameplay code asks for clips per layer and
 * they cross-fade; the proxy samples and blends them on the animation worker thread.
 */
UCLASS(Transient, NotBlueprintable)
class VELISECT_API UVelisectAnimInstance : public UAnimInstance
{
	GENERATED_BODY()

public:
	/** Cross-fade Layer to Anim. Returns the clip duration at PlayRate (0 if Anim is null). */
	float Play(EVelisectAnimLayer Layer, UAnimSequenceBase* Anim, float PlayRate = 1.f, bool bLoop = true, float BlendTime = 0.2f, bool bRestart = false);

	/** Adjust the rate of the active clip of Layer without restarting it. */
	void SetPlayRate(EVelisectAnimLayer Layer, float PlayRate);

	/** Hold the active clip of Layer at a fixed time (used for single-frame poses). */
	void SetTime(EVelisectAnimLayer Layer, float Time);

	UAnimSequenceBase* GetActiveAnim(EVelisectAnimLayer Layer) const;

	void SetUpperBodyAlpha(float Alpha, float BlendTime = 0.2f);

	/** Blend the left hand onto the weapon (1) or back to the clip (0). */
	void SetLeftHandAlpha(float Alpha, float BlendTime = 0.15f);

	/** Bone whose subtree the Upper layer drives. Its rotation blends in component space, so the upper body keeps
	 *  the clip's facing even when the base layer's hips are turned differently. */
	FName UpperBodyRootBone;

	/** Bones that share AimRotation so the weapon follows the camera. */
	TArray<FName> AimBones;

	/** Component-space rotation spread across AimBones (aim pitch plus any yaw trim). */
	FQuat AimRotation = FQuat::Identity;

	FVelisectLeftHandIK LeftHand;

protected:
	virtual void NativeUpdateAnimation(float DeltaSeconds) override;
	virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
	virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) override;

private:
	friend struct FVelisectAnimInstanceProxy;

	FVelisectAnimLayer Layers[2];
	float UpperAlpha = 0.f;
	float UpperTargetAlpha = 0.f;
	float UpperAlphaSpeed = 5.f;
	float LeftHandAlpha = 0.f;
	float LeftHandTargetAlpha = 0.f;
	float LeftHandAlphaSpeed = 5.f;
};
