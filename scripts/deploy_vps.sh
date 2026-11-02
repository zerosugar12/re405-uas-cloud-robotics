#!/usr/bin/env bash
set -eo pipefail

VPS_USER="root"
VPS_IP="xxx.xxx.xxx.xxx"
VPS_TAILSCALE_IP="xxx.xxx.xxx.xxx"
PC_TAILSCALE_IP="${PC_TAILSCALE_IP:-xxx.xxx.xxx.xxx}"
WEB_DIR="$(dirname "$0")/../src/robot_bringup/web"

echo "========================================="
echo " Deploy Dashboard to VPS"
echo " VPS: ${VPS_USER}@${VPS_IP}"
echo "========================================="
echo ""

# 1. Setup VPS dependencies
echo "[1/5] Installing VPS dependencies (ROS2 + nginx)..."
ssh ${VPS_USER}@${VPS_IP} << 'REMOTE_SETUP'
  apt update
  apt install -y curl gnupg lsb-release software-properties-common nginx

  # ROS2 Jazzy repository
  add-apt-repository universe
  curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
    http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | \
    tee /etc/apt/sources.list.d/ros2.list > /dev/null

  apt update
  apt install -y ros-jazzy-rosbridge-server ros-jazzy-rosbridge-suite

  # Firewall
  ufw allow ssh
  ufw allow 80/tcp
  ufw --force enable

  # Web directory
  mkdir -p /var/www/rosbridge
REMOTE_SETUP
echo "  Done!"
echo ""

# 2. Create ROS2 workspace on VPS
echo "[2/5] Creating ROS2 workspace on VPS..."
ssh ${VPS_USER}@${VPS_IP} << 'REMOTE_WS'
  mkdir -p ~/ros2_ws/src/vps_rosbridge/launch
  mkdir -p ~/ros2_ws/src/vps_rosbridge/config

  # package.xml
  cat > ~/ros2_ws/src/vps_rosbridge/package.xml << 'PKGXML'
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>vps_rosbridge</name>
  <version>0.0.0</version>
  <description>VPS rosbridge relay for remote robot monitoring</description>
  <maintainer email="user@todo.todo">user</maintainer>
  <license>Apache License 2.0</license>
  <buildtool_depend>ament_cmake</buildtool_depend>
  <exec_depend>rosbridge_server</exec_depend>
  <exec_depend>rosbridge_suite</exec_depend>
  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
PKGXML

  # CMakeLists.txt
  cat > ~/ros2_ws/src/vps_rosbridge/CMakeLists.txt << 'CMAKE'
cmake_minimum_required(VERSION 3.8)
project(vps_rosbridge)
find_package(ament_cmake REQUIRED)
install(DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)
ament_package()
CMAKE

  # Launch file
  cat > ~/ros2_ws/src/vps_rosbridge/launch/rosbridge_launch.py << 'LAUNCH'
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rosbridge_server',
            executable='rosbridge_websocket',
            name='rosbridge_websocket',
            output='screen',
            parameters=[{
                'port': 9090,
                'address': '0.0.0.0',
                'retry_startup_delay': 2.0,
                'max_retry_attempts': 10,
                'authenticate': False
            }]
        )
    ])
LAUNCH

  touch ~/ros2_ws/src/vps_rosbridge/config/.gitkeep
REMOTE_WS
echo "  Done!"
echo ""

# 3. Build ROS2 workspace on VPS
echo "[3/5] Building ROS2 workspace on VPS..."
ssh ${VPS_USER}@${VPS_IP} << 'REMOTE_BUILD'
  source /opt/ros/jazzy/setup.bash
  cd ~/ros2_ws
  colcon build
  echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
REMOTE_BUILD
echo "  Done!"
echo ""

# 4. Deploy web dashboard to VPS
echo "[4/5] Deploying web dashboard..."
rsync -av --delete ${WEB_DIR}/ ${VPS_USER}@${VPS_IP}:/var/www/rosbridge/
echo "  Done!"
echo ""

# 5. Setup nginx on VPS
echo "[5/5] Configuring nginx..."

# Generate nginx config locally so variable substitution works correctly
TMP_NGINX=$(mktemp)
cat > "${TMP_NGINX}" <<- NGINX_EOF
server {
    listen 80;
    server_name _;

    root /var/www/rosbridge;
    index index.html;

    location / {
        try_files \$uri \$uri/ =404;
    }

    location /rosbridge {
        proxy_pass http://${PC_TAILSCALE_IP}:9090/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /camera/ {
        proxy_pass http://${PC_TAILSCALE_IP}:8080/;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX_EOF

scp "${TMP_NGINX}" ${VPS_USER}@${VPS_IP}:/etc/nginx/sites-available/rosbridge
rm -f "${TMP_NGINX}"

ssh ${VPS_USER}@${VPS_IP} << 'NGINX_RELOAD'
  ln -sf /etc/nginx/sites-available/rosbridge /etc/nginx/sites-enabled/
  rm -f /etc/nginx/sites-enabled/default
  nginx -t && systemctl restart nginx
NGINX_RELOAD
echo "  Done!"
echo ""

echo "========================================="
echo " Deployment selesai!"
echo "========================================="
echo ""
echo "Cara menjalankan:"
echo ""
echo "  1. Di PC Robot (jalankan ini):"
echo "     ./scripts/connect_vps.sh"
echo ""
echo "     Catatan: pastikan PC_TAILSCALE_IP di deploy_vps.sh"
echo "     sesuai dengan IP Tailscale PC Robot."
echo ""
echo "  2. Buka browser di mana saja:"
echo "     http://${VPS_IP}"
echo ""
echo "  Dashboard akan connect ke rosbridge di PC Robot"
echo "  melalui: VPS nginx → proxy_pass → Tailscale tunnel → PC"
echo ""
