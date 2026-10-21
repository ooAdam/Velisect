#include "VelisectCharacter.h"

#include "VelisectAnimInstance.h"
#include "VelisectZombie.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/DamageEvents.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/DamageType.h"
#include "GameFramework/PlayerController.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "Sound/SoundBase.h"
#include "TimerManager.h"

namespace
{
	const TCHAR* PlayerAnimFolder = TEXT("/Game/Velisect/Characters/Player/Animations");

	TSoftObjectPtr<UAnimSequenceBase> PlayerAnim(const TCHAR* Name)
	{
		return TSoftObjectPtr<UAnimSequenceBase>(FSoftObjectPath(FString::Printf(TEXT("%s/%s.%s"), PlayerAnimFolder, Name, Name)));
	}

	FVelisectLocoClip Loco(const TCHAR* Name, float NaturalSpeed)
	{
		FVelisectLocoClip Clip;
		Clip.Anim = PlayerAnim(Name);
		Clip.NaturalSpeed = NaturalSpeed;
		return Clip;
	}

	/** Maps a local-space velocity to F, FR, R, BR, B, BL, L, FL (0..7). */
	int32 DirectionSector(const FVector& LocalVelocity)
	{
		const float Angle = FMath::RadiansToDegrees(FMath::Atan2(LocalVelocity.Y, LocalVelocity.X));
		return (FMath::RoundToInt(Angle / 45.f) + 8) % 8;
	}
}

