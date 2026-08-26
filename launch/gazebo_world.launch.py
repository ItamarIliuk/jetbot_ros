import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import ThisLaunchFileDir, LaunchConfiguration
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

from ament_index_python.packages import get_package_share_directory
 
def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='True')
     
    robot_name = DeclareLaunchArgument('robot_name', default_value='jetbot')
    robot_model = DeclareLaunchArgument('robot_model', default_value='simple_diff_ros')  # jetbot_ros
    
    robot_x = DeclareLaunchArgument('x', default_value='-0.3')
    robot_y = DeclareLaunchArgument('y', default_value='-2.65')
    robot_z = DeclareLaunchArgument('z', default_value='0.0')
    
    world_file_name = 'dirt_path_curves.world'
    pkg_dir = get_package_share_directory('jetbot_ros')
 
    os.environ["GAZEBO_MODEL_PATH"] = os.path.join(pkg_dir, 'models')

    # gazebo/plugins/user_camera_control_system is a standalone CMake project (not built by colcon);
    # build it once via `cmake` + `make` in gazebo/plugins/build, then point Gazebo at the output .so.
    plugin_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'gazebo', 'plugins', 'build')
    os.environ["GAZEBO_PLUGIN_PATH"] = plugin_dir + os.pathsep + os.environ.get("GAZEBO_PLUGIN_PATH", "")
 
    world = os.path.join(pkg_dir, 'worlds', world_file_name)
    launch_file_dir = os.path.join(pkg_dir, 'launch')
 
    gazebo = ExecuteProcess(
                cmd=['gazebo', '--verbose', world, 
                     '-s', 'libgazebo_ros_init.so', 
                     '-s', 'libgazebo_ros_factory.so',
                     '-g', 'libgazebo_user_camera_control_system.so'],
                output='screen', emulate_tty=True)

    
    spawn_entity = Node(package='jetbot_ros', executable='gazebo_spawn',
                        parameters=[
                            {'name': LaunchConfiguration('robot_name')},
                            {'model': LaunchConfiguration('robot_model')},
                            {'x': LaunchConfiguration('x')},
                            {'y': LaunchConfiguration('y')},
                            {'z': LaunchConfiguration('z')},
                        ],
                        output='screen', emulate_tty=True)

    # The SDF's chassis->camera_link joint is fixed but nothing publishes its TF (Gazebo only
    # publishes what a plugin explicitly sends, and diff_drive only covers odom/wheel frames).
    # Without this, RViz2's Camera display can't resolve camera_link and fails to connect.
    # Pose matches gazebo/models/simple_diff_ros/model.sdf's camera_link <pose> (x y z roll pitch yaw).
    camera_tf = Node(package='tf2_ros', executable='static_transform_publisher',
                     arguments=['--x', '0.175', '--y', '0', '--z', '0.2',
                                '--roll', '0', '--pitch', '0.1', '--yaw', '0',
                                '--frame-id', 'chassis', '--child-frame-id', 'camera_link'],
                     output='screen')

    return LaunchDescription([
        robot_name,
        robot_model,
        robot_x,
        robot_y,
        robot_z,
        gazebo,
        spawn_entity,
        camera_tf,
    ])
