#!/usr/bin/env bash
set -eo pipefail

cd "$(dirname "$0")/.."

echo "Cleaning up previous sessions..."
pkill -f rosbridge_websocket 2>/dev/null || true
pkill -f "http.server 8000" 2>/dev/null || true
sleep 1

if [ -f install/setup.bash ]; then
  COLCON_TRACE=${COLCON_TRACE:-} source install/setup.bash
fi

echo "Starting vps-robot-telemetry in REMOTE mode..."
echo "  - Gazebo Simulation"
echo "  - ROS2 Bridge (Gazebo <-> ROS2)"
echo "  - rosbridge: RUNNING ON PC ROBOT (port 9090, bind 0.0.0.0)"
echo "  - VPS nginx proxies WS to PC Robot via Tailscale"
echo "  - Web Dashboard: http://xxx.xxx.xxx.xxx"
echo ""

ros2 launch robot_bringup robot_launch.py start_web:=false "$@"
