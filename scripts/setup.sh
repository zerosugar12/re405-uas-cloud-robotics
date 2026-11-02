#!/usr/bin/env bash
set -euo pipefail

ROS_DISTRO="${ROS_DISTRO:-jazzy}"

echo "[1/3] Installing system dependencies..."
sudo apt update
sudo apt install -y \
  python3-colcon-common-extensions \
  python3-opencv \
  python3-requests

echo "[2/3] Installing ROS2 packages..."
sudo apt install -y \
  ros-${ROS_DISTRO}-rosbridge-server \
  ros-${ROS_DISTRO}-robot-state-publisher \
  ros-${ROS_DISTRO}-rviz2 \
  ros-${ROS_DISTRO}-ros-gz-bridge \
  ros-${ROS_DISTRO}-ros-gz-sim \
  ros-${ROS_DISTRO}-web-video-server \
  ros-${ROS_DISTRO}-cv-bridge

echo "[3/3] Building workspace..."
cd "$(dirname "$0")/.."
colcon build --symlink-install --paths src/robot_bringup src/robot_description

echo ""
echo "Done!"
echo ""
echo "Usage:"
echo "  source install/setup.bash"
echo "  ./scripts/run.sh"
echo "  # Open http://localhost:8000 in browser"
