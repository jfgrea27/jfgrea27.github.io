{
  description = "A flake to manage my personal blog";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config = {
            allowUnsupportedSystem = true;
            allowUnfree = true;
          };
        };
        gccLib = pkgs.stdenv.cc.cc.lib;
      in
      {
        devShell = pkgs.mkShell {
          packages = [
            pkgs.just
            pkgs.git

            pkgs.hugo
          ];
          shellHook = ''
            export LD_LIBRARY_PATH=${gccLib}/lib:${pkgs.zlib}/lib
          '';
        };
      }
    );
}
