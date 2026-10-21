#include "VelisectZombie.h"

#include "AIController.h"
#include "NavigationSystem.h"
#include "VelisectAnimInstance.h"
#include "VelisectCharacter.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/DamageEvents.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/DamageType.h"
#include "Kismet/GameplayStatics.h"
#include "Navigation/PathFollowingComponent.h"

namespace
{
	TSoftObjectPtr<UAnimSequenceBase> ZombieAnim(const TCHAR* Name)
	{
		return TSoftObjectPtr<UAnimSequenceBase>(FSoftObjectPath(FString::Printf(TEXT("/Game/Velisect/Characters/Zombie/Animations/%s.%s"), Name, Name)));
	}
}

AVelisectZombie::AVelisectZombie()
{
	PrimaryActorTick.bCanEverTick = true;
	AIControllerClass = AAIController::StaticClass();
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;

	GetCapsuleComponent()->InitCapsuleSize(38.f, 100.f);
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);

	// Shots trace against the physics-asset bodies so headshots know which bone they hit.
	GetMesh()->SetRelativeLocationAndRotation(FVector(0.f, 0.f, -100.f), FRotator(0.f, -90.f, 0.f));
	GetMesh()->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	GetMesh()->SetCollisionResponseToAllChannels(ECR_Ignore);
	GetMesh()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	GetMesh()->SetAnimInstanceClass(UVelisectAnimInstance::StaticClass());
	GetMesh()->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;

	bUseControllerRotationYaw = false;
	UCharacterMovementComponent* Movement = GetCharacterMovement();
	Movement->bOrientRotationToMovement = true;
	Movement->RotationRate = FRotator(0.f, 300.f, 0.f);
	Movement->MaxWalkSpeed = WanderSpeed;
	Movement->bUseRVOAvoidance = true;
	Movement->AvoidanceConsiderationRadius = 150.f;

	BodyMeshAsset = TSoftObjectPtr<USkeletalMesh>(FSoftObjectPath(TEXT("/Game/Velisect/Characters/Zombie/SK_Zombie.SK_Zombie")));
	IdleAnim = ZombieAnim(TEXT("A_Zombie_Idle"));
	WalkAnim = ZombieAnim(TEXT("A_Zombie_Walk"));
	RunAnim = ZombieAnim(TEXT("A_Zombie_Run"));
	ScreamAnim = ZombieAnim(TEXT("A_Zombie_Scream"));
	AttackAnims = {ZombieAnim(TEXT("A_Zombie_Attack")), ZombieAnim(TEXT("A_Zombie_Biting"))};
	DeathAnims = {ZombieAnim(TEXT("A_Zombie_Death")), ZombieAnim(TEXT("A_Zombie_Dying"))};
}

void AVelisectZombie::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	LoadAssets();
}

void AVelisectZombie::BeginPlay()
{
	Super::BeginPlay();
	LoadAssets();
	Health = MaxHealth;
	ThinkCooldown = FMath::FRandRange(0.f, 0.3f);
	SetState(bWanders ? EVelisectZombieState::Wander : EVelisectZombieState::Idle);
}

void AVelisectZombie::LoadAssets()
{
	if (USkeletalMesh* Body = BodyMeshAsset.LoadSynchronous(); Body && GetMesh()->GetSkeletalMeshAsset() != Body)
	{
		GetMesh()->SetSkeletalMesh(Body);
		GetMesh()->SetAnimInstanceClass(UVelisectAnimInstance::StaticClass());
	}
	// Show the idle pose in the editor too.
	if (UVelisectAnimInstance* Anim = GetVelisectAnim(); Anim && !Anim->GetActiveAnim(EVelisectAnimLayer::Base))
	{
		Anim->Play(EVelisectAnimLayer::Base, Loaded(IdleAnim), 1.f, true, 0.f);
	}
}

UVelisectAnimInstance* AVelisectZombie::GetVelisectAnim() const
{
	return Cast<UVelisectAnimInstance>(GetMesh()->GetAnimInstance());
}

UAnimSequenceBase* AVelisectZombie::Loaded(const TSoftObjectPtr<UAnimSequenceBase>& Anim)
{
	UAnimSequenceBase* Sequence = Anim.LoadSynchronous();
	if (Sequence)
	{
		LoadedAnims.AddUnique(Sequence);
	}
	return Sequence;
}

