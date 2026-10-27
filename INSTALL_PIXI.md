# Installing Geant4 via Pixi

> ⚠️ **Heads up:** Pixi has known compatibility issues on macOS — especially the Qt `cocoa` platform plugin. If you run into that error, give up and go back to [README.md](./README.md) to install from source instead. You've been warned.

## Install Pixi

```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

## Initialize Project

```bash
cd ~/Desktop
mkdir geant4_project
cd geant4_project
pwd

pixi init
pixi --version
```

> ⚠️ Make sure conda is not active (no `(base)` in front of your prompt):
> ```bash
> conda config --set auto_activate_base false
> ```

## Install Geant4

Make sure you are at `~/Desktop/geant4_project`, then:

```bash
pixi add geant4

pixi shell
geant4-config --version
```

If you don't have cmake:

```bash
pixi add cmake
```

## Copy ExampleB1

```bash
cp -r .pixi/envs/default/share/Geant4/examples/basic/B1 B1_copy
cd B1_copy
```

Create a separate build folder for compilation. All generated files will be placed here. If something goes wrong, simply delete this directory and rebuild.

```bash
mkdir build
cd build
```

If you need to rebuild from scratch:

```bash
cd ..
rm -rf build
mkdir build
cd build
```

## Configure Project

Use pixi's CMake to avoid conflicts with system/Homebrew CMake. Explicitly set the prefix path so dependencies (zlib, etc.) are resolved from the pixi environment.

```bash
pixi run cmake .. \
  -DCMAKE_PREFIX_PATH=$CONDA_PREFIX \
  -DZLIB_ROOT=$CONDA_PREFIX
```

## Build

```bash
pixi run cmake --build .
```

You should see `[100%] Built target exampleB1`, then:

```bash
./exampleB1
```

## Troubleshooting

**Could not find the Qt platform plugin "cocoa"** — It's really complicated to fix. Just install from source instead. See [README.md](./README.md).

**Show hidden files on Mac** — `Cmd + Shift + .`