AVelisectCharacter::AVelisectCharacter()
{
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->InitCapsuleSize(34.f, 92.f);
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);

	bUseControllerRotationYaw = true;
	bUseControllerRotationPitch = false;
	bUseControllerRotationRoll = false;

	UCharacterMovementComponent* Movement = GetCharacterMovement();
	Movement->MaxWalkSpeed = WalkSpeed;
	Movement->MaxWalkSpeedCrouched = CrouchSpeed;
	Movement->JumpZVelocity = 430.f;
	Movement->AirControl = 0.25f;
	Movement->BrakingDecelerationWalking = 1600.f;
	Movement->GroundFriction = 7.f;
	Movement->bOrientRotationToMovement = false;
	Movement->GetNavAgentPropertiesRef().bCanCrouch = true;
	Movement->SetCrouchedHalfHeight(58.f);
	CrouchedEyeHeight = 50.f;

	// Mixamo meshes face +Y; turn them to face the actor's +X. The owner sees the arms instead; the body casts the shadow.
	GetMesh()->SetRelativeLocationAndRotation(FVector(0.f, 0.f, -92.f), FRotator(0.f, -90.f, 0.f));
	GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	GetMesh()->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
	GetMesh()->SetAnimInstanceClass(UVelisectAnimInstance::StaticClass());
	GetMesh()->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::WorldSpaceRepresentation);

	Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
	Camera->SetupAttachment(GetCapsuleComponent());
	Camera->SetRelativeLocation(FVector(14.f, 0.f, EyeHeight));
	Camera->bUsePawnControlRotation = true;
	Camera->SetFieldOfView(90.f);
	Camera->SetEnableFirstPersonFieldOfView(true);
	Camera->SetEnableFirstPersonScale(true);

	FirstPersonArms = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("FirstPersonArms"));
	FirstPersonArms->SetupAttachment(Camera);
	FirstPersonArms->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	FirstPersonArms->SetCastShadow(false);
	FirstPersonArms->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
	FirstPersonArms->SetAnimInstanceClass(UVelisectAnimInstance::StaticClass());
	FirstPersonArms->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::FirstPerson);

	Weapon = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Weapon"));
	Weapon->SetupAttachment(FirstPersonArms);
	Weapon->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Weapon->SetCastShadow(false);
	Weapon->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::FirstPerson);

	WorldWeapon = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WorldWeapon"));
	WorldWeapon->SetupAttachment(GetMesh());
	WorldWeapon->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	WorldWeapon->SetCastShadow(true);
	WorldWeapon->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::WorldSpaceRepresentation);

	MuzzleLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("MuzzleLight"));
	MuzzleLight->SetupAttachment(Weapon);
	MuzzleLight->SetIntensity(0.f);
	MuzzleLight->SetLightColor(FLinearColor(1.f, 0.75f, 0.4f));
	MuzzleLight->SetAttenuationRadius(600.f);
	MuzzleLight->SetCastShadows(false);

	Flashlight = CreateDefaultSubobject<USpotLightComponent>(TEXT("Flashlight"));
	Flashlight->SetupAttachment(Camera);
	Flashlight->SetRelativeLocation(FVector(10.f, 12.f, -10.f));
	Flashlight->SetIntensity(9000.f);
	Flashlight->SetAttenuationRadius(2400.f);
	Flashlight->SetInnerConeAngle(14.f);
	Flashlight->SetOuterConeAngle(28.f);
	Flashlight->SetLightColor(FLinearColor(1.f, 0.95f, 0.85f));
	Flashlight->SetVisibility(false);

	BodyMeshAsset = TSoftObjectPtr<USkeletalMesh>(FSoftObjectPath(TEXT("/Game/Velisect/Characters/Player/SK_Player.SK_Player")));
	ArmsMeshAsset = TSoftObjectPtr<USkeletalMesh>(FSoftObjectPath(TEXT("/Game/Velisect/Characters/Player/SK_PlayerArms.SK_PlayerArms")));
	WeaponMeshAsset = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(TEXT("/Game/Velisect/Weapons/Rifle/SM_Rifle.SM_Rifle")));
	FireSound = TSoftObjectPtr<USoundBase>(FSoftObjectPath(TEXT("/Game/Velisect/Audio/S_RifleShot.S_RifleShot")));
	ImpactDecalMaterial = TSoftObjectPtr<UMaterialInterface>(FSoftObjectPath(TEXT("/Game/Velisect/Materials/M_BulletHole.M_BulletHole")));

	AimPoseAnim = PlayerAnim(TEXT("A_Player_FiringRifle"));
	FireAnim = PlayerAnim(TEXT("A_Player_FiringRifle"));
	LowReadyAnim = PlayerAnim(TEXT("A_Player_RifleTurn"));
	ReloadAnim = PlayerAnim(TEXT("A_Player_Reloading"));
	EquipAnim = PlayerAnim(TEXT("A_Player_RiflePullOut"));
	HitReactAnim = PlayerAnim(TEXT("A_Player_HitReaction"));
	DeathAnim = PlayerAnim(TEXT("A_Player_Dying"));
	IdleAnim = PlayerAnim(TEXT("A_Player_RifleTurn"));
	CrouchIdleAnim = PlayerAnim(TEXT("A_Player_CrouchStopWalking"));
	JumpAnim = PlayerAnim(TEXT("A_Player_Jump"));

	// A negative natural speed plays the clip in reverse (forward run reversed reads as backpedalling).
	MoveClips = {
		Loco(TEXT("A_Player_SprintForward"), 714.f),
		Loco(TEXT("A_Player_SprintForwardRight"), 716.f),
		Loco(TEXT("A_Player_StrafeRight"), 108.f),
		Loco(TEXT("A_Player_RunBackwardRight"), 475.f),
		Loco(TEXT("A_Player_SprintForward"), -714.f),
		Loco(TEXT("A_Player_RunBackwardLeft"), 475.f),
		Loco(TEXT("A_Player_StrafeLeft"), 108.f),
		Loco(TEXT("A_Player_SprintForwardLeft"), 716.f)};

	CrouchMoveClips = {
		Loco(TEXT("A_Player_CrouchRunning"), 130.f),
		Loco(TEXT("A_Player_CrouchRunning"), 130.f),
		Loco(TEXT("A_Player_WalkCrouchingRight"), 202.f),
		Loco(TEXT("A_Player_WalkCrouchingRight"), 202.f),
		Loco(TEXT("A_Player_CrouchRunning"), -130.f),
		Loco(TEXT("A_Player_WalkCrouchingLeft"), 202.f),
		Loco(TEXT("A_Player_WalkCrouchingLeft"), 202.f),
		Loco(TEXT("A_Player_CrouchRunning"), 130.f)};
}

void AVelisectCharacter::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	// Runs before ACharacter caches the mesh offset for crouching, so the offset survives crouch/uncrouch.
	GetMesh()->SetRelativeLocation(FVector(0.f, 0.f, -GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight()) + BodyOffset);
	LoadAssets();
}

void AVelisectCharacter::BeginPlay()
{
	Super::BeginPlay();

	LoadAssets();
	Health = MaxHealth;
	AmmoInMagazine = MagazineSize;
	CameraBaseHeight = EyeHeight;
	CameraBaseForward = CameraOffset.X;

	Camera->SetFirstPersonFieldOfView(ViewmodelFieldOfView);
	Camera->SetFirstPersonScale(ViewmodelScale);

	if (UVelisectAnimInstance* Anim = GetVelisectAnim())
	{
		SetupAnim(Anim, GetMesh());
		Anim->AimBones = {Velisect::FindBone(GetMesh(), TEXT("Spine")), Velisect::FindBone(GetMesh(), TEXT("Spine1")), Velisect::FindBone(GetMesh(), TEXT("Spine2"))};
		Anim->Play(EVelisectAnimLayer::Base, Loaded(IdleAnim), 0.f, true, 0.f);
	}
	// The arms stand in the aim pose (it is what ViewmodelOffset frames); the upper-body clips play over it.
	if (UVelisectAnimInstance* Arms = GetArmsAnim())
	{
		SetupAnim(Arms, FirstPersonArms);
		Arms->Play(EVelisectAnimLayer::Base, Loaded(AimPoseAnim), 0.f, true, 0.f);
	}

	bEquipping = true;
	UpperPose = EUpperPose::OneShot;
	const float EquipTime = PlayUpper(Loaded(EquipAnim), 1.4f, false, 0.f, false);
	GetWorldTimerManager().SetTimer(EquipTimer, this, &AVelisectCharacter::FinishEquip, FMath::Max(EquipTime * 0.85f, 0.1f));
}