AVelisectCharacter* AVelisectZombie::GetPlayer() const
{
	return Cast<AVelisectCharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
}

bool AVelisectZombie::CanSeePlayer() const
{
	const AVelisectCharacter* Player = GetPlayer();
	const AAIController* AI = GetController<AAIController>();
	if (!Player || Player->IsDead() || !AI)
	{
		return false;
	}
	const FVector ToPlayer = Player->GetActorLocation() - GetActorLocation();
	const float Distance = ToPlayer.Size();
	if (Distance > SightRange)
	{
		return false;
	}
	// Close enough to sense from any direction; otherwise it has to be roughly in front.
	const bool bInView = Distance < 450.f || FVector::DotProduct(GetActorForwardVector(), ToPlayer.GetSafeNormal()) > 0.1f;
	return bInView && AI->LineOfSightTo(Player);
}

void AVelisectZombie::HearNoise(const FVector& Location, float Radius)
{
	if ((State == EVelisectZombieState::Idle || State == EVelisectZombieState::Wander) && FVector::Dist(Location, GetActorLocation()) <= Radius)
	{
		SetState(bHasScreamed ? EVelisectZombieState::Chase : EVelisectZombieState::Scream);
	}
}

void AVelisectZombie::SetState(EVelisectZombieState NewState)
{
	State = NewState;
	StateTime = 0.f;

	AAIController* AI = GetController<AAIController>();
	UVelisectAnimInstance* Anim = GetVelisectAnim();
	switch (State)
	{
	case EVelisectZombieState::Idle:
	case EVelisectZombieState::Wander:
		GetCharacterMovement()->MaxWalkSpeed = WanderSpeed;
		break;

	case EVelisectZombieState::Scream:
		bHasScreamed = true;
		if (AI)
		{
			AI->StopMovement();
		}
		if (Anim)
		{
			const float Duration = Anim->Play(EVelisectAnimLayer::Base, Loaded(ScreamAnim), 1.2f, false, 0.2f, true);
			AttackDuration = FMath::Max(Duration, 0.5f);
		}
		break;

	case EVelisectZombieState::Chase:
		GetCharacterMovement()->MaxWalkSpeed = ChaseSpeed;
		ThinkCooldown = 0.f;
		break;

	case EVelisectZombieState::Attack:
		BeginAttack();
		break;

	case EVelisectZombieState::Dead:
		break;
	}
}

void AVelisectZombie::BeginAttack()
{
	if (AAIController* AI = GetController<AAIController>())
	{
		AI->StopMovement();
	}
	bAttackLanded = false;
	AttackDuration = 1.2f;
	if (UVelisectAnimInstance* Anim = GetVelisectAnim(); Anim && AttackAnims.Num() > 0)
	{
		const TSoftObjectPtr<UAnimSequenceBase>& Clip = AttackAnims[FMath::RandRange(0, AttackAnims.Num() - 1)];
		AttackDuration = FMath::Min(Anim->Play(EVelisectAnimLayer::Base, Loaded(Clip), 1.5f, false, 0.15f, true), 2.2f);
	}
}

void AVelisectZombie::ResolveAttackHit()
{
	bAttackLanded = true;
	AVelisectCharacter* Player = GetPlayer();
	if (Player && !Player->IsDead() && FVector::Dist2D(Player->GetActorLocation(), GetActorLocation()) <= AttackRange + 60.f)
	{
		UGameplayStatics::ApplyDamage(Player, AttackDamage, GetController(), this, UDamageType::StaticClass());
	}
}

void AVelisectZombie::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (State == EVelisectZombieState::Dead)
	{
		return;
	}

	StateTime += DeltaSeconds;
	ThinkCooldown -= DeltaSeconds;
	if (ThinkCooldown <= 0.f)
	{
		ThinkCooldown = 0.25f;
		Think();
	}

	AVelisectCharacter* Player = GetPlayer();
	const bool bFacePlayer = State == EVelisectZombieState::Scream || (State == EVelisectZombieState::Attack && StateTime < AttackDuration * 0.4f);
	if (bFacePlayer && Player)
	{
		const FRotator Target = (Player->GetActorLocation() - GetActorLocation()).Rotation();
		SetActorRotation(FMath::RInterpTo(GetActorRotation(), FRotator(0.f, Target.Yaw, 0.f), DeltaSeconds, 6.f));
	}

	if (State == EVelisectZombieState::Attack)
	{
		if (!bAttackLanded && StateTime >= AttackDuration * 0.45f)
		{
			ResolveAttackHit();
		}
		if (StateTime >= AttackDuration)
		{
			SetState(EVelisectZombieState::Chase);
			// Brief recovery before it can swing again.
			ThinkCooldown = 0.45f;
		}
	}
	else if (State == EVelisectZombieState::Scream && StateTime >= AttackDuration)
	{
		SetState(EVelisectZombieState::Chase);
	}

	UpdateAnimation();
}

