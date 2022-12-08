d4m
===

![d4m banner](https://github.com/Brod8362/d4m/blob/main/resources/EXPORT_github.png)

### A cross-platform Project Diva MegaMix+ mod manager

Features
========

- Cross-platform
- Simple usage, everything you need and nothing you don't (no bloat!)
- Automatically determine game install directory
- Install and update DivaModLoader
- Easily enable/disable mods
- Search and Install mods from [GameBanana](https://gamebanana.com/games/16522) and [DivaModArchive](https://divamodarchive.xyz/)
- Install mods from a local archive (.7z,.rar,.zip, etc)
- Update installed mods easily
- Migrate metadata from DivaModManager
- Automatic self-update checking
- TUI or GUI: your choice! (TUI is Linux only)

Installation
============

Requirements: `python >= 3.9`, `libarchive`

### Linux

[d4m is now available in the AUR!](https://aur.archlinux.org/packages/d4m-git)

Before installing `d4m`, you first need to install libarchive.

For Ubuntu, this can be installed with

`sudo apt install libarchive-dev`

After installing libarchive, install `d4m` via pip:

`python -m pip install d4m`

### For Windows (Bundled)

Download the latest d4m installer from the [releases page.](https://github.com/Brod8362/d4m/releases)

### From Source

*Note: libarchive must be installed 

```sh
git clone https://github.com/Brod8362/d4m
cd d4m
python -m pip install build
python -m build
python -m pip install dist/*.whl
```

### From Source (Development)

*Note: libarchive must be installed

```sh
git clone https://github.com/Brod8362/d4m
cd d4m
git checkout unstable
python -m pip install build
python -m pip install -e .
```

### Flatpak (pre-built binary)

Download the latest .flatpak from the [releases](https://github.com/Brod8362/d4m/releases) section and install it via `flatpak install`. (e.g, `flatpak install d4m-VERSION.flatpak`)

### Flatpak (building)

```sh
git clone https://github.com/Brod8362/d4m
cd d4m/flatpak
./build.sh --repo=REPO_PATH --force-clean
flatpak build-bundle REPO_PATH d4m-VERSION.flatpak pw.byakuren.d4m
flatpak install d4m.flatpak
rm d4m.flatpak # optional
```

Running
=======

Linux (via pip)
-----

`d4m` (TUI)

`d4m-gui` (GUI)

Linux (via AUR or Flatpak)
--------------------------

`d4m` should have been added as a desktop entry. This will run the GUI.

For AUR, you can also use the `d4m` or `d4m-gui` commands.

If you're having issues with the Flatpak or AUR distributions, [please open an issue.](https://github.com/Brod8362/d4m/issues/new/choose)

Demo (TUI)
-------
![d4m tui](https://github.com/Brod8362/d4m/blob/main/resources/d4m.gif)

Demo (GUI)
-----------
![d4m gui](https://github.com/Brod8362/d4m/blob/main/resources/gui.png)


FAQ
===

- Why is DivaModLoader installation not supported on my platform?

> As of d4m 0.3.1, `libarchive` is *required* for installations on all platforms.

> As of d4m 0.3.0, `libarchive` should be bundled with all Windows installations.

Currently, automatic DivaModLoader installation/updating depends on `libarchive`. Most Windows users likely don't have this installed, and I don't want to make it a hard dependency of the application.

`libarchive` is needed because the packager of DivaModLoader creates archives using BCJ2, which is not supported by `py7zr`.

If you manually install `libarchive` and the corresponding pip package (`libarchive`), you should then be able to auto install/update DML.

Configuration
=============
You can override some parameters of d4m via environment variables.

| Environment Variable | Purpose                    | Default                   |
| -------------------- | -------------------------- | ------------------------- |
| `D4M_INSTALL_DIR`    | MegaMix+ install directory | Auto-determined via steam |