void AVelisectCharacter::SetupAnim(UVelisectAnimInstance* Anim, const USkeletalMeshComponent* Skeleton) const
{
	Anim->UpperBodyRootBone = Velisect::FindBone(Skeleton, TEXT("Spine"));
	Anim->SetUpperBodyAlpha(1.f, 0.f);
	Anim->LeftHand.RightHand = Velisect::FindBone(Skeleton, TEXT("RightHand"));
	Anim->LeftHand.UpperArm = Velisect::FindBone(Skeleton, TEXT("LeftArm"));
	Anim->LeftHand.ForeArm = Velisect::FindBone(Skeleton, TEXT("LeftForeArm"));
	Anim->LeftHand.Hand = Velisect::FindBone(Skeleton, TEXT("LeftHand"));
	Anim->LeftHand.Fingers.Reset();
	for (const TCHAR* Finger : {TEXT("Thumb"), TEXT("Index"), TEXT("Middle"), TEXT("Ring"), TEXT("Pinky")})
	{
		for (int32 Joint = 1; Joint <= 3; ++Joint)
		{
			const FName Left = Velisect::FindBone(Skeleton, *FString::Printf(TEXT("LeftHand%s%d"), Finger, Joint));
			const FName Right = Velisect::FindBone(Skeleton, *FString::Printf(TEXT("RightHand%s%d"), Finger, Joint));
			if (!Left.IsNone() && !Right.IsNone())
			{
				Anim->LeftHand.Fingers.Emplace(Left, Right);
			}
		}
	}
	Anim->LeftHand.WeaponGrip = WeaponGripOffset;
	Anim->LeftHand.Grip = LeftHandGrip;
	Anim->LeftHand.GripPivot = PistolGrip;
	Anim->LeftHand.Twist = LeftHandTwist.Quaternion();
	Anim->LeftHand.ElbowHint = LeftElbowHint;
}

float AVelisectCharacter::PlayUpper(UAnimSequenceBase* Clip, float Rate, bool bLoop, float BlendTime, bool bRestart, UAnimSequenceBase* ArmsClip)
{
	if (UVelisectAnimInstance* Arms = GetArmsAnim())
	{
		Arms->Play(EVelisectAnimLayer::Upper, ArmsClip ? ArmsClip : Clip, Rate, bLoop, BlendTime, bRestart);
	}
	UVelisectAnimInstance* Anim = GetVelisectAnim();
	return Anim ? Anim->Play(EVelisectAnimLayer::Upper, Clip, Rate, bLoop, BlendTime, bRestart) : 0.f;
}

void AVelisectCharacter::LoadAssets()
{
	if (USkeletalMesh* Body = BodyMeshAsset.LoadSynchronous(); Body && GetMesh()->GetSkeletalMeshAsset() != Body)
	{
		GetMesh()->SetSkeletalMesh(Body);
		GetMesh()->SetAnimInstanceClass(UVelisectAnimInstance::StaticClass());
	}
	if (USkeletalMesh* Arms = ArmsMeshAsset.LoadSynchronous(); Arms && FirstPersonArms->GetSkeletalMeshAsset() != Arms)
	{
		FirstPersonArms->SetSkeletalMesh(Arms);
		FirstPersonArms->SetAnimInstanceClass(UVelisectAnimInstance::StaticClass());
	}
	FirstPersonArms->SetRelativeTransform(ViewmodelOffset);
	if (UStaticMesh* Rifle = WeaponMeshAsset.LoadSynchronous())
	{
		Weapon->SetStaticMesh(Rifle);
		WorldWeapon->SetStaticMesh(Rifle);
	}

	RightHandBone = Velisect::FindBone(GetMesh(), TEXT("RightHand"));
	if (!RightHandBone.IsNone())
	{
		Weapon->AttachToComponent(FirstPersonArms, FAttachmentTransformRules::KeepRelativeTransform, RightHandBone);
		Weapon->SetRelativeTransform(WeaponGripOffset);
		WorldWeapon->AttachToComponent(GetMesh(), FAttachmentTransformRules::KeepRelativeTransform, RightHandBone);
		WorldWeapon->SetRelativeTransform(WeaponGripOffset);
	}
	MuzzleLight->SetRelativeLocation(MuzzleOffset);

	// The camera sits where the head is; hide it so it never clips into view.
	HeadBone = Velisect::FindBone(GetMesh(), TEXT("Head"));
	if (!HeadBone.IsNone() && GetWorld() && GetWorld()->IsGameWorld())
	{
		GetMesh()->HideBoneByName(HeadBone, PBO_None);
	}
}

