#include "VelisectAnimInstance.h"

#include "Animation/AnimSequenceBase.h"
#include "Animation/AnimationPoseData.h"
#include "Animation/AnimNodeBase.h"
#include "BonePose.h"
#include "TwoBoneIK.h"

namespace
{
	FCompactPoseBoneIndex CompactIndex(const FBoneContainer& Bones, FName Name)
	{
		const int32 MeshIndex = Name.IsNone() ? INDEX_NONE : Bones.GetPoseBoneIndexForBoneName(Name);
		return MeshIndex == INDEX_NONE ? FCompactPoseBoneIndex(INDEX_NONE) : Bones.MakeCompactPoseIndex(FMeshPoseBoneIndex(MeshIndex));
	}

	float BlendSpeedFor(float BlendTime)
	{
		return BlendTime > KINDA_SMALL_NUMBER ? 1.f / BlendTime : 1000.f;
	}

	void SnapshotLayer(const FVelisectAnimLayer& Layer, TArray<FVelisectPoseSample>& Out)
	{
		Out.Reset();
		float Total = 0.f;
		for (const FVelisectAnimChannel& Channel : Layer.Channels)
		{
			if (Channel.Anim && Channel.Weight > KINDA_SMALL_NUMBER)
			{
				Out.Add({Channel.Anim, Channel.Time, Channel.Weight, Channel.bLoop});
				Total += Channel.Weight;
			}
		}
		for (FVelisectPoseSample& Sample : Out)
		{
			Sample.Weight /= Total;
		}
	}
}

float UVelisectAnimInstance::Play(EVelisectAnimLayer Layer, UAnimSequenceBase* Anim, float PlayRate, bool bLoop, float BlendTime, bool bRestart)
{
	if (!Anim)
	{
		return 0.f;
	}

	TArray<FVelisectAnimChannel>& Channels = Layers[static_cast<int32>(Layer)].Channels;
	const float Speed = BlendSpeedFor(BlendTime);

	if (!bRestart && Channels.Num() > 0 && Channels.Last().Anim == Anim)
	{
		Channels.Last().PlayRate = PlayRate;
		Channels.Last().bLoop = bLoop;
		Channels.Last().BlendSpeed = Speed;
	}
	else
	{
		FVelisectAnimChannel& Channel = Channels.AddDefaulted_GetRef();
		Channel.Anim = Anim;
		Channel.PlayRate = PlayRate;
		Channel.bLoop = bLoop;
		Channel.BlendSpeed = Speed;
		Channel.Weight = Channels.Num() == 1 ? 1.f : 0.f;
	}

	for (FVelisectAnimChannel& Channel : Channels)
	{
		Channel.BlendSpeed = Speed;
	}

	return Anim->GetPlayLength() / FMath::Max(FMath::Abs(PlayRate), KINDA_SMALL_NUMBER);
}

void UVelisectAnimInstance::SetPlayRate(EVelisectAnimLayer Layer, float PlayRate)
{
	TArray<FVelisectAnimChannel>& Channels = Layers[static_cast<int32>(Layer)].Channels;
	if (Channels.Num() > 0)
	{
		Channels.Last().PlayRate = PlayRate;
	}
}

void UVelisectAnimInstance::SetTime(EVelisectAnimLayer Layer, float Time)
{
	TArray<FVelisectAnimChannel>& Channels = Layers[static_cast<int32>(Layer)].Channels;
	if (Channels.Num() > 0)
	{
		Channels.Last().Time = Time;
	}
}

UAnimSequenceBase* UVelisectAnimInstance::GetActiveAnim(EVelisectAnimLayer Layer) const
{
	const TArray<FVelisectAnimChannel>& Channels = Layers[static_cast<int32>(Layer)].Channels;
	return Channels.Num() > 0 ? Channels.Last().Anim : nullptr;
}

void UVelisectAnimInstance::SetUpperBodyAlpha(float Alpha, float BlendTime)
{
	UpperTargetAlpha = FMath::Clamp(Alpha, 0.f, 1.f);
	UpperAlphaSpeed = BlendSpeedFor(BlendTime);
}