void AVelisectZombie::Think()
{
	AAIController* AI = GetController<AAIController>();
	AVelisectCharacter* Player = GetPlayer();
	if (!AI)
	{
		return;
	}

	switch (State)
	{
	case EVelisectZombieState::Idle:
	case EVelisectZombieState::Wander:
		if (CanSeePlayer())
		{
			SetState(bHasScreamed ? EVelisectZombieState::Chase : EVelisectZombieState::Scream);
			return;
		}
		if (State == EVelisectZombieState::Wander && (StateTime > 8.f || AI->GetMoveStatus() == EPathFollowingStatus::Idle))
		{
			if (const UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld()))
			{
				FNavLocation Point;
				if (Nav->GetRandomReachablePointInRadius(GetActorLocation(), 1200.f, Point))
				{
					AI->MoveToLocation(Point.Location, 50.f);
					StateTime = 0.f;
				}
			}
		}
		break;

	case EVelisectZombieState::Chase:
		if (!Player || Player->IsDead())
		{
			SetState(EVelisectZombieState::Wander);
			return;
		}
		if (FVector::Dist2D(Player->GetActorLocation(), GetActorLocation()) <= AttackRange)
		{
			SetState(EVelisectZombieState::Attack);
			return;
		}
		AI->MoveToActor(Player, AttackRange * 0.6f, true, true, false);
		break;

	default:
		break;
	}
}

void AVelisectZombie::UpdateAnimation()
{
	UVelisectAnimInstance* Anim = GetVelisectAnim();
	if (!Anim || State == EVelisectZombieState::Scream || State == EVelisectZombieState::Attack)
	{
		return;
	}

	const float Speed = GetVelocity().Size2D();
	if (Speed < 10.f)
	{
		Anim->Play(EVelisectAnimLayer::Base, Loaded(IdleAnim), 1.f, true, 0.3f);
	}
	else if (State == EVelisectZombieState::Chase)
	{
		Anim->Play(EVelisectAnimLayer::Base, Loaded(RunAnim), FMath::Clamp(Speed / RunNaturalSpeed, 0.5f, 1.5f), true, 0.25f);
	}
	else
	{
		Anim->Play(EVelisectAnimLayer::Base, Loaded(WalkAnim), FMath::Clamp(Speed / WalkNaturalSpeed, 0.6f, 2.f), true, 0.3f);
	}
}

float AVelisectZombie::TakeDamage(float DamageAmount, const FDamageEvent& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	if (State == EVelisectZombieState::Dead)
	{
		return 0.f;
	}

	float Amount = DamageAmount;
	if (DamageEvent.IsOfType(FPointDamageEvent::ClassID))
	{
		const FPointDamageEvent& Point = static_cast<const FPointDamageEvent&>(DamageEvent);
		if (Point.HitInfo.BoneName.ToString().Contains(TEXT("Head")))
		{
			Amount *= HeadshotMultiplier;
		}
	}

	Health -= Amount;
	if (Health <= 0.f)
	{
		Die();
	}
	else if (State == EVelisectZombieState::Idle || State == EVelisectZombieState::Wander)
	{
		// Getting shot skips the scream and goes straight for the shooter.
		bHasScreamed = true;
		SetState(EVelisectZombieState::Chase);
	}
	return Amount;
}

void AVelisectZombie::Die()
{
	SetState(EVelisectZombieState::Dead);
	if (AAIController* AI = GetController<AAIController>())
	{
		AI->StopMovement();
	}
	GetCharacterMovement()->DisableMovement();
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	if (UVelisectAnimInstance* Anim = GetVelisectAnim(); Anim && DeathAnims.Num() > 0)
	{
		Anim->Play(EVelisectAnimLayer::Base, Loaded(DeathAnims[FMath::RandRange(0, DeathAnims.Num() - 1)]), 1.f, false, 0.15f, true);
	}
	SetLifeSpan(45.f);
}
