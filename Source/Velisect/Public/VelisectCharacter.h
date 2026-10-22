#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "VelisectTypes.h"
#include "VelisectCharacter.generated.h"

class UCameraComponent;
class UStaticMeshComponent;
class USpotLightComponent;
class UPointLightComponent;
class UInputAction;
class UInputMappingContext;
class UMaterialInterface;
class USoundBase;
class UVelisectAnimInstance;
struct FInputActionValue;

/**
 * First-person player. The view shows arms and a rifle on the camera (first-person primitives with their own FOV and
 * scale, so they never clip into walls); the full Mixamo body is the world representation (shadow, death cam).
 */
UCLASS()
class VELISECT_API AVelisectCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	AVelisectCharacter();

	virtual void Tick(float DeltaSeconds) override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual float TakeDamage(float DamageAmount, const FDamageEvent& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;

	float GetHealth() const { return Health; }
	float GetMaxHealth() const { return MaxHealth; }
	int32 GetAmmoInMagazine() const { return AmmoInMagazine; }
	int32 GetReserveAmmo() const { return ReserveAmmo; }
	bool IsDead() const { return bDead; }
	bool IsReloading() const { return bReloading; }
	bool IsSprinting() const;
	/** Seconds since the last shot that hit an enemy (for the HUD hit marker). */
	float GetTimeSinceHitConfirm() const;
	/** Seconds since the player last took damage (for the HUD damage flash). */
	float GetTimeSinceDamaged() const;

	/** Console: start a reload (for checking the reload on screen without input). */
	UFUNCTION(Exec)
	void VsReload();

	/** Console: empty the magazine and reload (the empty reload racks the charging handle). */
	UFUNCTION(Exec)
	void VsReloadEmpty();

protected:
	virtual void BeginPlay() override;
	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void OnStartCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust) override;
	virtual void OnEndCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Velisect")
	TObjectPtr<UCameraComponent> Camera;

	/** Arms-only cut of the body, playing the first-person clips, framed on the camera. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Velisect")
	TObjectPtr<USkeletalMeshComponent> FirstPersonArms;

	/** The rifle the player sees, in the first-person arms' right hand; its own takes move the magazines and bolt. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Velisect")
	TObjectPtr<USkeletalMeshComponent> Weapon;

	/** The body's rifle: its shadow, and what the death cam sees. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Velisect")
	TObjectPtr<UStaticMeshComponent> WorldWeapon;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Velisect")
	TObjectPtr<USpotLightComponent> Flashlight;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Velisect")
	TObjectPtr<UPointLightComponent> MuzzleLight;

	// ---- Assets ----

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Assets")
	TSoftObjectPtr<USkeletalMesh> BodyMeshAsset;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Assets")
	TSoftObjectPtr<USkeletalMesh> ArmsMeshAsset;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Assets")
	TSoftObjectPtr<UStaticMesh> WeaponMeshAsset;

	/** The first-person rifle: SM_Rifle's mesh rigged with magazine, spare magazine, bolt and trigger bones. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Assets")
	TSoftObjectPtr<USkeletalMesh> ViewmodelWeaponAsset;

	/** The body's rifle relative to the body's right hand bone. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Assets")
	FTransform WeaponGripOffset;

	/** The first-person rifle relative to the arms' right hand bone (the authored hold). */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Assets")
	FTransform ViewmodelGripOffset;

	/** Centre of the pistol grip in weapon mesh space (where the right palm sits). */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Assets")
	FVector PistolGrip = FVector(0.f, 17.8f, 10.3f);

	/** Muzzle position in weapon mesh space. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Assets")
	FVector MuzzleOffset = FVector(0.f, 60.f, 5.f);

	// ---- Animation ----

	/** Shouldered rifle pose held on the upper body while idle or moving. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	TSoftObjectPtr<UAnimSequenceBase> AimPoseAnim;

	/** Lowered rifle pose held on the upper body while sprinting. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	TSoftObjectPtr<UAnimSequenceBase> LowReadyAnim;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	TSoftObjectPtr<UAnimSequenceBase> FireAnim;

	/** Hold the aim pose while firing and kick the spine per shot instead of playing FireAnim. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	bool bProceduralFire = true;

	/** Degrees the rifle kicks up per shot when bProceduralFire is set. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	float WeaponKickPerShot = 2.f;

	/** The body's reload (its shadow), stretched to the first-person reload's length. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	TSoftObjectPtr<UAnimSequenceBase> ReloadAnim;

	/** First-person takes (export_fp.py): the hold (a breathing loop), the draw, the reloads and the rifle's bolt cycle. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Viewmodel")
	FVelisectViewmodelClip ViewmodelIdle;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Viewmodel")
	FVelisectViewmodelClip ViewmodelEquip;

	/** Rounds left: swap the magazine. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Viewmodel")
	FVelisectViewmodelClip ViewmodelReload;

	/** Empty: swap the magazine and rack the charging handle. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Viewmodel")
	FVelisectViewmodelClip ViewmodelReloadEmpty;

	/** Played on the rifle per shot (the bolt carrier cycles). */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Viewmodel")
	FVelisectViewmodelClip ViewmodelFire;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	TSoftObjectPtr<UAnimSequenceBase> EquipAnim;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	TSoftObjectPtr<UAnimSequenceBase> HitReactAnim;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	TSoftObjectPtr<UAnimSequenceBase> DeathAnim;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	TSoftObjectPtr<UAnimSequenceBase> IdleAnim;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	TSoftObjectPtr<UAnimSequenceBase> CrouchIdleAnim;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	TSoftObjectPtr<UAnimSequenceBase> JumpAnim;

	/** Standing locomotion by direction: F, FR, R, BR, B, BL, L, FL. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	TArray<FVelisectLocoClip> MoveClips;

	/** Crouched locomotion by direction: F, FR, R, BR, B, BL, L, FL. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	TArray<FVelisectLocoClip> CrouchMoveClips;

	/** Degrees of aim pitch applied through the spine; flip the sign if the rifle bends the wrong way. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	float AimPitchScale = 1.f;

	/** Pitch trim (degrees) through the spine, applied after AimPitchScale, so the barrel lines up with the crosshair. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	float AimPitchOffset = 0.f;

	/** Yaw trim (degrees) through the spine so the barrel converges on the crosshair. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	float AimYawOffset = 0.f;

	/** Body offset from the default capsule placement (X forward, Y right, Z up); moves the arms and rifle in view. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Camera")
	FVector BodyOffset = FVector::ZeroVector;

	/** Camera offset from the capsule centre (X forward, Y right); height comes from EyeHeight. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Camera")
	FVector2D CameraOffset = FVector2D(14.f, 0.f);

	/** First-person arms relative to the camera (X forward, Y right, Z up); frames the rifle in the aim pose. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Viewmodel")
	FTransform ViewmodelOffset;

	/** Horizontal field of view the arms and rifle are drawn with. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Viewmodel")
	float ViewmodelFieldOfView = 70.f;

	/** Arms and rifle shrink towards the camera by this much so they never poke into walls (looks the same on screen). */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Viewmodel")
	float ViewmodelScale = 0.6f;

	/** Where the left hand holds the rifle (rifle mesh space): it holds it the way the right hand holds PistolGrip, mirrored. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Viewmodel")
	FVector LeftHandGrip = FVector::ZeroVector;

	/** Turns the left hand's hold about LeftHandGrip (rifle space), e.g. upright for a vertical foregrip. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Viewmodel")
	FRotator LeftHandTwist = FRotator::ZeroRotator;

	/** Where the left elbow swings, as a nudge from the clip's elbow (arms mesh space: X left, Y forward, Z up). */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Viewmodel")
	FVector LeftElbowHint = FVector::ZeroVector;

	/** While sprinting the arms keep the aim pose and the rifle drops and tilts by this (camera space, about the right hand). */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Viewmodel")
	FVector ViewmodelSprintSlide = FVector::ZeroVector;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Viewmodel")
	FRotator ViewmodelSprintTurn = FRotator::ZeroRotator;

	/** Centimetres the rifle slides back per degree of WeaponKick. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Viewmodel")
	float ViewmodelKickBack = 1.f;

	/** Degrees the rifle trails the view per degree turned, and the most it trails. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Viewmodel")
	float ViewmodelSway = 0.35f;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Viewmodel")
	float ViewmodelMaxSway = 2.5f;

	// ---- Movement ----

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Movement")
	float WalkSpeed = 280.f;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Movement")
	float SprintSpeed = 600.f;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Movement")
	float CrouchSpeed = 160.f;

	/** Camera height above the capsule centre while standing. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Movement")
	float EyeHeight = 72.f;

	/** While crouched the camera follows the head bone (crouch clips vary a lot in hip placement), offset by these. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Movement")
	float CrouchedEyeAboveHead = 8.f;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Movement")
	float CrouchedEyeForward = 8.f;

	// ---- Weapon ----

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Weapon")
	float FireInterval = 0.1f;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Weapon")
	float Damage = 25.f;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Weapon")
	float Range = 6000.f;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Weapon")
	int32 MagazineSize = 30;

	/** Playback rate of the first-person reloads. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Weapon")
	float ReloadPlayRate = 1.f;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Weapon")
	float RecoilPitch = 0.45f;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Weapon")
	float SpreadDegrees = 0.8f;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Weapon")
	TSoftObjectPtr<USoundBase> FireSound;

	/** Zombies within this radius hear each shot. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Weapon")
	float NoiseRadius = 1800.f;

	/** Decal left where shots hit the level. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Weapon")
	TSoftObjectPtr<UMaterialInterface> ImpactDecalMaterial;

	// ---- Health ----

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Health")
	float MaxHealth = 100.f;

private:
	/** What the upper body is showing; one-shot clips (reload, equip, hit) own the layer until they end. */
	enum class EUpperPose : uint8
	{
		OneShot,
		Aim,
		Fire,
		LowReady
	};

	void LoadAssets();
	void BuildInput();
	void UpdateAnimation(float DeltaSeconds);
	void UpdateCamera(float DeltaSeconds);
	void UpdateViewmodel(float DeltaSeconds, float BobAmplitude);
	void SetupAnim(UVelisectAnimInstance* Anim, const USkeletalMeshComponent* Skeleton) const;
	/** Plays a clip on the body's upper body; returns its duration. */
	float PlayUpper(UAnimSequenceBase* Clip, float Rate, bool bLoop, float BlendTime, bool bRestart);
	/** Plays a first-person take on the arms and the rifle together; returns its duration. */
	float PlayViewmodel(const FVelisectViewmodelClip& Clip, bool bLoop, float BlendTime, float Rate = 1.f);
	UVelisectAnimInstance* GetVelisectAnim() const;
	UVelisectAnimInstance* GetArmsAnim() const;
	UAnimSequenceBase* Loaded(const TSoftObjectPtr<UAnimSequenceBase>& Anim);

	void Move(const FInputActionValue& Value);
	void Look(const FInputActionValue& Value);
	void StartSprint();
	void StopSprint();
	void ToggleCrouch();
	void StartFire();
	void StopFire();
	void Reload();
	void ToggleFlashlight();

	void FireShot();
	void FinishReload();
	void FinishEquip();
	void Die();

	UPROPERTY(Transient)
	TArray<TObjectPtr<UAnimSequenceBase>> LoadedAnims;

	UPROPERTY(Transient)
	TObjectPtr<UInputMappingContext> InputContext;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> MoveAction;
	UPROPERTY(Transient)
	TObjectPtr<UInputAction> LookAction;
	UPROPERTY(Transient)
	TObjectPtr<UInputAction> JumpAction;
	UPROPERTY(Transient)
	TObjectPtr<UInputAction> SprintAction;
	UPROPERTY(Transient)
	TObjectPtr<UInputAction> CrouchAction;
	UPROPERTY(Transient)
	TObjectPtr<UInputAction> FireAction;
	UPROPERTY(Transient)
	TObjectPtr<UInputAction> ReloadAction;
	UPROPERTY(Transient)
	TObjectPtr<UInputAction> FlashlightAction;

	FVector2D MoveInput = FVector2D::ZeroVector;
	EUpperPose UpperPose = EUpperPose::OneShot;
	float CameraBaseHeight = 72.f;
	float CameraBaseForward = 0.f;
	float Health = 100.f;
	int32 AmmoInMagazine = 30;
	int32 ReserveAmmo = 120;
	bool bWantsSprint = false;
	bool bTriggerHeld = false;
	bool bReloading = false;
	bool bEquipping = false;
	bool bDead = false;
	double LastShotTime = -1000.0;
	double LastHitConfirmTime = -1000.0;
	double LastDamagedTime = -1000.0;
	float HitReactUntil = 0.f;
	float BobPhase = 0.f;
	float RecoilKick = 0.f;
	float WeaponKick = 0.f;
	/** Degrees the viewmodel trails the view: X yaw, Y pitch. */
	FVector2D ViewSway = FVector2D::ZeroVector;
	/** 0..1 towards the sprint hold of the viewmodel. */
	float SprintBlend = 0.f;
	FName RightHandBone;
	FName HeadBone;
	FTimerHandle FireTimer;
	FTimerHandle ReloadTimer;
	FTimerHandle EquipTimer;
	FTimerHandle MuzzleTimer;
};
