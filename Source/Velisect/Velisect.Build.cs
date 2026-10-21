using UnrealBuildTool;

public class Velisect : ModuleRules
{
	public Velisect(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput",
			"AIModule", "NavigationSystem", "GameplayTasks"
		});

		// code in subfolders (Private/Tests) includes the module's headers by name
		PrivateIncludePaths.Add(ModuleDirectory);
		// each file on its own: unity batches leak files' private helpers into each other
		bUseUnity = false;
	}
}