void UVelisectAnimInstance::SetLeftHandAlpha(float Alpha, float BlendTime)
{
	LeftHandTargetAlpha = FMath::Clamp(Alpha, 0.f, 1.f);
	LeftHandAlphaSpeed = BlendSpeedFor(BlendTime);
}

void UVelisectAnimInstance::NativeUpdateAnimation(float DeltaSeconds)
{
	Super::NativeUpdateAnimation(DeltaSeconds);

	for (FVelisectAnimLayer& Layer : Layers)
	{
		const int32 Num = Layer.Channels.Num();
		for (int32 Index = 0; Index < Num; ++Index)
		{
			FVelisectAnimChannel& Channel = Layer.Channels[Index];
			const float Length = Channel.Anim ? Channel.Anim->GetPlayLength() : 0.f;
			Channel.Time += DeltaSeconds * Channel.PlayRate;
			if (Length > 0.f)
			{
				Channel.Time = Channel.bLoop ? FMath::Fmod(Channel.Time + Length, Length) : FMath::Clamp(Channel.Time, 0.f, Length);
			}

			const float Target = Index == Num - 1 ? 1.f : 0.f;
			Channel.Weight = FMath::FInterpConstantTo(Channel.Weight, Target, DeltaSeconds, Channel.BlendSpeed);
		}

		// Drop fully faded channels, always keeping the active one.
		for (int32 Index = Layer.Channels.Num() - 2; Index >= 0; --Index)
		{
			if (Layer.Channels[Index].Weight <= KINDA_SMALL_NUMBER)
			{
				Layer.Channels.RemoveAt(Index);
			}
		}
	}

	UpperAlpha = FMath::FInterpConstantTo(UpperAlpha, UpperTargetAlpha, DeltaSeconds, UpperAlphaSpeed);
	LeftHandAlpha = FMath::FInterpConstantTo(LeftHandAlpha, LeftHandTargetAlpha, DeltaSeconds, LeftHandAlphaSpeed);
}

FAnimInstanceProxy* UVelisectAnimInstance::CreateAnimInstanceProxy()
{
	return new FVelisectAnimInstanceProxy(this);
}

void UVelisectAnimInstance::DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy)
{
	delete static_cast<FVelisectAnimInstanceProxy*>(InProxy);
}

void FVelisectAnimInstanceProxy::PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds)
{
	FAnimInstanceProxy::PreUpdate(InAnimInstance, DeltaSeconds);

	const UVelisectAnimInstance* Instance = CastChecked<UVelisectAnimInstance>(InAnimInstance);
	SnapshotLayer(Instance->Layers[static_cast<int32>(EVelisectAnimLayer::Base)], BaseSamples);
	SnapshotLayer(Instance->Layers[static_cast<int32>(EVelisectAnimLayer::Upper)], UpperSamples);
	UpperAlpha = Instance->UpperAlpha;
	UpperBodyRootBone = Instance->UpperBodyRootBone;
	AimBones = Instance->AimBones;
	AimRotation = Instance->AimRotation;
	LeftHand = Instance->LeftHand;
	LeftHandAlpha = Instance->LeftHandAlpha;
}

bool FVelisectAnimInstanceProxy::Evaluate(FPoseContext& Output)
{
	if (BaseSamples.Num() > 0)
	{
		BlendSamples(BaseSamples, Output);
	}
	else
	{
		Output.ResetToRefPose();
	}

	ApplyUpperBody(Output);
	ApplyAimRotation(Output);
	ApplyLeftHandIK(Output);
	return true;
}

void FVelisectAnimInstanceProxy::BlendSamples(const TArray<FVelisectPoseSample>& Samples, FPoseContext& Output)
{
	// Sample the first clip straight into Output, then fold the rest in with running normalised weights.
	{
		FAnimationPoseData PoseData(Output);
		Samples[0].Anim->GetAnimationPose(PoseData, FAnimExtractContext(static_cast<double>(Samples[0].Time), false, {}, Samples[0].bLoop));
	}

	float Accumulated = Samples[0].Weight;
	for (int32 Index = 1; Index < Samples.Num(); ++Index)
	{
		const FVelisectPoseSample& Sample = Samples[Index];
		FPoseContext Temp(Output);
		FAnimationPoseData PoseData(Temp);
		Sample.Anim->GetAnimationPose(PoseData, FAnimExtractContext(static_cast<double>(Sample.Time), false, {}, Sample.bLoop));

		Accumulated += Sample.Weight;
		const float Alpha = Sample.Weight / Accumulated;
		for (const FCompactPoseBoneIndex BoneIndex : Output.Pose.ForEachBoneIndex())
		{
			Output.Pose[BoneIndex].BlendWith(Temp.Pose[BoneIndex], Alpha);
		}
	}
}

