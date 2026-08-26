import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import ThisLaunchFileDir,LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    
    # NOTE: `ros2 launch` proxies child stdin through its own pty, which breaks this node's
    # raw termios keyboard reads even without a prefix. Needs a real separate terminal
    # (lxterminal/xterm) to own its own tty, or just run it directly: `ros2 run jetbot_ros teleop_keyboard`.
    teleop_keyboard = Node(package='jetbot_ros', executable='teleop_keyboard',
                           prefix='lxterminal -e', #'xterm -e'
                           output='screen',
                           emulate_tty=True)
       
    return LaunchDescription([
        teleop_keyboard
    ])