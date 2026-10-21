#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "VelisectHUD.generated.h"

/** Canvas HUD: crosshair, hit marker, health, ammo, damage flash and death screen. */
UCLASS()
class VELISECT_API AVelisectHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void DrawHUD() override;

private:
	void DrawCrosshair(const class AVelisectCharacter& Player, const FVector2D& Center);
	void DrawStatus(const class AVelisectCharacter& Player);
};