UVelisectAnimInstance* AVelisectCharacter::GetVelisectAnim() const
{
	return Cast<UVelisectAnimInstance>(GetMesh()->GetAnimInstance());
}

UVelisectAnimInstance* AVelisectCharacter::GetArmsAnim() const
{
	return Cast<UVelisectAnimInstance>(FirstPersonArms->GetAnimInstance());
}

UAnimSequenceBase* AVelisectCharacter::Loaded(const TSoftObjectPtr<UAnimSequenceBase>& Anim)
{
	UAnimSequenceBase* Sequence = Anim.LoadSynchronous();
	if (Sequence)
	{
		LoadedAnims.AddUnique(Sequence);
	}
	return Sequence;
}

void AVelisectCharacter::BuildInput()
{
	auto MakeAction = [this](EInputActionValueType Type)
	{
		UInputAction* Action = NewObject<UInputAction>(this);
		Action->ValueType = Type;
		return Action;
	};

	InputContext = NewObject<UInputMappingContext>(this);
	MoveAction = MakeAction(EInputActionValueType::Axis2D);
	LookAction = MakeAction(EInputActionValueType::Axis2D);
	JumpAction = MakeAction(EInputActionValueType::Boolean);
	SprintAction = MakeAction(EInputActionValueType::Boolean);
	CrouchAction = MakeAction(EInputActionValueType::Boolean);
	FireAction = MakeAction(EInputActionValueType::Boolean);
	ReloadAction = MakeAction(EInputActionValueType::Boolean);
	FlashlightAction = MakeAction(EInputActionValueType::Boolean);

	// WASD -> 2D axis: X = strafe, Y = forward.
	auto MapMove = [this](FKey Key, bool bSwizzle, bool bNegate)
	{
		FEnhancedActionKeyMapping& Mapping = InputContext->MapKey(MoveAction, Key);
		if (bSwizzle)
		{
			UInputModifierSwizzleAxis* Swizzle = NewObject<UInputModifierSwizzleAxis>(this);
			Swizzle->Order = EInputAxisSwizzle::YXZ;
			Mapping.Modifiers.Add(Swizzle);
		}
		if (bNegate)
		{
			Mapping.Modifiers.Add(NewObject<UInputModifierNegate>(this));
		}
	};
	MapMove(EKeys::W, true, false);
	MapMove(EKeys::S, true, true);
	MapMove(EKeys::D, false, false);
	MapMove(EKeys::A, false, true);

	InputContext->MapKey(LookAction, EKeys::Mouse2D);
	InputContext->MapKey(JumpAction, EKeys::SpaceBar);
	InputContext->MapKey(SprintAction, EKeys::LeftShift);
	InputContext->MapKey(CrouchAction, EKeys::LeftControl);
	InputContext->MapKey(CrouchAction, EKeys::C);
	InputContext->MapKey(FireAction, EKeys::LeftMouseButton);
	InputContext->MapKey(ReloadAction, EKeys::R);
	InputContext->MapKey(FlashlightAction, EKeys::F);
}

void AVelisectCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	BuildInput();
	if (const APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer()))
		{
			Subsystem->AddMappingContext(InputContext, 0);
		}
	}

	UEnhancedInputComponent* Input = CastChecked<UEnhancedInputComponent>(PlayerInputComponent);
	Input->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AVelisectCharacter::Move);
	Input->BindAction(MoveAction, ETriggerEvent::Completed, this, &AVelisectCharacter::Move);
	Input->BindAction(LookAction, ETriggerEvent::Triggered, this, &AVelisectCharacter::Look);
	Input->BindAction(JumpAction, ETriggerEvent::Started, this, &ACharacter::Jump);
	Input->BindAction(JumpAction, ETriggerEvent::Completed, this, &ACharacter::StopJumping);
	Input->BindAction(SprintAction, ETriggerEvent::Started, this, &AVelisectCharacter::StartSprint);
	Input->BindAction(SprintAction, ETriggerEvent::Completed, this, &AVelisectCharacter::StopSprint);
	Input->BindAction(CrouchAction, ETriggerEvent::Started, this, &AVelisectCharacter::ToggleCrouch);
	Input->BindAction(FireAction, ETriggerEvent::Started, this, &AVelisectCharacter::StartFire);
	Input->BindAction(FireAction, ETriggerEvent::Completed, this, &AVelisectCharacter::StopFire);
	Input->BindAction(ReloadAction, ETriggerEvent::Started, this, &AVelisectCharacter::Reload);
	Input->BindAction(FlashlightAction, ETriggerEvent::Started, this, &AVelisectCharacter::ToggleFlashlight);
}

