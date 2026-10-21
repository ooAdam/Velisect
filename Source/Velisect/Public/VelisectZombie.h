#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "VelisectZombie.generated.h"

class AVelisectCharacter;
class UVelisectAnimInstance;
class UAnimSequenceBase;

UENUM(BlueprintType)
enum class EVelisectZombieState : uint8
{
	Idle,
	Wander,
	Scream,
	Chase,
	Attack,
	Dead
};

/** Backrooms zombie: wanders, screams when it spots the player, chases over the navmesh and claws. */
UCLASS()
class VELISECT_API AVelisectZombie : public ACharacter
{
	GENERATED_BODY()

public:
	AVelisectZombie();

	virtual void Tick(float DeltaSeconds) override;
	virtual float TakeDamage(float DamageAmount, const FDamageEvent& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;

	/** Alert this zombie if Location is within Radius. */
	void HearNoise(const FVector& Location, float Radius);

	bool IsDead() const { return State == EVelisectZombieState::Dead; }

protected:
	virtual void BeginPlay() override;
	virtual void OnConstruction(const FTransform& Transform) override;

	UPROPERTY(EditAnywhere, Category = "Velisect|Assets")
	TSoftObjectPtr<USkeletalMesh> BodyMeshAsset;

	UPROPERTY(EditAnywhere, Category = "Velisect|Animation")
	TSoftObjectPtr<UAnimSequenceBase> IdleAnim;

	UPROPERTY(EditAnywhere, Category = "Velisect|Animation")
	TSoftObjectPtr<UAnimSequenceBase> WalkAnim;

	UPROPERTY(EditAnywhere, Category = "Velisect|Animation")
	TSoftObjectPtr<UAnimSequenceBase> RunAnim;

	UPROPERTY(EditAnywhere, Category = "Velisect|Animation")
	TSoftObjectPtr<UAnimSequenceBase> ScreamAnim;

	UPROPERTY(EditAnywhere, Category = "Velisect|Animation")
	TArray<TSoftObjectPtr<UAnimSequenceBase>> AttackAnims;

	UPROPERTY(EditAnywhere, Category = "Velisect|Animation")
	TArray<TSoftObjectPtr<UAnimSequenceBase>> DeathAnims;

	/** Ground speeds (cm/s) the walk and run clips were authored at. */
	UPROPERTY(EditAnywhere, Category = "Velisect|Animation")
	float WalkNaturalSpeed = 34.f;

	UPROPERTY(EditAnywhere, Category = "Velisect|Animation")
	float RunNaturalSpeed = 304.f;

	UPROPERTY(EditAnywhere, Category = "Velisect|AI")
	float MaxHealth = 150.f;

	UPROPERTY(EditAnywhere, Category = "Velisect|AI")
	float SightRange = 2600.f;

	UPROPERTY(EditAnywhere, Category = "Velisect|AI")
	float WanderSpeed = 60.f;

	UPROPERTY(EditAnywhere, Category = "Velisect|AI")
	float ChaseSpeed = 300.f;

	UPROPERTY(EditAnywhere, Category = "Velisect|AI")
	float AttackRange = 140.f;

	UPROPERTY(EditAnywhere, Category = "Velisect|AI")
	float AttackDamage = 18.f;

	UPROPERTY(EditAnywhere, Category = "Velisect|AI")
	float HeadshotMultiplier = 3.f;

	/** Start out wandering instead of standing idle. */
	UPROPERTY(EditAnywhere, Category = "Velisect|AI")
	bool bWanders = true;

private:
	void LoadAssets();
	void SetState(EVelisectZombieState NewState);
	void Think();
	void UpdateAnimation();
	void BeginAttack();
	void ResolveAttackHit();
	void Die();
	bool CanSeePlayer() const;
	AVelisectCharacter* GetPlayer() const;
	UVelisectAnimInstance* GetVelisectAnim() const;
	UAnimSequenceBase* Loaded(const TSoftObjectPtr<UAnimSequenceBase>& Anim);

	UPROPERTY(Transient)
	TArray<TObjectPtr<UAnimSequenceBase>> LoadedAnims;

	EVelisectZombieState State = EVelisectZombieState::Idle;
	float Health = 150.f;
	float StateTime = 0.f;
	float ThinkCooldown = 0.f;
	float AttackDuration = 1.f;
	bool bAttackLanded = false;
	bool bHasScreamed = false;
	FVector WanderTarget = FVector::ZeroVector;
};