void FVelisectAnimInstanceProxy::ApplyUpperBody(FPoseContext& Output) const
{
	if (UpperAlpha <= KINDA_SMALL_NUMBER || UpperSamples.Num() == 0 || UpperBodyRootBone.IsNone())
	{
		return;
	}

	const FBoneContainer& Bones = Output.Pose.GetBoneContainer();
	const int32 MeshIndex = Bones.GetPoseBoneIndexForBoneName(UpperBodyRootBone);
	if (MeshIndex == INDEX_NONE)
	{
		return;
	}
	const FCompactPoseBoneIndex RootIndex = Bones.MakeCompactPoseIndex(FMeshPoseBoneIndex(MeshIndex));
	if (!RootIndex.IsValid())
	{
		return;
	}

	FPoseContext Upper(Output);
	BlendSamples(UpperSamples, Upper);

	// Mesh-space rotation for the subtree root: keep the clip's component-space orientation on top of the base hips.
	{
		FCSPose<FCompactPose> BaseComponent;
		BaseComponent.InitPose(Output.Pose);
		FCSPose<FCompactPose> UpperComponent;
		UpperComponent.InitPose(Upper.Pose);
		const FCompactPoseBoneIndex Parent = Output.Pose.GetParentBoneIndex(RootIndex);
		const FQuat BaseParent = Parent.IsValid() ? BaseComponent.GetComponentSpaceTransform(Parent).GetRotation() : FQuat::Identity;
		const FQuat UpperRoot = UpperComponent.GetComponentSpaceTransform(RootIndex).GetRotation();
		Upper.Pose[RootIndex].SetRotation((BaseParent.Inverse() * UpperRoot).GetNormalized());
	}

	// Compact poses list parents before children, so one pass marks the whole subtree.
	TArray<bool> InUpper;
	InUpper.SetNumZeroed(Output.Pose.GetNumBones());
	for (const FCompactPoseBoneIndex BoneIndex : Output.Pose.ForEachBoneIndex())
	{
		const FCompactPoseBoneIndex Parent = Output.Pose.GetParentBoneIndex(BoneIndex);
		const bool bUpper = BoneIndex == RootIndex || (Parent.IsValid() && InUpper[Parent.GetInt()]);
		InUpper[BoneIndex.GetInt()] = bUpper;
		if (bUpper)
		{
			Output.Pose[BoneIndex].BlendWith(Upper.Pose[BoneIndex], UpperAlpha);
		}
	}
}

void FVelisectAnimInstanceProxy::ApplyAimRotation(FPoseContext& Output) const
{
	if (AimRotation.Equals(FQuat::Identity, 1.e-4f) || AimBones.Num() == 0)
	{
		return;
	}

	const FBoneContainer& Bones = Output.Pose.GetBoneContainer();
	FCSPose<FCompactPose> ComponentPose;
	ComponentPose.InitPose(Output.Pose);

	// Each bone takes an equal slice of the rotation, computed against the unmodified parent transforms. That is
	// exact for a single axis and close enough for a small yaw trim on top of pitch.
	const FQuat Slice = FQuat::Slerp(FQuat::Identity, AimRotation, 1.f / AimBones.Num());
	for (const FName& BoneName : AimBones)
	{
		const int32 MeshIndex = Bones.GetPoseBoneIndexForBoneName(BoneName);
		if (MeshIndex == INDEX_NONE)
		{
			continue;
		}
		const FCompactPoseBoneIndex BoneIndex = Bones.MakeCompactPoseIndex(FMeshPoseBoneIndex(MeshIndex));
		if (!BoneIndex.IsValid())
		{
			continue;
		}

		const FCompactPoseBoneIndex Parent = Output.Pose.GetParentBoneIndex(BoneIndex);
		const FQuat ParentRotation = Parent.IsValid() ? ComponentPose.GetComponentSpaceTransform(Parent).GetRotation() : FQuat::Identity;
		FTransform& Local = Output.Pose[BoneIndex];
		Local.SetRotation((ParentRotation.Inverse() * Slice * ParentRotation * Local.GetRotation()).GetNormalized());
	}
}

