d4m
===

### Project Diva MegaMix+ mod manager

Supported Systems
-----------------
Currently, only Linux is supported.

However, Windows support is WIP.

A GUI is also WIP.

Features
--------

- Automatically determine game install directory
- Install and update DivaModLoader
- Easily enable/disable mods
- Search and Install mods from [GameBanana](https://gamebanana.com/games/16522)
- Update installed mods easily

Installation
------------

### From PyPi

`python -m pip install d4m` (currently not available just yet)

### From Source

```
git clone https://github.com/Brod8362/d4m
cd d4m
python -m pip install build
python -m build
python -m pip install dist/*.whl
```

### For Development
```
git clone https://github.com/Brod8362/d4m
cd d4m
python -m pip install build
python -m pip install -e .
```

Running
-------

`python -m d4m`

You can place an alias in your shell config, e.g `~/.bashrc` or `~/.zshrc`

> `alias d4m=python -m d4m`

Example
-------
![d4m demo](https://github.com/Brod8362/d4m/blob/main/d4m.gif)

Configuration
-------------
You can override some parameters of d4m via environment variables.

| Environment Variable | Purpose                    | Default                   |
| -------------------- | -------------------------- | ------------------------- |
| `D4M_INSTALL_DIR`    | MegaMix+ install directory | Auto-determined via steam |