// Content the C++ loads by path: a rename or a broken import fails here instead of silently in play.
#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "VelisectTypes.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "UObject/SoftObjectPtr.h"
#include "UObject/UnrealType.h"

namespace
{
	constexpr EAutomationTestFlags Content = EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter;

	const TCHAR* Blueprints[] = {
		TEXT("/Game/Velisect/Blueprints/BP_Player.BP_Player_C"),
		TEXT("/Game/Velisect/Blueprints/BP_Zombie.BP_Zombie_C"),
		TEXT("/Game/Velisect/Blueprints/BP_GameMode.BP_GameMode_C"),
	};

	/** Every soft object path reachable from Container's properties (structs and arrays included). */
	void CollectSoftPaths(const UStruct* Type, const void* Container, const FString& Prefix, TArray<TPair<FString, FSoftObjectPath>>& Out)
	{
		for (TFieldIterator<FProperty> It(Type); It; ++It)
		{
			const FProperty* Property = *It;
			for (int32 Index = 0; Index < Property->ArrayDim; ++Index)
			{
				const void* Value = Property->ContainerPtrToValuePtr<void>(Container, Index);
				const FString Name = Prefix + Property->GetName();
				if (const FSoftObjectProperty* Soft = CastField<FSoftObjectProperty>(Property))
				{
					Out.Emplace(Name, Soft->GetPropertyValue(Value).ToSoftObjectPath());
				}
				else if (const FStructProperty* Struct = CastField<FStructProperty>(Property))
				{
					CollectSoftPaths(Struct->Struct, Value, Name + TEXT("."), Out);
				}
				else if (const FArrayProperty* Array = CastField<FArrayProperty>(Property))
				{
					FScriptArrayHelper Helper(Array, Value);
					for (int32 Element = 0; Element < Helper.Num(); ++Element)
					{
						const FString ElementName = FString::Printf(TEXT("%s[%d]"), *Name, Element);
						if (const FSoftObjectProperty* InnerSoft = CastField<FSoftObjectProperty>(Array->Inner))
						{
							Out.Emplace(ElementName, InnerSoft->GetPropertyValue(Helper.GetRawPtr(Element)).ToSoftObjectPath());
						}
						else if (const FStructProperty* InnerStruct = CastField<FStructProperty>(Array->Inner))
						{
							CollectSoftPaths(InnerStruct->Struct, Helper.GetRawPtr(Element), ElementName + TEXT("."), Out);
						}
					}
				}
			}
		}
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVelisectSoftPathsTest, "Velisect.Content.SoftPaths", Content)

bool FVelisectSoftPathsTest::RunTest(const FString& Parameters)
{
	for (const TCHAR* Path : Blueprints)
	{
		const UClass* Class = LoadObject<UClass>(nullptr, Path);
		if (!TestNotNull(FString::Printf(TEXT("%s loads"), Path), Class))
		{
			continue;
		}
		TArray<TPair<FString, FSoftObjectPath>> Paths;
		CollectSoftPaths(Class, Class->GetDefaultObject(), TEXT(""), Paths);
		int32 Checked = 0;
		for (const TPair<FString, FSoftObjectPath>& Entry : Paths)
		{
			if (Entry.Value.IsNull())
			{
				continue;
			}
			TestNotNull(FString::Printf(TEXT("%s %s -> %s loads"), Path, *Entry.Key, *Entry.Value.ToString()), Entry.Value.TryLoad());
			++Checked;
		}
		AddInfo(FString::Printf(TEXT("%s: %d soft paths load"), Path, Checked));
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVelisectBonesTest, "Velisect.Content.Bones", Content)

bool FVelisectBonesTest::RunTest(const FString& Parameters)
{
	// The bones gameplay code finds by short name on each Mixamo rig.
	struct FRig
	{
		const TCHAR* Path;
		TArray<const TCHAR*> Bones;
	};
	const FRig Rigs[] = {
		{TEXT("/Game/Velisect/Characters/Player/SK_Player.SK_Player"), {TEXT("Spine"), TEXT("Spine1"), TEXT("Spine2"), TEXT("Head"), TEXT("RightHand")}},
		{TEXT("/Game/Velisect/Characters/Zombie/SK_Zombie.SK_Zombie"), {TEXT("Spine"), TEXT("Head")}},
	};
	for (const FRig& Rig : Rigs)
	{
		USkeletalMesh* Mesh = LoadObject<USkeletalMesh>(nullptr, Rig.Path);
		if (!TestNotNull(FString::Printf(TEXT("%s loads"), Rig.Path), Mesh))
		{
			continue;
		}
		TestNotNull(FString::Printf(TEXT("%s has a physics asset (shots trace its bodies)"), Rig.Path), Mesh->GetPhysicsAsset());
		USkeletalMeshComponent* Component = NewObject<USkeletalMeshComponent>();
		Component->SetSkeletalMeshAsset(Mesh);
		for (const TCHAR* Bone : Rig.Bones)
		{
			TestFalse(FString::Printf(TEXT("%s finds %s"), Rig.Path, Bone), Velisect::FindBone(Component, Bone).IsNone());
		}
	}
	return true;
}

#endif
