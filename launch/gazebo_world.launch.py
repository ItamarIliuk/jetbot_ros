import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

from ament_index_python.packages import get_package_share_directory

# chassis -> camera_link pose (x y z roll pitch yaw) for the legacy SDF models. Gazebo doesn't
# publish TF for an SDF fixed joint, so RViz2 needs a static transform to place their camera.
# The URDF robot ('jetbot') gets all of its TF from robot_state_publisher instead.
LEGACY_CAMERA_TF = {
    'simple_diff_ros': ['0.175', '0', '0.2', '0', '0.1', '0'],
}


def spawn_robot(context, *args, **kwargs):
    pkg_dir = get_package_share_directory('jetbot_ros')

    model = LaunchConfiguration('robot_model').perform(context)
    name = LaunchConfiguration('robot_name')
    x, y, z = (LaunchConfiguration(k) for k in ('x', 'y', 'z'))
    use_sim_time = LaunchConfiguration('use_sim_time')

    if model == 'jetbot':
        xacro_file = os.path.join(pkg_dir, 'urdf', 'jetbot.urdf.xacro')
        robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)

        return [
            Node(package='robot_state_publisher', executable='robot_state_publisher',
                 namespace=name,
                 # publish_frequency defaults to 20 Hz, which silently drops joint_states published
                 # faster than that and makes the wheels stutter in RViz2; keep it above the plugin rate.
                 parameters=[{'robot_description': robot_description,
                              'use_sim_time': use_sim_time,
                              'publish_frequency': 100.0}],
                 output='screen'),

            Node(package='gazebo_ros', executable='spawn_entity.py',
                 arguments=['-topic', ['/', name, '/robot_description'],
                            '-entity', name,
                            '-robot_namespace', name,
                            '-x', x, '-y', y, '-z', z],
                 output='screen'),
        ]

    # legacy path: plain SDF models under gazebo/models/<robot_model>/model.sdf
    actions = [
        Node(package='jetbot_ros', executable='gazebo_spawn',
             parameters=[{'name': name}, {'model': model}, {'x': x}, {'y': y}, {'z': z}],
             output='screen', emulate_tty=True),
    ]

    if model in LEGACY_CAMERA_TF:
        cx, cy, cz, croll, cpitch, cyaw = LEGACY_CAMERA_TF[model]
        actions.append(
            Node(package='tf2_ros', executable='static_transform_publisher',
                 arguments=['--x', cx, '--y', cy, '--z', cz,
                            '--roll', croll, '--pitch', cpitch, '--yaw', cyaw,
                            '--frame-id', 'chassis', '--child-frame-id', 'camera_link'],
                 output='screen'))

    return actions


def generate_launch_description():
    pkg_dir = get_package_share_directory('jetbot_ros')

    # model:// lookups for the worlds' models (gazebo/models/*); the URDF uses file:// mesh URIs
    os.environ['GAZEBO_MODEL_PATH'] = os.pathsep.join(
        [os.path.join(pkg_dir, 'models')]
        + [p for p in os.environ.get('GAZEBO_MODEL_PATH', '').split(os.pathsep) if p])

    # gazebo/plugins/user_camera_control_system is a standalone CMake project (not built by colcon);
    # build it once via `cmake` + `make` in gazebo/plugins/build, then point Gazebo at the output .so.
    plugin_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'gazebo', 'plugins', 'build')
    os.environ['GAZEBO_PLUGIN_PATH'] = plugin_dir + os.pathsep + os.environ.get('GAZEBO_PLUGIN_PATH', '')

    world = [os.path.join(pkg_dir, 'worlds', ''), LaunchConfiguration('world')]

    ros_plugins = ['-s', 'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so']

    gazebo = ExecuteProcess(
        cmd=['gazebo', '--verbose', world, *ros_plugins,
             '-g', 'libgazebo_user_camera_control_system.so'],
        condition=IfCondition(LaunchConfiguration('gui')),
        output='screen', emulate_tty=True)

    # gui:=false runs only the physics server (CI, SSH sessions, or debugging without a display)
    gzserver = ExecuteProcess(
        cmd=['gzserver', '--verbose', world, *ros_plugins],
        condition=UnlessCondition(LaunchConfiguration('gui')),
        output='screen', emulate_tty=True)

    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='dirt_path_curves.world',
                              description='world file under share/jetbot_ros/worlds'),
        DeclareLaunchArgument('robot_name', default_value='jetbot'),
        DeclareLaunchArgument('robot_model', default_value='jetbot',
                              description="'jetbot' (URDF with the real JetBot meshes) or the name "
                                          "of an SDF model under gazebo/models, e.g. simple_diff_ros"),
        DeclareLaunchArgument('x', default_value='-0.3'),
        DeclareLaunchArgument('y', default_value='-2.65'),
        DeclareLaunchArgument('z', default_value='0.0'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('gui', default_value='true',
                              description='false: run gzserver only (no Gazebo window)'),
        gazebo,
        gzserver,
        OpaqueFunction(function=spawn_robot),
    ])
