#include "VelisectHUD.h"

#include "VelisectCharacter.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"

namespace
{
	const FLinearColor HudWhite(0.95f, 0.93f, 0.82f, 0.9f);
	const FLinearColor HudRed(0.85f, 0.08f, 0.05f, 1.f);
}

void AVelisectHUD::DrawHUD()
{
	Super::DrawHUD();

	const AVelisectCharacter* Player = Cast<AVelisectCharacter>(GetOwningPawn());
	if (!Player || !Canvas)
	{
		return;
	}

	const FVector2D Center(Canvas->ClipX * 0.5f, Canvas->ClipY * 0.5f);

	// Red flash that fades after taking damage, plus a persistent tint when badly hurt.
	const float SinceDamage = Player->GetTimeSinceDamaged();
	const float LowHealth = 1.f - FMath::Clamp(Player->GetHealth() / Player->GetMaxHealth() / 0.35f, 0.f, 1.f);
	const float FlashAlpha = FMath::Max(FMath::Clamp(0.45f - SinceDamage, 0.f, 0.45f), LowHealth * 0.18f);
	if (FlashAlpha > 0.f)
	{
		DrawRect(FLinearColor(0.6f, 0.f, 0.f, FlashAlpha), 0.f, 0.f, Canvas->ClipX, Canvas->ClipY);
	}

	if (Player->IsDead())
	{
		DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.45f), 0.f, 0.f, Canvas->ClipX, Canvas->ClipY);
		UFont* Font = GEngine->GetLargeFont();
		const FString Text = TEXT("YOU DIED");
		float Width = 0.f, Height = 0.f;
		GetTextSize(Text, Width, Height, Font, 3.f);
		DrawText(Text, HudRed, Center.X - Width * 0.5f, Center.Y - Height * 0.5f, Font, 3.f);
		return;
	}

	DrawCrosshair(*Player, Center);
	DrawStatus(*Player);
}

void AVelisectHUD::DrawCrosshair(const AVelisectCharacter& Player, const FVector2D& Center)
{
	if (Player.IsSprinting())
	{
		return;
	}

	const float Gap = 6.f + FMath::Clamp(Player.GetVelocity().Size2D() / 40.f, 0.f, 10.f);
	const float Length = 8.f;
	DrawLine(Center.X - Gap - Length, Center.Y, Center.X - Gap, Center.Y, HudWhite, 2.f);
	DrawLine(Center.X + Gap, Center.Y, Center.X + Gap + Length, Center.Y, HudWhite, 2.f);
	DrawLine(Center.X, Center.Y - Gap - Length, Center.X, Center.Y - Gap, HudWhite, 2.f);
	DrawLine(Center.X, Center.Y + Gap, Center.X, Center.Y + Gap + Length, HudWhite, 2.f);

	if (Player.GetTimeSinceHitConfirm() < 0.15f)
	{
		const float A = 5.f, B = 11.f;
		DrawLine(Center.X - B, Center.Y - B, Center.X - A, Center.Y - A, HudRed, 2.f);
		DrawLine(Center.X + B, Center.Y - B, Center.X + A, Center.Y - A, HudRed, 2.f);
		DrawLine(Center.X - B, Center.Y + B, Center.X - A, Center.Y + A, HudRed, 2.f);
		DrawLine(Center.X + B, Center.Y + B, Center.X + A, Center.Y + A, HudRed, 2.f);
	}
}

void AVelisectHUD::DrawStatus(const AVelisectCharacter& Player)
{
	UFont* Font = GEngine->GetMediumFont();
	const float Margin = 40.f;
	const float Bottom = Canvas->ClipY - Margin;

	// Health bar, bottom left.
	const float BarWidth = 260.f, BarHeight = 12.f;
	const float HealthFraction = FMath::Clamp(Player.GetHealth() / Player.GetMaxHealth(), 0.f, 1.f);
	DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.5f), Margin, Bottom - BarHeight, BarWidth, BarHeight);
	DrawRect(FLinearColor::LerpUsingHSV(HudRed, FLinearColor(0.85f, 0.8f, 0.45f, 1.f), HealthFraction), Margin, Bottom - BarHeight, BarWidth * HealthFraction, BarHeight);
	DrawText(FString::Printf(TEXT("HEALTH  %d"), FMath::CeilToInt(Player.GetHealth())), HudWhite, Margin, Bottom - BarHeight - 26.f, Font, 1.2f);

	// Ammo, bottom right.
	const FString Ammo = FString::Printf(TEXT("%d / %d"), Player.GetAmmoInMagazine(), Player.GetReserveAmmo());
	float Width = 0.f, Height = 0.f;
	GetTextSize(Ammo, Width, Height, Font, 2.f);
	const FLinearColor AmmoColor = Player.GetAmmoInMagazine() == 0 ? HudRed : HudWhite;
	DrawText(Ammo, AmmoColor, Canvas->ClipX - Margin - Width, Bottom - Height, Font, 2.f);

	if (Player.IsReloading())
	{
		const FString Text = TEXT("RELOADING");
		GetTextSize(Text, Width, Height, Font, 1.2f);
		DrawText(Text, HudWhite, Canvas->ClipX * 0.5f - Width * 0.5f, Canvas->ClipY * 0.5f + 40.f, Font, 1.2f);
	}
	else if (Player.GetAmmoInMagazine() == 0)
	{
		const FString Text = Player.GetReserveAmmo() > 0 ? TEXT("PRESS R TO RELOAD") : TEXT("OUT OF AMMO");
		GetTextSize(Text, Width, Height, Font, 1.2f);
		DrawText(Text, HudRed, Canvas->ClipX * 0.5f - Width * 0.5f, Canvas->ClipY * 0.5f + 40.f, Font, 1.2f);
	}
}