void AVelisectCharacter::Move(const FInputActionValue& Value)
{
	MoveInput = Value.Get<FVector2D>();
	if (bDead)
	{
		return;
	}
	AddMovementInput(GetActorForwardVector(), MoveInput.Y);
	AddMovementInput(GetActorRightVector(), MoveInput.X);
}

void AVelisectCharacter::Look(const FInputActionValue& Value)
{
	if (bDead || !Controller)
	{
		return;
	}
	const FVector2D Delta = Value.Get<FVector2D>();
	constexpr float Sensitivity = 0.08f;
	FRotator Rotation = Controller->GetControlRotation();
	Rotation.Yaw += Delta.X * Sensitivity;
	Rotation.Pitch = FMath::Clamp(FRotator::NormalizeAxis(Rotation.Pitch + Delta.Y * Sensitivity), -80.f, 80.f);
	Controller->SetControlRotation(Rotation);

	// The rifle lags behind the turn, then settles (UpdateViewmodel).
	ViewSway.X = FMath::Clamp(ViewSway.X - Delta.X * Sensitivity * ViewmodelSway, -ViewmodelMaxSway, ViewmodelMaxSway);
	ViewSway.Y = FMath::Clamp(ViewSway.Y - Delta.Y * Sensitivity * ViewmodelSway, -ViewmodelMaxSway, ViewmodelMaxSway);
}

bool AVelisectCharacter::IsSprinting() const
{
	return bWantsSprint && !bIsCrouched && MoveInput.Y > 0.3f && !GetCharacterMovement()->IsFalling() && GetVelocity().Size2D() > 50.f;
}

void AVelisectCharacter::StartSprint()
{
	bWantsSprint = true;
	if (bIsCrouched)
	{
		UnCrouch();
	}
}

void AVelisectCharacter::StopSprint()
{
	bWantsSprint = false;
}

void AVelisectCharacter::ToggleCrouch()
{
	if (bDead)
	{
		return;
	}
	if (bIsCrouched)
	{
		UnCrouch();
	}
	else
	{
		bWantsSprint = false;
		Crouch();
	}
}

void AVelisectCharacter::StartFire()
{
	bTriggerHeld = true;
	const float SinceLast = static_cast<float>(GetWorld()->GetTimeSeconds() - LastShotTime);
	const float FirstDelay = FMath::Max(FireInterval - SinceLast, 0.f);
	GetWorldTimerManager().SetTimer(FireTimer, this, &AVelisectCharacter::FireShot, FireInterval, true, FirstDelay);
}

void AVelisectCharacter::StopFire()
{
	bTriggerHeld = false;
	GetWorldTimerManager().ClearTimer(FireTimer);
}

void AVelisectCharacter::FireShot()
{
	if (bDead || bReloading || bEquipping || IsSprinting())
	{
		return;
	}
	if (AmmoInMagazine <= 0)
	{
		StopFire();
		Reload();
		return;
	}

	--AmmoInMagazine;
	LastShotTime = GetWorld()->GetTimeSeconds();

	const FVector Start = Camera->GetComponentLocation();
	const float Spread = SpreadDegrees * (GetVelocity().Size2D() > 50.f ? 2.f : 1.f) * (bIsCrouched ? 0.6f : 1.f);
	const FVector Direction = FMath::VRandCone(Camera->GetForwardVector(), FMath::DegreesToRadians(Spread));
	const FVector End = Start + Direction * Range;

	FCollisionQueryParams Params(SCENE_QUERY_STAT(VelisectShot), false, this);
	FHitResult Hit;
	if (GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params))
	{
		if (AVelisectZombie* Zombie = Cast<AVelisectZombie>(Hit.GetActor()))
		{
			UGameplayStatics::ApplyPointDamage(Zombie, Damage, Direction, Hit, GetController(), this, UDamageType::StaticClass());
			LastHitConfirmTime = LastShotTime;
		}
		else if (UMaterialInterface* Decal = ImpactDecalMaterial.LoadSynchronous())
		{
			FRotator Rotation = (-Hit.ImpactNormal).Rotation();
			Rotation.Roll = FMath::FRandRange(0.f, 360.f);
			UGameplayStatics::SpawnDecalAtLocation(this, Decal, FVector(3.f, 2.5f, 2.5f), Hit.ImpactPoint, Rotation, 30.f);
		}
	}

	// Gunfire wakes nearby zombies.
	for (TActorIterator<AVelisectZombie> It(GetWorld()); It; ++It)
	{
		It->HearNoise(GetActorLocation(), NoiseRadius);
	}

	if (USoundBase* Sound = FireSound.LoadSynchronous())
	{
		UGameplayStatics::PlaySoundAtLocation(this, Sound, Weapon->GetComponentTransform().TransformPosition(MuzzleOffset), FMath::FRandRange(0.9f, 1.f), FMath::FRandRange(0.94f, 1.06f));
	}
	MuzzleLight->SetIntensity(12000.f);
	GetWorldTimerManager().SetTimer(MuzzleTimer, [this]() { MuzzleLight->SetIntensity(0.f); }, 0.045f, false);
	RecoilKick += RecoilPitch * FMath::FRandRange(0.8f, 1.2f);
	WeaponKick += WeaponKickPerShot * FMath::FRandRange(0.8f, 1.2f);
}

