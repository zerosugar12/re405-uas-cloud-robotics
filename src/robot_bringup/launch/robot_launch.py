import os
import subprocess

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    TimerAction,
    SetEnvironmentVariable,
    ExecuteProcess,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch_ros.actions import Node

def generate_launch_description():

    pkg_desc_name    = 'robot_description'
    pkg_bringup_name = 'robot_bringup'
    robot_name       = 'robot'

    pkg_desc_path    = get_package_share_directory(pkg_desc_name)
    pkg_bringup_path = get_package_share_directory(pkg_bringup_name)

    urdf_dir    = os.path.join(pkg_desc_path, 'urdf')
    field_file  = os.path.join(urdf_dir, 'field.urdf')
    ball_file   = os.path.join(urdf_dir, 'ball.sdf')
    bridge_yaml = os.path.join(pkg_bringup_path, 'config', 'bridge.yaml')
    rviz_config = os.path.join(pkg_desc_path, 'rviz', 'robot_view.rviz')

    xacro_file = os.path.join(urdf_dir, 'robot.urdf')
    robot_description_xml = subprocess.check_output(['xacro', xacro_file]).decode('utf-8')

    # Arguments for conditional launch components
    start_web = LaunchConfiguration('start_web', default='true')
    start_rosbridge = LaunchConfiguration('start_rosbridge', default='true')

    # Set GZ_SIM_RESOURCE_PATH so Gazebo finds the mesh/URDF assets
    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=os.path.join(pkg_desc_path, '..')
    )

    # Start robot_state_publisher with the robot URDF description
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description_xml,
            'use_sim_time': True
        }]
    )

    # Launch the Gazebo ignition simulator
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch', 'gz_sim.launch.py'
            )
        ]),
        launch_arguments={'gz_args': '-r empty.sdf'}.items(),
    )

    # Spawn the field model (lapangan)
    node_spawn_field = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_field',
        arguments=[
            '-name', 'lapangan',
            '-file', field_file,
            '-x', '0.0', '-y', '0.0', '-z', '0.0',
            '-R', '0.0', '-P', '0.0', '-Y', '0.0'
        ],
        output='screen',
    )

    # Spawn the robot model
    node_spawn_robot = TimerAction(
        period=3.0,
        actions=[Node(
            package='ros_gz_sim',
            executable='create',
            name='spawn_robot',
            arguments=[
                '-name', robot_name,
                '-string', robot_description_xml,
                '-x', '-0.250', '-y', '0.1', '-z', '0.0'
            ],
            output='screen',
        )]
    )

    # Spawn the ball model after a 4s delay
    node_spawn_ball = TimerAction(
        period=4.0,
        actions=[Node(
            package='ros_gz_sim',
            executable='create',
            name='spawn_ball',
            arguments=[
                '-name', 'ball',
                '-file', ball_file,
                '-x', '0.5', '-y', '0.0', '-z', '0.5',
            ],
            output='screen',
        )]
    )

    # ROS-Gazebo bridge using parameter file for topic mappings
    node_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        arguments=[
            '--ros-args', '-p',
            f'config_file:={bridge_yaml}'
        ] if os.path.exists(bridge_yaml) else [],
        output='screen'
    )

    # Launch RViz2 for robot visualization
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config] if os.path.exists(rviz_config) else [],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    # rosbridge WebSocket server on port 9090
    rosbridge = Node(
        condition=IfCondition(start_rosbridge),
        package='rosbridge_server',
        executable='rosbridge_websocket',
        name='rosbridge_websocket',
        parameters=[{'port': 9090, 'address': '0.0.0.0'}],
        output='screen'
    )

    # Vision-based ball distance detection node
    node_vision = Node(
        package='robot_bringup',
        executable='vision_distance.py',
        name='vision_distance',
        output='screen'
    )

    # MJPEG video stream server on port 8080
    node_video_server = Node(
        package='web_video_server',
        executable='web_video_server',
        name='web_video_server',
        parameters=[{
            'port': 8080,
            'address': '0.0.0.0',
        }],
        output='screen'
    )

    # Simple Python HTTP server serving the web dashboard on port 8000
    web_dir = os.path.join(pkg_bringup_path, 'web')
    if not os.path.exists(web_dir):
        web_dir = os.path.join(get_package_share_directory(pkg_bringup_name), 'web')
    web_server = ExecuteProcess(
        condition=IfCondition(start_web),
        cmd=['python3', '-m', 'http.server', '8000', '--bind', '0.0.0.0', '--directory', web_dir],
        output='screen'
    )

    # Assemble all launch actions
    return LaunchDescription([
        set_gz_resource_path,
        node_robot_state_publisher,
        gazebo_launch,
        node_spawn_field,
        node_spawn_robot,
        node_spawn_ball,
        node_vision,
        node_bridge,
        rosbridge,
        node_video_server,
        web_server,
        rviz,
    ])