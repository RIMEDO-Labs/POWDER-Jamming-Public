#!/bin/bash

set -ex

COMMIT_HASH=$1
BINDIR="$(dirname "$0")"
ETCDIR=/local/repository/etc

source "$BINDIR/common.sh"

# ============================================================
# CONFIGURATION
# ============================================================

# Pin UHD to an exact version.
# Do NOT use the latest UHD from the Ettus PPA.
UHD_VERSION="4.10.0.0"

UHD_REPO="https://github.com/EttusResearch/uhd.git"
UHD_SRC_DIR="$SRCDIR/uhd"
UHD_BUILD_DIR="$UHD_SRC_DIR/host/build"

# ============================================================
# PREVENT DOUBLE DEPLOYMENT
# ============================================================

if [ -f "$SRCDIR/ocudu-setup-complete" ]; then
    echo "setup already ran; not running again"
    exit 0
fi

echo
echo "============================================================"
echo "OCUDU DEPLOYMENT"
echo "============================================================"
echo "OCUDU commit : $COMMIT_HASH"
echo "UHD version  : $UHD_VERSION"
echo "============================================================"
echo

# ============================================================
# SYSTEM DEPENDENCIES
# ============================================================

echo "Installing system dependencies..."

sudo apt-get update

sudo apt-get install -y \
    cmake \
    make \
    gcc \
    g++ \
    git \
    pkg-config \
    iperf3 \
    libboost-dev \
    libboost-all-dev \
    libfftw3-dev \
    libmbedtls-dev \
    libsctp-dev \
    libyaml-cpp-dev \
    libgtest-dev \
    numactl \
    python3-dev \
    python3-venv \
    python3-numpy \
    python3-setuptools \
    python3-requests \
    python3-mako \
    pybind11-dev \
    libusb-1.0-0-dev \
    libusb-1.0-0 \
    libudev-dev \
    libncurses-dev \
    ppp

# ============================================================
# REMOVE APT/PPA UHD
# ============================================================

echo
echo "============================================================"
echo "Removing distro/PPA UHD packages"
echo "============================================================"
echo

# We build UHD ourselves below.
# Remove any Ubuntu/PPA version which could interfere with it.

sudo apt-get remove -y \
    uhd-host \
    libuhd-dev \
    libuhd4.11.0 \
    libuhd4.10.0 \
    python3-uhd \
    uhd-rfnoc-dev \
    2>/dev/null || true

sudo apt-get autoremove -y || true

# ============================================================
# UHD 4.10.0.0
# ============================================================

echo
echo "============================================================"
echo "Installing UHD ${UHD_VERSION}"
echo "============================================================"
echo

cd "$SRCDIR"

# Remove an old/incomplete source tree if one exists.
rm -rf "$UHD_SRC_DIR"

echo "Cloning UHD ${UHD_VERSION}..."

git clone \
    --branch "v${UHD_VERSION}" \
    --depth 1 \
    "$UHD_REPO" \
    "$UHD_SRC_DIR"

cd "$UHD_SRC_DIR"

echo "UHD commit:"
git rev-parse HEAD

# ============================================================
# BUILD UHD
# ============================================================

echo
echo "============================================================"
echo "Building UHD ${UHD_VERSION}"
echo "============================================================"
echo

mkdir -p "$UHD_BUILD_DIR"

cd "$UHD_BUILD_DIR"

cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DENABLE_PYTHON_API=ON \
    -DENABLE_EXAMPLES=ON \
    ..

make -j "$(nproc)"

# ============================================================
# INSTALL UHD
# ============================================================

echo
echo "============================================================"
echo "Installing UHD ${UHD_VERSION} to /usr/local"
echo "============================================================"
echo

sudo make install

sudo ldconfig

# ============================================================
# VERIFY UHD
# ============================================================

echo
echo "============================================================"
echo "VERIFYING UHD"
echo "============================================================"
echo

# Prefer the newly installed UHD binary.
UHD_CONFIG="/usr/local/bin/uhd_config_info"

if [ ! -x "$UHD_CONFIG" ]; then
    echo "ERROR: UHD installation failed."
    echo "Cannot find $UHD_CONFIG"
    exit 1
fi

"$UHD_CONFIG" --version

