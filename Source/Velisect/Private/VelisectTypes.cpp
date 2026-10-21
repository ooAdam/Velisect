#include "VelisectTypes.h"

#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "ReferenceSkeleton.h"

FName Velisect::FindBone(const USkeletalMeshComponent* Mesh, const TCHAR* ShortName)
{
	if (!Mesh || !Mesh->GetSkeletalMeshAsset())
	{
		return NAME_None;
	}

	const FReferenceSkeleton& RefSkeleton = Mesh->GetSkeletalMeshAsset()->GetRefSkeleton();
	const FString Colon = FString(TEXT(":")) + ShortName;
	const FString Underscore = FString(TEXT("_")) + ShortName;
	for (int32 Index = 0; Index < RefSkeleton.GetNum(); ++Index)
	{
		const FName Name = RefSkeleton.GetBoneName(Index);
		const FString NameString = Name.ToString();
		if (NameString.Equals(ShortName, ESearchCase::IgnoreCase)
			|| NameString.EndsWith(Colon, ESearchCase::IgnoreCase)
			|| NameString.EndsWith(Underscore, ESearchCase::IgnoreCase))
		{
			return Name;
		}
	}
	return NAME_None;
}