void AVelisectCharacter::Reload()
{
	if (bDead || bReloading || bEquipping || AmmoInMagazine >= MagazineSize || ReserveAmmo <= 0)
	{
		return;
	}
	bReloading = true;
	UpperPose = EUpperPose::OneShot;
	StopFire();
	const float Duration = PlayUpper(Loaded(ReloadAnim), ReloadPlayRate, false, 0.2f, true);
	GetWorldTimerManager().SetTimer(ReloadTimer, this, &AVelisectCharacter::FinishReload, FMath::Max(Duration - 0.2f, 0.5f));
}

void AVelisectCharacter::VsReload()
{
	// A full magazine never reloads; spend a round first.
	AmmoInMagazine = FMath::Min(AmmoInMagazine, MagazineSize - 1);
	Reload();
}

void AVelisectCharacter::FinishReload()
{
	const int32 Needed = MagazineSize - AmmoInMagazine;
	const int32 Taken = FMath::Min(Needed, ReserveAmmo);
	AmmoInMagazine += Taken;
	ReserveAmmo -= Taken;
	bReloading = false;
}

void AVelisectCharacter::FinishEquip()
{
	bEquipping = false;
}

void AVelisectCharacter::ToggleFlashlight()
{
	Flashlight->SetVisibility(!Flashlight->IsVisible());
}

float AVelisectCharacter::GetTimeSinceHitConfirm() const
{
	return static_cast<float>(GetWorld()->GetTimeSeconds() - LastHitConfirmTime);
}

float AVelisectCharacter::GetTimeSinceDamaged() const
{
	return static_cast<float>(GetWorld()->GetTimeSeconds() - LastDamagedTime);
}

float AVelisectCharacter::TakeDamage(float DamageAmount, const FDamageEvent& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	if (bDead || DamageAmount <= 0.f)
	{
		return 0.f;
	}
	Health = FMath::Max(Health - DamageAmount, 0.f);
	LastDamagedTime = GetWorld()->GetTimeSeconds();

	if (Health <= 0.f)
	{
		Die();
	}
	else if (!bReloading && !bEquipping)
	{
		HitReactUntil = GetWorld()->GetTimeSeconds() + 0.35f;
		UpperPose = EUpperPose::OneShot;
		PlayUpper(Loaded(HitReactAnim), 1.6f, false, 0.08f, true);
	}
	return DamageAmount;
}

void AVelisectCharacter::Die()
{
	bDead = true;
	StopFire();
	GetWorldTimerManager().ClearTimer(ReloadTimer);
	GetCharacterMovement()->DisableMovement();
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	if (UVelisectAnimInstance* Anim = GetVelisectAnim())
	{
		Anim->AimRotation = FQuat::Identity;
		Anim->SetUpperBodyAlpha(0.f, 0.2f);
		Anim->SetLeftHandAlpha(0.f, 0.2f);
		Anim->Play(EVelisectAnimLayer::Base, Loaded(DeathAnim), 1.f, false, 0.2f, true);
	}

	// The death cam sees the body and its rifle, not the first-person arms.
	FirstPersonArms->SetVisibility(false, true);
	GetMesh()->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::None);
	WorldWeapon->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::None);

	// Ride the head down with the body.
	if (!HeadBone.IsNone())
	{
		Camera->bUsePawnControlRotation = false;
		Camera->AttachToComponent(GetMesh(), FAttachmentTransformRules::KeepWorldTransform, HeadBone);
	}

	FTimerHandle RestartTimer;
	GetWorldTimerManager().SetTimer(RestartTimer, [this]()
	{
		if (APlayerController* PC = Cast<APlayerController>(GetController()))
		{
			PC->ConsoleCommand(TEXT("RestartLevel"));
		}
	}, 6.f, false);
}

void AVelisectCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!bDead)
	{
		GetCharacterMovement()->MaxWalkSpeed = IsSprinting() ? SprintSpeed : WalkSpeed;
		if (bTriggerHeld && IsSprinting())
		{
			bWantsSprint = false;
		}
	}

	UpdateAnimation(DeltaSeconds);
	UpdateCamera(DeltaSeconds);
}

void AVelisectCharacter::UpdateAnimation(float DeltaSeconds)
{
	UVelisectAnimInstance* Anim = GetVelisectAnim();
	if (!Anim || bDead)
	{
		return;
	}

	// Aim pitch (plus a fixed yaw trim) bends the spine so the rifle tracks the camera.
	const FTransform& MeshTransform = GetMesh()->GetComponentTransform();
	WeaponKick = FMath::FInterpTo(WeaponKick, 0.f, DeltaSeconds, 16.f);
	// The kick rides with the view pitch so it always lifts the muzzle, whatever the scale's sign.
	const float Pitch = (FRotator::NormalizeAxis(GetControlRotation().Pitch) + WeaponKick) * AimPitchScale + AimPitchOffset;
	const FQuat PitchRotation(MeshTransform.InverseTransformVectorNoScale(GetActorRightVector()), FMath::DegreesToRadians(Pitch));
	const FQuat YawRotation(MeshTransform.InverseTransformVectorNoScale(GetActorUpVector()), FMath::DegreesToRadians(AimYawOffset));
	Anim->AimRotation = PitchRotation * YawRotation;

	// Base layer: locomotion.
	const FVector Velocity = GetVelocity();
	const float Speed = Velocity.Size2D();
	if (GetCharacterMovement()->IsFalling())
	{
		Anim->Play(EVelisectAnimLayer::Base, Loaded(JumpAnim), 1.4f, false, 0.15f);
	}
	else if (Speed > 30.f)
	{
		const TArray<FVelisectLocoClip>& Clips = bIsCrouched ? CrouchMoveClips : MoveClips;
		if (Clips.Num() == 8)
		{
			const FVelisectLocoClip& Clip = Clips[DirectionSector(GetActorRotation().UnrotateVector(Velocity))];
			const float Natural = FMath::Max(FMath::Abs(Clip.NaturalSpeed), 1.f);
			const float Rate = FMath::Clamp(Speed / Natural, 0.35f, 1.6f) * FMath::Sign(Clip.NaturalSpeed);
			Anim->Play(EVelisectAnimLayer::Base, Loaded(Clip.Anim), Rate, true, 0.25f);
		}
	}
	else if (bIsCrouched)
	{
		UAnimSequenceBase* CrouchIdle = Loaded(CrouchIdleAnim);
		Anim->Play(EVelisectAnimLayer::Base, CrouchIdle, 0.f, false, 0.25f);
		if (CrouchIdle)
		{
			Anim->SetTime(EVelisectAnimLayer::Base, CrouchIdle->GetPlayLength());
		}
	}
	else
	{
		Anim->Play(EVelisectAnimLayer::Base, Loaded(IdleAnim), 0.f, true, 0.3f);
	}

	// The left hand holds the rifle except while reload and equip use it.
	const float LeftHand = bReloading || bEquipping ? 0.f : 1.f;
	Anim->SetLeftHandAlpha(LeftHand);
	if (UVelisectAnimInstance* Arms = GetArmsAnim())
	{
		Arms->SetLeftHandAlpha(LeftHand);
	}

	// Upper layer: weapon handling. One-shot clips (reload, equip, hit) own the layer until they finish.
	const bool bHitReacting = GetWorld()->GetTimeSeconds() < HitReactUntil;
	if (bReloading || bEquipping || bHitReacting)
	{
		return;
	}

	// Pose clips restart on change, so the aim pose can share the fire clip frozen on its first frame.
	auto SetUpperPose = [this](EUpperPose Pose, const TSoftObjectPtr<UAnimSequenceBase>& Clip, float Rate, float BlendTime)
	{
		if (UpperPose != Pose)
		{
			UpperPose = Pose;
			// The low-ready clip takes the rifle out of view: the arms keep aiming and UpdateViewmodel lowers them.
			PlayUpper(Loaded(Clip), Rate, true, BlendTime, true, Pose == EUpperPose::LowReady ? Loaded(AimPoseAnim) : nullptr);
		}
	};

	const bool bFiring = GetWorld()->GetTimeSeconds() - LastShotTime < FireInterval * 2.f;
	if (IsSprinting())
	{
		SetUpperPose(EUpperPose::LowReady, LowReadyAnim, 0.f, 0.25f);
	}
	else if (bFiring && !bProceduralFire)
	{
		SetUpperPose(EUpperPose::Fire, FireAnim, 1.f, 0.06f);
	}
	else
	{
		SetUpperPose(EUpperPose::Aim, AimPoseAnim, 0.f, 0.15f);
	}
}