INSTALLED_UHD="$("$UHD_CONFIG" --version | awk '{print $2}')"

if [ "$INSTALLED_UHD" != "$UHD_VERSION" ]; then
    echo
    echo "ERROR: Wrong UHD version!"
    echo "Expected: $UHD_VERSION"
    echo "Found:    $INSTALLED_UHD"
    echo
    exit 1
fi

echo
echo "UHD version OK: $INSTALLED_UHD"
echo

# ============================================================
# UHD DEVICE UTILITIES
# ============================================================

echo "Checking UHD installation..."

if [ ! -x "/usr/local/bin/uhd_find_devices" ]; then
    echo "WARNING: /usr/local/bin/uhd_find_devices not found."
fi

if [ ! -x "/usr/local/bin/uhd_usrp_probe" ]; then
    echo "WARNING: /usr/local/bin/uhd_usrp_probe not found."
fi

# ============================================================
# OCUDU
# ============================================================

echo
echo "============================================================"
echo "BUILDING OCUDU"
echo "============================================================"
echo

cd "$SRCDIR"

git clone "$OCUDU_REPO"

cd ocudu

git checkout "$COMMIT_HASH"

echo
echo "OCUDU commit:"
git rev-parse HEAD
echo

mkdir build

cd build

# Make sure CMake can find the UHD installation in /usr/local.
cmake \
    -DCMAKE_CXX_FLAGS="${CMAKE_CXX_FLAGS} -Wno-error=switch" \
    -DCMAKE_PREFIX_PATH=/usr/local \
    ..

make -j "$(nproc)"

# ============================================================
# VERIFY OCUDU / UHD LINKING
# ============================================================

echo
echo "============================================================"
echo "VERIFYING OCUDU / UHD LINKING"
echo "============================================================"
echo

GNB_BINARY="$SRCDIR/ocudu/build/apps/gnb/gnb"

if [ ! -f "$GNB_BINARY" ]; then
    echo "ERROR: gNB binary was not built:"
    echo "$GNB_BINARY"
    exit 1
fi

echo "gNB binary:"
echo "$GNB_BINARY"

echo
echo "UHD libraries linked by gNB:"
ldd "$GNB_BINARY" | grep -i uhd || true

echo
echo "UHD version:"
/usr/local/bin/uhd_config_info --version

# ============================================================
# CONFIGURATION
# ============================================================

echo
echo "============================================================"
echo "CONFIGURING OCUDU"
echo "============================================================"
echo

cd "$SRCDIR"

mkdir -p "$SRCDIR/etc/ocudu"

cp -r "$ETCDIR/ocudu/"* "$SRCDIR/etc/ocudu/"

LANIF="$(ip r | awk '/192\.168\.1\.0/{print $3}')"

if [ ! -z "$LANIF" ]; then

    LANIP="$(ip r | awk '/192\.168\.1\.0/{print $NF}')"

    echo "LAN IFACE is $LANIF IP is $LANIP.. updating nodeb config"

    find "$SRCDIR/etc/ocudu/" \
        -type f \
        -exec sed -i "s/LANIP/$LANIP/" {} \;

    IPLAST="$(echo "$LANIP" | awk -F. '{print $NF}')"

    find "$SRCDIR/etc/ocudu/" \
        -type f \
        -exec sed -i "s/GNBID/$IPLAST/" {} \;

else

    echo "No LAN IFACE.. not updating nodeb config"

fi

echo "configuring nodeb... done."

# ============================================================
# FINAL CHECKS
# ============================================================

echo
echo "============================================================"
echo "FINAL DEPLOYMENT CHECK"
echo "============================================================"
echo

echo "UHD:"
/usr/local/bin/uhd_config_info --version

echo
echo "OCUDU:"
cd "$SRCDIR/ocudu"
git rev-parse HEAD

echo
echo "gNB UHD linkage:"
ldd "$GNB_BINARY" | grep -i uhd || true

echo
echo "============================================================"
echo "DEPLOYMENT COMPLETE"
echo "============================================================"
echo
echo "UHD       : $UHD_VERSION"
echo "OCUDU     : $COMMIT_HASH"
echo "gNB       : $GNB_BINARY"
echo

# ============================================================
# MARK SETUP AS COMPLETE
# ============================================================

touch "$SRCDIR/ocudu-setup-complete"