#!/usr/bin/env bash
# Compile-checks the Unity project's C# without Unity or a license.
#
# - Compiler: Roslyn from Ubuntu's packaged .NET 8 SDK (apt install dotnet-sdk-8.0).
# - API: Unity 6000.3.8f1's own reference libraries, taken from GameCI's public editor image
#   (unityci/editor:ubuntu-6000.3.8f1-base-3). They are read as compiler metadata only, never run.
#   The image layer is checked against its SHA-256 digest, kept in .refcache/ (gitignored), and never committed.
#
# Usage: tests/unity_compile.sh        Exit code 0 means both assemblies compiled.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJ="$ROOT/unity/BorrowedTime"
CACHE="$ROOT/.refcache/unity"
D="$CACHE/opt/unity/Editor/Data"
OUT="$CACHE/out"
LAYER=1115644c7fedd34fe4eb93193925a1d79c8fec05efeba9ee08dca1450ec5f3b8   # the editor layer of ubuntu-6000.3.8f1-base-3 (amd64)

if [ ! -f "$D/Managed/UnityEngine/UnityEngine.CoreModule.dll" ]; then
  echo "Fetching Unity 6000.3.8f1 reference libraries (streams about 5 GB, keeps about 240 MB)..."
  mkdir -p "$CACHE"
  TOKEN=$(curl -sf "https://auth.docker.io/token?service=registry.docker.io&scope=repository:unityci/editor:pull" \
          | python3 -I -c 'import sys,json;print(json.load(sys.stdin)["token"])')
  curl -sfL -H "Authorization: Bearer $TOKEN" "https://registry-1.docker.io/v2/unityci/editor/blobs/sha256:$LAYER" \
    | tee >(sha256sum | cut -d' ' -f1 > "$CACHE/layer.sha256") \
    | tar -xz -C "$CACHE" --wildcards --no-anchored '*/Editor/Data/Managed/*' '*/Editor/Data/NetStandard/*' '*/Editor/Data/UnityReferenceAssemblies/*'
  sleep 1
  if [ "$(cat "$CACHE/layer.sha256")" != "$LAYER" ]; then
    echo "Layer digest mismatch; deleting the download." >&2; rm -rf "$CACHE/opt"; exit 2
  fi
fi

CSC=$(ls -d /usr/lib/dotnet/sdk/*/Roslyn/bincore/csc.dll 2>/dev/null | sort -V | tail -1)
[ -n "$CSC" ] || { echo "Install the compiler first: apt-get install -y dotnet-sdk-8.0" >&2; exit 2; }
mkdir -p "$OUT"

ENGINE_REFS=$(find "$D/Managed/UnityEngine" -maxdepth 1 -name 'UnityEngine.*.dll' -printf '-r:%p\n')
EDITOR_REFS=$(find "$D/Managed/UnityEngine" -maxdepth 1 -name 'UnityEditor.*.dll' -printf '-r:%p\n')
NETSTD_REFS="-r:$D/NetStandard/ref/2.1.0/netstandard.dll $(find "$D/NetStandard/compat/2.1.0/shims/netfx" -name '*.dll' -printf '-r:%p ')"
FX="$D/UnityReferenceAssemblies/unity-4.8-api"
NETFX_REFS="-r:$FX/mscorlib.dll -r:$FX/System.dll -r:$FX/System.Core.dll -r:$FX/Facades/netstandard.dll"
COMMON="-nologo -noconfig -nostdlib+ -langversion:9.0 -target:library -warn:4 -nowarn:0169,0649 -deterministic"
DEFINES="UNITY_6000_3_OR_NEWER;UNITY_2023_1_OR_NEWER;UNITY_5_3_OR_NEWER"

mapfile -t RUNTIME < <(find "$PROJ/Assets" -name '*.cs' -not -path '*/Editor/*' | sort)
mapfile -t EDITOR < <(find "$PROJ/Assets" -path '*/Editor/*' -name '*.cs' | sort)

echo "Runtime (Assembly-CSharp, .NET Standard 2.1): ${#RUNTIME[@]} files"
# shellcheck disable=SC2086
dotnet "$CSC" $COMMON -define:"$DEFINES;UNITY_STANDALONE" -out:"$OUT/Assembly-CSharp.dll" \
  $NETSTD_REFS $ENGINE_REFS "${RUNTIME[@]}"

echo "Editor (Assembly-CSharp-Editor, .NET Framework 4.8 API): ${#EDITOR[@]} files"
# shellcheck disable=SC2086
dotnet "$CSC" $COMMON -define:"$DEFINES;UNITY_EDITOR" -out:"$OUT/Assembly-CSharp-Editor.dll" \
  $NETFX_REFS $ENGINE_REFS $EDITOR_REFS -r:"$OUT/Assembly-CSharp.dll" "${EDITOR[@]}"

echo "OK: Unity scripts compile against Unity 6000.3.8f1."
