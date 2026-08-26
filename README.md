# jetbot_ros
ROS2 nodes and Gazebo model for NVIDIA JetBot with Jetson Nano

> note:  if you want to use ROS Melodic, see the [`melodic`](https://github.com/dusty-nv/jetbot_ros/tree/melodic) branch

## Como rodar

Escolha a opção que combina com o seu ambiente:

| Ambiente | Quando usar | Seção |
|---|---|---|
| **Jetson Nano** (hardware real) | Você tem um JetBot físico | [Jetson Nano (Docker)](#jetson-nano-docker) |
| **WSL2** (Windows 11, notebook pessoal) | Rodar a simulação no seu próprio notebook | [WSL2 (notebook pessoal)](#wsl2-notebook-pessoal) |
| **Ubuntu 22.04 nativo** (VM VMware 17, LABRIOT) | Rodar nas máquinas do laboratório | [Ubuntu 22.04 na VM (LABRIOT)](#ubuntu-2204-na-vm-labriot) |

As opções WSL2 e VM do LABRIOT rodam **sem Docker**, direto sobre ROS2 Humble + Gazebo Classic instalados no sistema — as imagens Docker desse repositório são construídas para o L4T (Jetson/ARM64) e não existem/funcionam em x86_64.

---

## Jetson Nano (Docker)

### Start the JetBot ROS2 Foxy container

``` bash
git clone https://github.com/dusty-nv/jetbot_ros
cd jetbot_ros
docker/run.sh
```

### Run JetBot

If you have a real JetBot, you can start the camera / motors like so:

``` bash
ros2 launch jetbot_ros jetbot_nvidia.launch.py
```

or (for a Sparkfun Jetbot)
``` bash
ros2 launch jetbot_ros jetbot_sparkfun.launch.py
```

Otherwise, see the [`Launch Gazebo`](#launch-gazebo) section below to run the simulator.

### Launch Gazebo

``` bash
ros2 launch jetbot_ros gazebo_world.launch.py
```

Then to run the following commands, launch a new terminal session into the container:

``` bash
sudo docker exec -it jetbot_ros /bin/bash
```

---

## WSL2 (notebook pessoal)

Pré-requisitos (uma vez só):
- Windows 11 com WSL2 + Ubuntu 22.04 (o WSLg já vem junto, é o que dá suporte a aplicações gráficas como o Gazebo e o RViz2 sem configuração extra)
- ROS2 Humble instalado na distro. Se ainda não tiver, siga o [guia oficial](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html) e depois instale os pacotes do Gazebo:
  ```bash
  sudo apt update
  sudo apt install -y ros-humble-desktop ros-humble-gazebo-ros-pkgs \
      python3-colcon-common-extensions libgazebo-dev qtbase5-dev
  ```

### 1. Clonar e montar o workspace

```bash
git clone https://github.com/ItamarIliuk/jetbot_ros ~/JetBot/jetbot_ros
mkdir -p ~/ros2_ws/src
ln -s ~/JetBot/jetbot_ros ~/ros2_ws/src/jetbot_ros
```

### 2. Buildar o pacote ROS2

```bash
source /opt/ros/humble/setup.bash
cd ~/ros2_ws
colcon build --symlink-install --packages-select jetbot_ros
```

### 3. Instalar o modelo do robô no Gazebo

Precisa ter rodado o Gazebo pelo menos uma vez antes (para a pasta `~/.gazebo` existir):

```bash
timeout 10 gazebo --verbose > /dev/null 2>&1   # cria ~/.gazebo na primeira execução
cd ~/JetBot/jetbot_ros/gazebo
./install_jetbot_model.sh
```

### 4. Buildar o plugin de câmera do Gazebo (opcional)

O plugin `user_camera_control_system` é um projeto CMake separado (não faz parte do build do colcon). Sem ele a simulação funciona igual, só aparece um aviso no log do Gazebo dizendo que não achou o `.so`:

```bash
mkdir -p ~/JetBot/jetbot_ros/gazebo/plugins/build
cd ~/JetBot/jetbot_ros/gazebo/plugins/build
cmake .. && make -j$(nproc)
```

### 5. Rodar

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch jetbot_ros gazebo_world.launch.py
```

Deixe esse terminal aberto rodando o Gazebo, e para os próximos comandos (teleop, RViz2 etc) abra **um novo terminal** e rode de novo os dois `source` acima antes de cada comando.

---

## Ubuntu 22.04 na VM (LABRIOT)

Mesmos passos do WSL2 (seções 1 a 5 acima), com estas diferenças específicas de VMware Workstation 17:

- **Aceleração 3D**: em *VM Settings → Display*, marque **Accelerate 3D graphics** e reserve pelo menos 1–2 GB de memória de vídeo. Sem isso o Gazebo tende a renderizar muito devagar ou travar.
- **VMware Tools**: garanta que o `open-vm-tools-desktop` está instalado (`sudo apt install -y open-vm-tools-desktop`) para resolução de tela e integração funcionarem direito.
- **Recursos da VM**: aloque pelo menos 4 GB de RAM e 2 vCPUs para a VM — o Gazebo é pesado.
- Como aqui é Ubuntu nativo (não WSL2), não existe equivalente ao WSLg: as janelas do Gazebo/RViz2 abrem normalmente no ambiente gráfico da própria VM, sem passo extra nenhum.

Se a imagem do laboratório já vem com ROS2 Humble e os pacotes do Gazebo instalados, pule direto para o passo 1 (clonar e montar o workspace) da seção WSL2 acima.

---

## Uso comum (WSL2 e VM)

### Test Teleop

O jeito mais simples e que sempre funciona é rodar o nó direto (sem passar pelo `ros2 launch`):

```bash
ros2 run jetbot_ros teleop_keyboard
```

> **Por quê não `ros2 launch jetbot_ros teleop_keyboard.launch.py`?** Esse launch file abre o node dentro de um terminal separado (`lxterminal`), que não vem instalado por padrão fora do container Jetson. Mesmo instalando um terminal (`sudo apt install lxterminal`), o `ros2 launch` proxya a entrada padrão (stdin) do processo filho, o que quebra a leitura de teclado raw do nó de teleop. Rodando com `ros2 run` direto no seu terminal isso não acontece.

The keyboard controls are as follows:

```
w/x:  increase/decrease linear velocity
a/d:  increase/decrease angular velocity

space key, s:  force stop
```

Press Ctrl+C to quit.

### Ver a câmera no RViz2

Com o `gazebo_world.launch.py` rodando, abra o RViz2 em outro terminal (lembrando de rodar os dois `source` primeiro):

```bash
rviz2
```

- **Fixed Frame**: `odom` (ou `chassis`)
- **Add → By display type → Image** (mais simples, só mostra o feed 2D) **ou Camera** (overlay 3D)
- **Topic**: `/jetbot/camera/image_raw`
- **Image Transport**: `raw`

O display **TF** também funciona normalmente e mostra os frames `odom → chassis → left_wheel/right_wheel/camera_link` se movimentando junto com o robô.

### Data Collection

``` bash
ros2 launch jetbot_ros data_collection.launch.py
```

> No Jetson (Docker), o dataset é salvo em `/workspace/src/jetbot_ros/data/datasets/`. No WSL2/VM, é salvo em `~/JetBot/jetbot_ros/data/datasets/` (ou onde você clonou o repositório).

É recomendável ver o feed da câmera pelo RViz2 (seção acima) ou pelo próprio Gazebo em `Window -> Topic Visualization -> gazebo.msgs.ImageStamped`, selecionando o tópico `/gazebo/default/jetbot/camera_link/camera/image`.

Then drive the robot and press the `C` key to capture an image.  Then annotate that image in the pop-up window by clicking the center point of the path.  Repeat this all the way around the track.  It's important to also collect data of when the robot gets off-course (i.e. near the edges of the track, or completely off the track).  This way, the JetBot will know how to get back on track.

Press Ctrl+C when you're done collecting data to quit.

### Train Navigation Model

Substitua o caminho do dataset que você coletou (por padrão fica numa pasta com timestamp, dentro de `data/datasets/` no local onde você clonou o repositório):

``` bash
cd ~/JetBot/jetbot_ros/jetbot_ros/dnn
python3 train.py --data ~/JetBot/jetbot_ros/data/datasets/20211018-160950/
```

(No Jetson/Docker, o caminho equivalente é `/workspace/src/jetbot_ros/...`, rodando de dentro do container.)

### Run Navigation Model

After the model has finished training, run the command below to have the JetBot navigate autonomously around the track.  Substitute the path to your model below:

``` bash
ros2 launch jetbot_ros nav_model.launch.py model:=/caminho/para/data/models/202106282129/model_best.pth
```

> note:  to reset the position of the robot in the Gazebo environment, press `Ctrl+R`

<a href="https://youtu.be/gok9pvUzZeY" target="_blank"><img src=https://github.com/dusty-nv/jetbot_ros/raw/dev/docs/images/jetbot_gazebo_sim_video.jpg width="750"></a>
