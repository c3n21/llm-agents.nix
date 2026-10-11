{
  lib,
  flake,
  stdenv,
  buildVscode,
  fetchurl,
  writeShellScript,
  coreutils,
  commandLineArgs ? "",
  useVSCodeRipgrep ? stdenv.hostPlatform.isDarwin,
}:

let
  inherit (stdenv) hostPlatform;
  versionData = builtins.fromJSON (builtins.readFile ./hashes.json);
  inherit (versionData) version vscodeVersion;
  source =
    versionData.sources.${hostPlatform.system}
      or (throw "antigravity-ide: unsupported system ${hostPlatform.system}");
in
(buildVscode {
  inherit
    commandLineArgs
    useVSCodeRipgrep
    version
    vscodeVersion
    ;
  pname = "antigravity-ide";

  executableName = "antigravity-ide";
  longName = "Antigravity IDE";
  shortName = "Antigravity IDE";
  libraryName = "antigravity-ide";
  iconName = "antigravity-ide";

  src = fetchurl {
    url = source.url;
    hash = source.sha256;
  };

  sourceRoot = if hostPlatform.isDarwin then "Antigravity IDE.app" else "Antigravity IDE";

  tests = { };
  updateScript = ./update.py;

  # When running inside an FHS environment, try linking Google Chrome or Chromium
  # to the hardcoded Playwright search path: /opt/google/chrome/chrome
  customizeFHSEnv =
    args:
    args
    // {
      extraBwrapArgs = (args.extraBwrapArgs or [ ]) ++ [ "--tmpfs /opt/google/chrome" ];
      extraBuildCommands = (args.extraBuildCommands or "") + ''
        mkdir -p "$out/opt/google/chrome"
      '';
      runScript = writeShellScript "antigravity-ide-wrapper" ''
        for candidate in google-chrome-stable google-chrome chromium-browser chromium; do
          if target=$(command -v "$candidate"); then
            ${coreutils}/bin/ln -sf "$target" /opt/google/chrome/chrome
            break
          fi
        done
        exec ${args.runScript} "$@"
      '';
    };

  meta = with lib; {
    description = "Agentic development platform, evolving the IDE into the agent-first era";
    homepage = "https://antigravity.google/product/antigravity-ide";
    downloadPage = "https://antigravity.google/download#antigravity-ide";
    changelog = "https://antigravity.google/changelog";
    license = flake.lib.licenses.unfree;
    sourceProvenance = with sourceTypes; [ binaryNativeCode ];
    maintainers = with maintainers; [
      xiaoxiangmoe
      Zaczero
      schembriaiden
    ];
    mainProgram = "antigravity-ide";
    platforms = [
      "x86_64-linux"
      "aarch64-linux"
      "aarch64-darwin"
    ];
  };
}).overrideAttrs
  (old: {
    passthru = (old.passthru or { }) // {
      category = "AI Coding Agents";
    };
  })
