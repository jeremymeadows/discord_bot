{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [ 
    (python3.withPackages(p: with p; [
      discordpy
      python-dotenv
      pytz
    ]))
  ];
  shellHook = ''
    python bot.py
  '';
}