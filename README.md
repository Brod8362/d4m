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
- Search and Install mods from [GameBanana](https://gamebanana.com/games/16522)
- Update installed mods easily

Installation
============

Requirements: `python >= 3.8`, `libarchive` (optional)

### From PyPi

`python -m pip install d4m` (currently not available just yet)

IMPORTANT: If your system supports `libarchive` (aka, Linux, or Windows users who went out of their way to install it)

**Make sure to do `python -m pip install libarchive` too!**

### For Windows (Bundled)

Download the latest d4m executable from the [releases page.](https://github.com/Brod8362/d4m/releases)

### From Source

```
git clone https://github.com/Brod8362/d4m
cd d4m
python -m pip install build
python -m build
python -m pip install dist/*.whl
```

### From Source (Development)
```
git clone https://github.com/Brod8362/d4m
cd d4m
python -m pip install build
python -m pip install -e .
```

Running
=======

Linux/Windows (via pip)
-----

`python -m d4m` (TUI)

`python -m d4m -g` (GUI)

You can place an alias in your shell config, e.g `~/.bashrc` or `~/.zshrc`

> `alias d4m=python -m d4m`

Demo (TUI)
-------
![d4m tui](https://github.com/Brod8362/d4m/blob/main/resources/d4m.gif)

Demo (GUI)
-----------
![d4m gui](https://github.com/Brod8362/d4m/blob/main/resources/gui.png)


FAQ
===

- Why is DivaModLoader installation not supported on my platform?

Currently, automatic DivaModLoader installation/updating depends on `libarchive`. Most Windows users likely don't have this installed, and I don't want to make it a hard dependency of the application.

`libarchive` is needed because the packager of DivaModLoader creates archives using BCJ2, which is not supported by `py7zr`.

If you manually install `libarchive` and the corresponding pip package (`libarchive`), you should then be able to auto install/update DML.

Configuration
=============
You can override some parameters of d4m via environment variables.

| Environment Variable | Purpose                    | Default                   |
| -------------------- | -------------------------- | ------------------------- |
| `D4M_INSTALL_DIR`    | MegaMix+ install directory | Auto-determined via steam |