{
  description = "";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
  let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};

    requirements = with pkgs; [
      (python3.withPackages(p: with p; [
        discordpy
        python-dotenv
        pytz
      ]))
    ];
  in
  {
    # `nix develop`
    devShells.${system}.default = pkgs.mkShell {
      packages = requirements;
      shellHook = ''
        python bot.py
      '';
    };

    # `nix build`
    build.${system}.default = pkgs.dockerTools.buildImage {
      name = "old-tom";
      copyToRoot = pkgs.buildEnv {
        paths = requirements;
      };
      config = {
        Cmd = [
          "${pkgs.python3}/bin/python" "bot.py"
        ];
      };
    };
  };
}