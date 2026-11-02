## Architecture & Workflow

```text
                   +----------------------+
                   |   Gazebo Harmonic    |
                   |----------------------|
                   | Robot                |
                   | Ball                 |
                   | Camera               |
                   +----------+-----------+
                              |
                              | Gazebo Topics
                              v
                   +----------------------+
                   |    ros_gz_bridge     |
                   +----+------------+----+
                        |            |
        ROS Topics      |            | Camera Image
                        |            v
                        |   +----------------------+
                        |   | vision_distance      |
                        |   |----------------------|
                        |   | OpenCV Detector      |
                        |   | /ball_distance       |
                        |   | /ball_world          |
                        |   | /annotated_img       |
                        |   +----------+-----------+
                        |              |
                        |              v
                        |   +----------------------+
                        |   | web_video_server     |
                        |   | HTTP :8080           |
                        |   +----------+-----------+
                        |              |
                        v              |
               +----------------------+
               | rosbridge_server     |
               | WebSocket :9090      |
               +----------+-----------+
                          |
                          | WebSocket
                          v
                 +----------------------+
                 |      Tailscale       |
                 |  WireGuard Tunnel    |
                 +----------+-----------+
                            |
          +-----------------+-----------------+
          |                                   |
          | WebSocket (:9090)                 | MJPEG (:8080)
          v                                   v
                 +----------------------+
                 |     VPS + Nginx      |
                 |----------------------|
                 | /                    |
                 | /rosbridge           |
                 | /camera              |
                 +----------+-----------+
                            |
                            | HTTP
                            v
                 +----------------------+
                 |    Web Dashboard     |
                 |----------------------|
                 | RosConnection.js     |
                 | RobotControl.js      |
                 | OdomTracker.js       |
                 | BallTrackers.js      |
                 | CanvasRenderer.js    |
                 | StatusPanel.js       |
                 | LatencyPinger.js     |
                 +----------------------+
```

1. **Simulation**: Gazebo Harmonic runs a differential-drive robot, a ball, and an overhead camera simulation.
2. **Bridge**: `ros_gz_bridge` connects Gazebo topics to ROS 2 topics (`/cmd_vel`, `/odom`, `/tf`, `/camera`, `/clock`).
3. **Vision**: `vision_distance` detects the ball with OpenCV and publishes `/ball_distance`, `/ball_world`, and `/annotated_img`.
4. **Streaming**: `web_video_server` serves an MJPEG video feed on port `8080`; `rosbridge_server` opens a ROS 2 WebSocket on port `9090`.
5. **Remote**: Tailscale creates an encrypted tunnel (WireGuard) between the Robot PC and the VPS.
6. **Proxy**: Nginx on the VPS (port 80) routes `/` → static dashboard, `/rosbridge` → `ws://robot:9090`, `/camera/` → `http://robot:8080`.
7. **Dashboard**: The browser displays the camera feed, 2D robot, odom status, ball distance, latency, and `/cmd_vel` control via rosbridge.

## Quick Start

### 1. Deploy to VPS (one-time setup)
```bash
./scripts/deploy_vps.sh
```

### 2. Run on PC Robot

```bash
./scripts/setup.sh
source install/setup.bash
./scripts/connect_vps.sh
```

### 3. Open browser from anywhere

http://xxx.xxx.xxx.xxx
