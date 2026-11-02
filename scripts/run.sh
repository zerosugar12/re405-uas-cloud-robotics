#!/usr/bin/env bash
set -eo pipefail

cd "$(dirname "$0")/.."

# Clean up any lingering processes from previous sessions
echo "Cleaning up previous sessions..."
pkill -f rosbridge_websocket 2>/dev/null || true
pkill -f "http.server 8000" 2>/dev/null || true
sleep 1

# Source ROS2 workspace if built
if [ -f install/setup.bash ]; then
  COLCON_TRACE=${COLCON_TRACE:-} source install/setup.bash
fi

echo "Starting system..."
echo "  - Gazebo Simulation"
echo "  - ROS2 Bridge"
echo "  - Rosbridge WebSocket (port 9090)"
echo "  - Web Dashboard (port 8000)"
echo ""
echo "Open http://localhost:8000 in your browser."
echo ""

ros2 launch robot_bringup robot_launch.py "$@"
