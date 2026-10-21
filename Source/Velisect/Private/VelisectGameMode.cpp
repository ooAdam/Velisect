#include "VelisectGameMode.h"

#include "VelisectCharacter.h"
#include "VelisectHUD.h"

AVelisectGameMode::AVelisectGameMode()
{
	DefaultPawnClass = AVelisectCharacter::StaticClass();
	HUDClass = AVelisectHUD::StaticClass();
}
