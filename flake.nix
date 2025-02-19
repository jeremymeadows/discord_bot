{
  description = "";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
  let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};

    python = pkgs.python312;

    dependencies = with pkgs; [
      (python.withPackages(p: with p; [
        discordpy
        python-dotenv
        pytz
      ]))
    ];
    devtools = with pkgs; [
      sqlite
    ];
  in
  {
    # `nix develop`
    devShells.${system}.default = pkgs.mkShell {
      packages = dependencies ++ devtools;
      shellHook = ''
        echo 'Environment created, `nix run` to start bot.'
      '';
    };

    # `nix run`
    # apps.${system}.default = pkgs.writeShellScriptBin "main" ''
    #   python bot.py
    # '';

    # `nix build`
    build.${system}.default = pkgs.dockerTools.buildImage {
      name = "old-tom";
      copyToRoot = pkgs.buildEnv {
        paths = dependencies;
      };
      config = {
        Cmd = [
          "${python}/bin/python" "bot.py"
        ];
      };
    };
  };
}