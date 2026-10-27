# Geant4 Tutorial

A step-by-step guide for installing and running Geant4 simulations on macOS.

> ⚠️ **Why not pixi?**
> Pixi has known compatibility issues on macOS (e.g. the Qt `cocoa` platform plugin often fails to load). Installing from source is more reliable and is the recommended approach here. If you still want to try pixi, see [INSTALL_PIXI.md](./INSTALL_PIXI.md).

## Installation from the source

### Prerequisites

Use [Homebrew](https://brew.sh) to install all required dependencies.

```bash
brew install zlib cmake xerces-c qt xquartz root
# mac's built-in C++ compiler will be used
```

> ⚠️ **Log out and log back in your macOS account** after installing dependencies.

### Download & Extract Geant4

Make sure you're downloading the latest version — it's v11.4.1 as of March 31, 2026.

```bash
curl -LO https://geant4-data.web.cern.ch/releases/geant4-v11.4.1.tar.gz
tar -xzf geant4-v11.4.1.tar.gz

# Rename for convenience
mv geant4-v11.4.1 geant4
```

After renaming, verify the contents look right:

```bash
cd geant4
ls
# You should see:
# CMakeLists.txt
# source/
# examples/
```

### Build & Install

```bash
mkdir build
cd build

cmake .. \
  -DCMAKE_INSTALL_PREFIX=~/geant4 \
  -DGEANT4_USE_OPENGL_X11=ON \
  -DGEANT4_USE_QT=ON \
  -DGEANT4_USE_RAYTRACER_X11=ON \
  -DGEANT4_INSTALL_DATA=ON \
  -DGEANT4_USE_SYSTEM_ZLIB=ON \
  -DZLIB_ROOT=$(brew --prefix zlib) \
  -DXERCESC_ROOT_DIR=$(brew --prefix xerces-c)

make -j$(sysctl -n hw.ncpu)  # Use all CPU cores
make install
```

> ✅ You don't need to install Geant4 ever again after this.

### Environment Setup

```bash
echo "source ~/geant4-install/bin/geant4.sh" >> ~/.zshrc
source ~/.zshrc
```

## Usage

### Build Your Project

Navigate to your project, wipe any old build, and start fresh:

```bash
# Go to where your copy is
cd Desktop/geant4_project/B1_copy

# Delete all the stuff in the build directory and rebuild
rm -rf build
mkdir build
cd build

# Configure project
# (Add -DGeant4_DIR and -DZLIB_ROOT if your system can't find them)
cmake .. \
  -DGeant4_DIR=~/geant4/lib/cmake/Geant4 \
  -DZLIB_ROOT=$(brew --prefix zlib)

# Build
make
./exampleB1
```

### Run a Simulation

In the Geant4 interactive terminal:

```
/control/execute run1.mac
```

Edit `run1.mac` to configure your beam. Example for a proton beam shooting in the +x direction:

```
# Macro file for example B1
#
# Can be run in batch, without graphic
# or interactively: Idle> /control/execute run1.mac
#
# Change the default number of workers (in multi-threading mode)
#/run/numberOfThreads 4
#
# Initialize kernel
/run/initialize
#
/control/verbose 2
/run/verbose 2
/event/verbose 0
/tracking/verbose 1
#
# gamma 6 MeV to the direction (0.,0.,1.)
#
/gun/particle proton
/gun/momentumAmp 242 MeV
/gun/position -51 0 0 cm
/gun/direction 1 0 0
/run/beamOn 10000
# This version is for proton shooting to dir +x.
```

Want to shoot a muon instead? Try editing it like this:

```
/gun/particle mu-
/gun/momentumAmp 50 MeV
/gun/position 0 0 51 cm
/gun/direction 0 0 1
/run/beamOn 1
```

### View Histograms

```bash
root
# In ROOT: Exit -> Show(entry_no)
```

## Tips for VS Code

| Shortcut | Action |
|---|---|
| `Opt + Shift + ↓` | Duplicate line |
| `Cmd + /` | Toggle comment |
| `Opt + ↑/↓` | Move line up/down |
| `Opt + Shift + Cmd + ↑/↓` | Duplicate cursor |

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
