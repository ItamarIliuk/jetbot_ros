import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    launch_dir = os.path.join(get_package_share_directory('jetbot_ros'), 'launch')

    # nav_model already runs in the /jetbot namespace, so it picks up the simulated
    # /jetbot/camera/image_raw and drives /jetbot/cmd_vel without any remapping.
    return LaunchDescription([
        DeclareLaunchArgument('model',
                              default_value='/workspace/src/jetbot_ros/data/models/202106282129/model_best.pth',
                              description='path to the trained navigation model (.pth)'),
        DeclareLaunchArgument('robot_model', default_value='jetbot'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(launch_dir, 'gazebo_world.launch.py')),
            launch_arguments={'robot_model': LaunchConfiguration('robot_model')}.items()),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(launch_dir, 'nav_model.launch.py')),
            launch_arguments={'model': LaunchConfiguration('model')}.items()),
    ])
