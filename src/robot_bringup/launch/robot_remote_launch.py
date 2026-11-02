import os
import subprocess

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    TimerAction,
    SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():

    pkg_desc_name    = 'robot_description'
    robot_name       = 'robot'

    pkg_desc_path    = get_package_share_directory(pkg_desc_name)

    urdf_dir    = os.path.join(pkg_desc_path, 'urdf')
    field_file  = os.path.join(urdf_dir, 'field.urdf')
    ball_file   = os.path.join(urdf_dir, 'ball.sdf')

    xacro_file = os.path.join(urdf_dir, 'robot.urdf')
    robot_description_xml = subprocess.check_output(['xacro', xacro_file]).decode('utf-8')

    # Set GZ_SIM_RESOURCE_PATH so Gazebo finds assets
    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=os.path.join(pkg_desc_path, '..')
    )

    # Start robot_state_publisher with the URDF description
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description_xml,
            'use_sim_time': True
        }]
    )

    # Launch Gazebo simulation
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch', 'gz_sim.launch.py'
            )
        ]),
        launch_arguments={'gz_args': '-r empty.sdf'}.items(),
    )

    # Spawn field, robot and ball 
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

    # ROS-Gazebo bridge using parameter file
    pkg_bringup_name = 'robot_bringup'
    pkg_bringup_path = get_package_share_directory(pkg_bringup_name)
    bridge_yaml = os.path.join(pkg_bringup_path, 'config', 'bridge.yaml')

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

    # Relay odometry data to VPS via HTTP POST
    ros2_to_http = Node(
        package='robot_bringup',
        executable='ros2_to_http.py',
        name='ros2_to_http',
        output='screen'
    )

    return LaunchDescription([
        set_gz_resource_path,
        node_robot_state_publisher,
        gazebo_launch,
        node_spawn_field,
        node_spawn_robot,
        node_spawn_ball,
        node_vision,
        node_video_server,
        node_bridge,
        ros2_to_http,
    ])