void AVelisectCharacter::OnStartCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust)
{
	Super::OnStartCrouch(HalfHeightAdjust, ScaledHalfHeightAdjust);
	// The capsule centre just dropped; keep the eye where it was and ease it down instead.
	CameraBaseHeight += ScaledHalfHeightAdjust;
}

void AVelisectCharacter::OnEndCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust)
{
	Super::OnEndCrouch(HalfHeightAdjust, ScaledHalfHeightAdjust);
	CameraBaseHeight -= ScaledHalfHeightAdjust;
}

void AVelisectCharacter::UpdateCamera(float DeltaSeconds)
{
	if (bDead || !Controller)
	{
		return;
	}

	// Recoil: kick the view up, then let it settle.
	if (RecoilKick > KINDA_SMALL_NUMBER)
	{
		const float Step = FMath::Min(RecoilKick, DeltaSeconds * 18.f);
		FRotator Rotation = Controller->GetControlRotation();
		Rotation.Pitch = FMath::Clamp(FRotator::NormalizeAxis(Rotation.Pitch + Step), -80.f, 80.f);
		Controller->SetControlRotation(Rotation);
		RecoilKick -= Step;
	}

	// Head bob scales with ground speed.
	const float Speed = GetCharacterMovement()->IsMovingOnGround() ? GetVelocity().Size2D() : 0.f;
	BobPhase += DeltaSeconds * (Speed > 10.f ? 6.f + Speed * 0.012f : 1.2f);
	const float Amplitude = Speed > 10.f ? FMath::Clamp(Speed / SprintSpeed, 0.f, 1.f) * 2.2f : 0.25f;
	float TargetHeight = EyeHeight;
	float TargetForward = CameraOffset.X;
	if (bIsCrouched)
	{
		TargetHeight = CrouchedEyeHeight;
		if (!HeadBone.IsNone())
		{
			const FVector Head = GetCapsuleComponent()->GetComponentTransform().InverseTransformPosition(GetMesh()->GetBoneLocation(HeadBone));
			TargetHeight = Head.Z + CrouchedEyeAboveHead;
			TargetForward = Head.X + CrouchedEyeForward;
		}
	}
	CameraBaseHeight = FMath::FInterpTo(CameraBaseHeight, TargetHeight, DeltaSeconds, 10.f);
	CameraBaseForward = FMath::FInterpTo(CameraBaseForward, TargetForward, DeltaSeconds, 10.f);

	FVector Location = Camera->GetRelativeLocation();
	Location.Z = CameraBaseHeight + FMath::Sin(BobPhase * 2.f) * Amplitude * 0.5f;
	Location.X = CameraBaseForward;
	Location.Y = CameraOffset.Y + FMath::Sin(BobPhase) * Amplitude * 0.4f;
	Camera->SetRelativeLocation(Location);

	ViewSway = FMath::Vector2DInterpTo(ViewSway, FVector2D::ZeroVector, DeltaSeconds, 8.f);
	UpdateViewmodel(DeltaSeconds, Amplitude);
}

void AVelisectCharacter::UpdateViewmodel(float DeltaSeconds, float BobAmplitude)
{
	// Kick, sway and the sprint hold turn the rifle about the right hand (camera space); kick also slides it back, and
	// it bobs a little against the camera's own bob.
	SprintBlend = FMath::FInterpTo(SprintBlend, IsSprinting() && !bReloading ? 1.f : 0.f, DeltaSeconds, 9.f);
	const FVector Pivot = ViewmodelOffset.TransformPosition(FirstPersonArms->GetSocketTransform(RightHandBone, RTS_Component).GetLocation());
	const FRotator Turn = FRotator(ViewSway.Y + WeaponKick * 0.6f, ViewSway.X, ViewSway.X * 0.5f) + ViewmodelSprintTurn * SprintBlend;
	const FVector Slide = FVector(-WeaponKick * ViewmodelKickBack, FMath::Sin(BobPhase) * BobAmplitude * 0.3f, FMath::Sin(BobPhase * 2.f) * BobAmplitude * 0.2f) + ViewmodelSprintSlide * SprintBlend;
	const FTransform Motion = FTransform(-Pivot) * FTransform(Turn) * FTransform(Pivot + Slide);
	FirstPersonArms->SetRelativeTransform(ViewmodelOffset * Motion);
}