void FVelisectAnimInstanceProxy::ApplyLeftHandIK(FPoseContext& Output) const
{
	if (LeftHandAlpha <= KINDA_SMALL_NUMBER)
	{
		return;
	}

	const FBoneContainer& Bones = Output.Pose.GetBoneContainer();
	const FCompactPoseBoneIndex RightHand = CompactIndex(Bones, LeftHand.RightHand);
	const FCompactPoseBoneIndex UpperArm = CompactIndex(Bones, LeftHand.UpperArm);
	const FCompactPoseBoneIndex ForeArm = CompactIndex(Bones, LeftHand.ForeArm);
	const FCompactPoseBoneIndex Hand = CompactIndex(Bones, LeftHand.Hand);
	if (!RightHand.IsValid() || !UpperArm.IsValid() || !ForeArm.IsValid() || !Hand.IsValid())
	{
		return;
	}

	// The rig's left bones mirror the right ones across component X (the body's left-right axis), so a mirrored
	// rotation is the same quaternion with Y and Z negated; that holds for local rotations and for weapon space alike.
	auto Mirror = [](const FQuat& Rotation) { return FQuat(Rotation.X, -Rotation.Y, -Rotation.Z, Rotation.W); };

	// Fingers (local space): the left hand closes the way the right one closes on the pistol grip.
	for (const TPair<FName, FName>& Finger : LeftHand.Fingers)
	{
		const FCompactPoseBoneIndex Left = CompactIndex(Bones, Finger.Key);
		const FCompactPoseBoneIndex Right = CompactIndex(Bones, Finger.Value);
		if (Left.IsValid() && Right.IsValid())
		{
			FTransform& Local = Output.Pose[Left];
			Local.SetRotation(FQuat::Slerp(Local.GetRotation(), Mirror(Output.Pose[Right].GetRotation()), LeftHandAlpha).GetNormalized());
		}
	}

	// The hand: the right hand's hold (weapon space) mirrored across the weapon's centre plane, carried from the
	// pistol grip to Grip and turned about it.
	const FTransform RightInWeapon = LeftHand.WeaponGrip.Inverse();
	const FVector MirroredLocation(-RightInWeapon.GetLocation().X, RightInWeapon.GetLocation().Y, RightInWeapon.GetLocation().Z);
	const FVector HandInWeapon = LeftHand.Grip + LeftHand.Twist.RotateVector(MirroredLocation - LeftHand.GripPivot);
	const FQuat HandInWeaponRotation = LeftHand.Twist * Mirror(RightInWeapon.GetRotation());

	FCSPose<FCompactPose> ComponentPose;
	ComponentPose.InitPose(Output.Pose);
	const FTransform Weapon = LeftHand.WeaponGrip * ComponentPose.GetComponentSpaceTransform(RightHand);
	FTransform UpperTransform = ComponentPose.GetComponentSpaceTransform(UpperArm);
	FTransform ForeTransform = ComponentPose.GetComponentSpaceTransform(ForeArm);
	FTransform HandTransform = ComponentPose.GetComponentSpaceTransform(Hand);

	// The clip's elbow, nudged by the hint, sets the arm's bend plane.
	AnimationCore::SolveTwoBoneIK(UpperTransform, ForeTransform, HandTransform, ForeTransform.GetLocation() + LeftHand.ElbowHint, Weapon.TransformPosition(HandInWeapon), false, 1.0, 1.0);
	HandTransform.SetRotation((Weapon.GetRotation() * HandInWeaponRotation).GetNormalized());

	const FBoneTransform Solved[] = {{UpperArm, UpperTransform}, {ForeArm, ForeTransform}, {Hand, HandTransform}};
	ComponentPose.LocalBlendCSBoneTransforms(Solved, LeftHandAlpha);
	FCSPose<FCompactPose>::ConvertComponentPosesToLocalPoses(MoveTemp(ComponentPose), Output.Pose);
}
