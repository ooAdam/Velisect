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

/** True first-person player: full Mixamo body under the camera (head hidden) holding the rifle. */
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

protected:
	virtual void BeginPlay() override;
	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void OnStartCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust) override;
	virtual void OnEndCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Velisect")
	TObjectPtr<UCameraComponent> Camera;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Velisect")
	TObjectPtr<UStaticMeshComponent> Weapon;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Velisect")
	TObjectPtr<USpotLightComponent> Flashlight;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Velisect")
	TObjectPtr<UPointLightComponent> MuzzleLight;

	// ---- Assets ----

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Assets")
	TSoftObjectPtr<USkeletalMesh> BodyMeshAsset;

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Assets")
	TSoftObjectPtr<UStaticMesh> WeaponMeshAsset;

	/** Rifle placement relative to the right hand bone. */
	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Assets")
	FTransform WeaponGripOffset;

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

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Animation")
	TSoftObjectPtr<UAnimSequenceBase> ReloadAnim;

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

	UPROPERTY(EditDefaultsOnly, Category = "Velisect|Weapon")
	float ReloadPlayRate = 1.35f;

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
	UVelisectAnimInstance* GetVelisectAnim() const;
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
	FName RightHandBone;
	FName HeadBone;
	FTimerHandle FireTimer;
	FTimerHandle ReloadTimer;
	FTimerHandle EquipTimer;
	FTimerHandle MuzzleTimer;
};
