{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = [
    pkgs.uv
    pkgs.python311
    pkgs.pkg-config
    pkgs.libpq
    pkgs.stdenv.cc.cc.lib
  ];

  shellHook = ''
    export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib pkgs.libpq ]}:$LD_LIBRARY_PATH"

    uv sync --extra dev

    echo "Nix shell ready."
    echo "Run: uv run uvicorn app.main:app --reload"
  '';
}
