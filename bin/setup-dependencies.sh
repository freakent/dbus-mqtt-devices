#!/bin/sh
BASE=$(dirname $(dirname $(realpath "$0")))
PREFIX="dbus-mqtt-devices:"

check_online() {
    local url="https://vrm.victronenergy.com"
    local attempts=0
    while [ $attempts -lt 10 ]; do
        wget --spider --quiet --tries=1 --timeout=5 "$url"  # Check URL without downloading content
        if [ $? -eq 0 ]; then  # If wget succeeds (exit status 0)
            break  # Exit loop
        else
            attempts=$((attempts + 1))
            echo "`date` $PREFIX GX Device does not appear to be online, retrying in 1 minute..."
            sleep 60  # Wait for 1 minute before retrying
        fi
    done
    if [ $attempts -eq 10 ]; then
        echo "`date` $PREFIX GX Device does not appear to be online, exiting..."
        exit 1
    fi
}

ensure_opkg_installed() {
    local pkg_name=$1
    if [ "$opkg_updated" != "yes" ]; then
        check_online
        venus_version=$(head -n 1 "/opt/victronenergy/version")

        # Check if the version number contains a '~' indicating it's a beta version
        if [[ "$venus_version" == *~* ]]; then
            echo "$PREFIX '$venus_version' of VenusOS is a beta version so using candidate opkg feed"
            /opt/victronenergy/swupdate-scripts/set-feed.sh candidate
        fi

        echo "$PREFIX Updating opkg package list"
        opkg update
        opkg_updated="yes"
    fi

    echo "$PREFIX Checking to see if library $pkg_name is installed"
    if opkg list-installed | grep -q "^$pkg_name"; then
        echo "$PREFIX Library $pkg_ame is already installed"
    else
        opkg install $pkg_name
        if [ $? -ne 0 ]; then
            echo "$PREFIX Failed to install $pkg_name"
            exit 1
        fi
        echo "$PREFIX Library $pkg_name installed successfully"
    fi

}

readonly=$(awk '$2 == "/" { print $4 }' /proc/mounts | grep -q 'ro' && echo "yes" || echo "no")
if [ "$readonly" = "yes" ]; then
    echo "$PREFIX Temporarily enable writing to root partition"
    mount -o remount,rw /
    remount="yes"
fi

ensure_opkg_installed python3-tomllib

echo "$PREFIX Checking to see if Python's Pip is installed"
python -m pip --version
piperr=$?
if [ "$piperr" -ne 0 ]; then
    ensure_opkg_installed python3-pip
fi

# ensure_opkg_installed python3-misc

echo "$PREFIX Pip install module dependencies"
check_online
python -m pip install dataclasses # need to force dataclasses to be installed before installing rest of requirements
python -m pip install -r $BASE/requirements.txt

if [ "$remount" = "yes" ]; then
    echo "$PREFIX Setting root partition back to readonly"
    mount -o remount,ro /
fi
