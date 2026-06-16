# 2장. 워크스페이스와 패키지, 빌드 시스템

> **학습 목표**
> - 워크스페이스(workspace)가 무엇이고 왜 필요한지 설명할 수 있다.
> - colcon과 ament의 역할, 그리고 빌드와 소싱(sourcing)의 흐름을 이해한다.
> - 내 손으로 워크스페이스를 만들고 colcon build 한다.
> - Python 패키지(ament_python)와 C++ 패키지(ament_cmake)를 각각 생성하고 구조를 읽는다.
> - 오버레이/언더레이(overlay/underlay) 개념으로 내 코드가 왜 인식되는가를 안다.

> **이번 장의 산출물**
> - ~/ros2_ws 워크스페이스와 Python/C++ 예제 패키지를 만든다.
> - src, build, install, log 디렉터리의 역할을 설명한다.
>
> **공통 학습 흐름**: 개념 → 따라하기 → 코드 해설 → 실행 확인 → 버전/환경 체크 → 트러블슈팅 → 연습문제 → 마무리 점검

1장에서 ROS 2를 설치하고 talker/listener를 돌려 봤다. 그건 남이 만든 노드였다.
이 장부터는 내 코드를 담을 그릇을 만든다. 그 그릇이 워크스페이스이고, 그릇 안의
부품 단위가 패키지다. 여기서 만든 워크스페이스를 2부 내내 계속 쓰게 된다.

---

## 2.1 워크스페이스란 무엇인가

**워크스페이스(workspace)** 는 내가 만든 ROS 2 패키지들을 한곳에 모아 함께 빌드하는
작업 폴더다. ROS 2 개발은 거의 항상 이 구조 위에서 이뤄진다.

워크스페이스 이름은 관례상 ros2_ws 를 많이 쓰지만, 사용자가 임의로 정의할 수 있다.
이 책에서는 홈 디렉터리 아래 ros2_ws 를 기준으로 설명한다.

```bash
mkdir -p ~/ros2_ws/src
```

핵심 규칙은 단 하나다.

> 모든 소스 패키지는 워크스페이스의 src 폴더 안에 둔다.

src 에 패키지를 넣고 워크스페이스 최상위에서 빌드하면, ROS 2는 자동으로 src 아래를
훑어 패키지들을 찾아 빌드한다. 빌드 결과는 워크스페이스 안의 네 폴더에 나뉘어 생긴다.

![그림 2-4. 워크스페이스 폴더 구조](figures/fig2-4.png)

| 폴더 | 생성 시점 | 내용 |
|---|---|---|
| src/ | 내가 직접 생성 | 소스 코드(패키지들). 유일하게 사람이 손대는 곳 |
| build/ | 빌드 시 자동 | 중간 빌드 산출물(오브젝트 파일 등) |
| install/ | 빌드 시 자동 | 설치 결과 — 실행에 필요한 것이 여기 모인다 |
| log/ | 빌드 시 자동 | 빌드 로그 |

> build, install, log 는 언제든 지우고 다시 빌드해도 된다. 버전 관리(git)에는
> src 만 올리고 나머지 셋은 .gitignore 로 제외하는 것이 표준이다.

---

## 2.2 colcon과 ament — 빌드 시스템의 두 축

ROS 1을 써 봤다면 catkin_make 를 기억할 것이다. ROS 2에서는 이것이 둘로 나뉘었다.

- **colcon** — Collective Construction 의 약자로, 워크스페이스 전체를 빌드하는 빌드 도구(명령)다.
  src 폴더 아래 패키지들을 의존성 순서대로 모아서 빌드하는 것을 담당한다.
  (1장에서 ros-dev-tools 로 함께 설치했다)
- **ament** — 패키지 하나하나가 어떻게 빌드되는지를 정의하는 빌드 시스템으로 언어에 따라
  두 종류를 쓴다.
  - ament_python — Python 패키지용. setup.py/setup.cfg 로 설정.
  - ament_cmake — C++ 패키지용. CMakeLists.txt 로 설정.

ament 는 패키지 내부를 구성하고 빌드하는 명세(API)고, colcon 은 이 ament 패키지들을
전체적으로 모아서(Collection) 의존성 순서대로 빌드해 주는 빌드 도구(Build Tool)다.

![그림 2-2. colcon과 ament의 역할 분리](figures/fig2-2.png)

> **Foxy → Jazzy 차이**
> 빌드 도구와 시스템의 큰 틀(colcon + ament)은 Foxy와 동일하다. 다만 Jazzy의 기반인
> Ubuntu 24.04 는 Python 3.12 를 쓰는데, 이 버전에서 ament_python 패키지를 빌드하면
> setup.py 방식에 대한 경고(SetuptoolsDeprecationWarning)가 보일 수 있다. 빌드는
> 정상적으로 끝나며 동작에 문제없다. 경고와 오류를 구분하는 눈이 필요하다(2.8절).

---

## 2.3 [따라하기] 워크스페이스 만들기

직접 만들어 보자. 터미널을 연다. (1장에서 ~/.bashrc 에 source /opt/ros/jazzy/setup.bash 를
넣었다고 가정한다)

![그림 2-3. 워크스페이스 생성부터 노드 실행까지의 흐름](figures/fig2-3.png)

**① 워크스페이스 폴더와 src 만들기**

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
```

`-p` 옵션은 중간 경로가 없어도 한 번에 생성하고, 이미 존재해도 오류를 내지 않는다.
~/ros2_ws/src 처럼 여러 단계를 한 번에 만들 때 유용하다.

**② 비어 있는 상태에서 환경 체크**

colcon build 는 반드시 워크스페이스 최상위 폴더(~/ros2_ws)에서 실행해야 한다.
src 안이나 다른 위치에서 실행하면 빌드 결과가 엉뚱한 곳에 생기거나 오류가 발생한다.

```bash
colcon build
```

src 가 비어 있어도 빌드는 성공하며, build install log 세 폴더가 생긴다.

```bash
ls
# build  install  log  src
```

각 폴더 안을 들여다보면 다음과 같은 파일이 생성돼 있다.

```text
./build:
COLCON_IGNORE

./install:
COLCON_IGNORE  local_setup.bash  local_setup.sh  local_setup.zsh
setup.bash  setup.sh  setup.zsh  ...

./log:
build_2026-06-14_15-49-02  COLCON_IGNORE  latest  latest_build
```

| 폴더 | 역할 |
|---|---|
| build/ | 각 패키지의 중간 빌드 산출물. CMake 캐시, 오브젝트 파일 등이 여기 쌓인다. |
| install/ | 빌드 완료 후 실행에 필요한 파일이 모인다. source 명령으로 이 폴더를 셸에 알린다. |
| log/ | 빌드 로그. 빌드 오류 추적에 쓴다. |

환경이 정상인 것을 확인했으면 세 폴더를 삭제한다. 실제 패키지를 추가한 뒤 다시 빌드할 것이다.

```bash
rm -rf build install log
```

**③ 워크스페이스 소싱(sourcing)**

빌드한 결과를 셸에 알려 줘야 ros2 run 으로 내 패키지를 실행할 수 있다.
지금은 install/ 폴더를 삭제했으므로 2.4절에서 패키지를 빌드한 뒤 아래 명령을 실행한다.

```bash
source ~/ros2_ws/install/setup.bash
```

> 이 줄이 바로 2.7절에서 설명할 오버레이를 활성화하는 명령이다. 새 터미널을 열 때마다
> 워크스페이스를 쓰려면 다시 실행해야 한다. 자주 쓰면 ~/.bashrc 에 추가해도 되지만,
> 워크스페이스가 여러 개라면 헷갈리니 처음엔 손으로 치며 흐름을 익히길 권한다.

> ~/.bashrc 에 넣을 때는 반드시 절대 경로로 써야 한다.
> ```bash
> source ~/ros2_ws/install/setup.bash   # 올바름 (절대 경로)
> source install/setup.bash             # 잘못됨 (상대 경로 — 터미널마다 실패)
> ```

---

## 2.4 [따라하기] Python 패키지 만들기

이제 src 안에 첫 패키지를 만든다. ROS 2는 패키지 뼈대를 자동 생성해 주는 명령을 준다.

```bash
cd ~/ros2_ws/src
ros2 pkg create my_py_pkg --build-type ament_python --dependencies rclpy
```

- my_py_pkg — 패키지 이름
- --build-type ament_python — Python 패키지로 만든다
- --dependencies rclpy — 의존성으로 rclpy(ROS 2 Python 클라이언트 라이브러리) 추가

생성된 구조:

```text
my_py_pkg/
├── my_py_pkg/          ← 실제 파이썬 모듈 (노드 .py 를 여기에 둔다)
│   └── __init__.py
├── resource/my_py_pkg
├── test/               ← 자동 생성된 테스트 (스타일 검사 등)
├── package.xml         ← 패키지 메타정보와 의존성
├── setup.py            ← 빌드·설치 설정 및 노드 실행 명령 등록
└── setup.cfg           ← 스크립트 설치 경로 지정 (최소 설정)
```

> Jazzy(Python 3.12) 기준으로 패키지의 실질적인 설정은 setup.py 에 담긴다.
> 노드를 ros2 run 으로 실행하려면 setup.py 의 entry_points 안 console_scripts 에 등록해야 한다.
>
> setup.py 의 console_scripts 부분:
> ```python
> entry_points={
>     'console_scripts': [
>         # 'my_node = my_py_pkg.my_node:main',   # 3장에서 채운다
>     ],
> },
> ```
>
> setup.cfg 는 스크립트 설치 경로만 담는 최소 파일이다. 직접 편집할 일은 거의 없다.
> ```ini
> [develop]
> script_dir=$base/lib/my_py_pkg
> [install]
> install_scripts=$base/lib/my_py_pkg
> ```

빌드하고 소싱한다. 반드시 워크스페이스 최상위에서 빌드한다.

```bash
cd ~/ros2_ws
colcon build
source ~/ros2_ws/install/setup.bash
```

> source ~/ros2_ws/install/setup.bash 는 내 워크스페이스를 셸에 알리는 오버레이 소싱이다.
> /opt/ros/jazzy/setup.bash 가 ROS 2 본체(시스템 설치 패키지들)를 셸에 알리는 것이라면,
> ~/ros2_ws/install/setup.bash 는 그 위에 내가 만든 패키지를 얹는 것이다.
> 자세한 내용은 2.7절에서 다룬다.

> Python 코드는 수정할 때마다 다시 빌드하기 번거롭다. 심볼릭 링크 설치를 쓰면
> .py 를 고칠 때 재빌드 없이 바로 반영된다. 입문 단계에서 특히 편하다.
> ```bash
> colcon build --symlink-install
> ```

---

## 2.5 [따라하기] C++ 패키지 만들기

같은 워크스페이스에 C++ 패키지도 만들어 둔다. (이 책은 Python/C++ 병행이 원칙이다)

```bash
cd ~/ros2_ws/src
ros2 pkg create my_cpp_pkg --build-type ament_cmake --dependencies rclcpp
```

- --build-type ament_cmake — C++ 패키지
- --dependencies rclcpp — C++ 클라이언트 라이브러리

생성된 구조:

```text
my_cpp_pkg/
├── include/my_cpp_pkg/ ← 헤더 (.hpp)
├── src/                ← 소스 (.cpp) 를 여기에 둔다
├── package.xml         ← 메타정보와 의존성 (Python 과 동일 형식)
└── CMakeLists.txt      ← 빌드 설정 (ament_cmake)
```

다시 워크스페이스 최상위에서 빌드한다.

```bash
cd ~/ros2_ws
colcon build
source ~/ros2_ws/install/setup.bash
```

이제 워크스페이스에 패키지 두 개(my_py_pkg, my_cpp_pkg)가 함께 빌드된다. 확인:

```bash
ros2 pkg list | grep my_
# my_cpp_pkg
# my_py_pkg
```

---

## 2.6 패키지 구조 해부 — 무엇이 무엇을 정의하나

패키지를 처음 만들면 파일이 여럿 생겨 막막하다. 딱 두 종류만 이해하면 된다.

### package.xml — 이 패키지는 무엇이고 무엇에 의존하는가

Python/C++ 공통이다. 패키지 이름, 버전, 설명, 라이선스, 그리고 의존성을 적는다.
Jazzy 에서 ros2 pkg create 가 생성하는 package.xml 은 format 3 을 사용한다.

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>my_py_pkg</name>
  <version>0.0.0</version>
  <description>TODO: Package description</description>
  <maintainer email="user@todo.todo">user</maintainer>
  <license>TODO: License declaration</license>

  <depend>rclpy</depend>

  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>python3-pytest</test_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

colcon 은 이 의존성을 읽어 빌드 순서를 정한다. A가 B에 의존하면 B를 먼저 빌드한다.

### setup.py (Python) / CMakeLists.txt (C++) — 무엇을 빌드·설치하는가

특히 Python 에서 노드를 실행 명령으로 등록하는 곳이 setup.py 의 console_scripts 다.
3장에서 노드를 만들면 여기에 등록해야 ros2 run 으로 실행된다. 지금은 위치만 기억한다.

> 자주 하는 실수: 노드 .py 를 만들어도 setup.py 의 console_scripts 에 등록하지 않으면
> ros2 run 이 못 찾는다. 코드는 맞는데 실행이 안 될 때 1순위로 의심할 곳이다.

---

## 2.7 오버레이와 언더레이 — 내 코드가 인식되는 원리

소싱을 두 번 한다는 점이 처음엔 헷갈린다. 구조를 그림으로 보자.

![그림 2-1. 언더레이와 오버레이의 계층 구조](figures/fig2-1.png)

- **언더레이**: ROS 2 배포판 자체. 보통 ~/.bashrc 에서 자동 소싱(1장).
- **오버레이**: 내 워크스페이스. 언더레이 위에 얹혀, 같은 이름이 있으면 오버레이가 우선.

즉 source install/setup.bash 는 내가 방금 빌드한 패키지들을 이 셸이 알게 하라는 뜻이다.
이걸 안 하면 ros2 run my_py_pkg ... 가 패키지를 못 찾음 오류를 낸다.

> **setup.bash 와 local_setup.bash 의 차이**
> install 폴더에는 파일이 두 개 생긴다.
> - setup.bash — 언더레이 포함 전체 소싱. 일반적으로 이것을 쓴다.
> - local_setup.bash — 이 워크스페이스만 소싱. 워크스페이스를 여러 겹 쌓는 고급 용도.
> 처음에는 setup.bash 만 쓰면 된다.

> 흔한 함정: 빌드한 터미널과 실행하는 터미널이 다른 경우. 새 터미널에는 오버레이가
> 안 걸려 있다. 새 터미널에서 실행하려면 그 터미널에서 다시
> source ~/ros2_ws/install/setup.bash 를 실행한다.

---

## 코드 해설 · 실행 확인 · 버전 체크

- **코드 해설 포인트**: package.xml, setup.py, CMakeLists.txt 가 빌드와 실행에 어떻게 관여하는지 해설한다.
- **실행 확인 포인트**: colcon build, source install/setup.bash, ros2 pkg list | grep my_ 로 빌드 결과를 확인한다.
- **버전/환경 체크**: Ubuntu 24.04 의 Python 3.12 와 setuptools 경고, Jazzy 의 colcon 사용 흐름을 기준으로 정리한다.

---

## 2.8 트러블슈팅 — 막혔을 때

| 증상 | 원인 | 해결 |
|---|---|---|
| colcon: command not found | dev-tools 미설치 | sudo apt install ros-dev-tools (1장) |
| ros2 run 이 패키지를 못 찾음 | 오버레이 미소싱 | source ~/ros2_ws/install/setup.bash |
| src 비었는데 빌드해도 install 없음 | 워크스페이스 최상위 아님 | pwd 로 위치 확인 후 cd ~/ros2_ws |
| src 안에서 colcon build 를 쳤다 | 잘못된 위치 | cd ~/ros2_ws 로 이동 후 재실행 |
| SetuptoolsDeprecationWarning 노란 경고 | Ubuntu 24.04 Python 3.12 | 경고일 뿐, 무시 가능. 빌드 성공은 마지막 Summary 줄로 판단 |
| 패키지 하나만 다시 빌드하고 싶다 | 전체 재빌드는 느림 | colcon build --packages-select my_py_pkg |
| 빌드가 꼬였다 (이상한 캐시) | build/install 오염 | rm -rf build install log 후 재빌드 |
| 새 터미널에서 내 패키지가 안 보인다 | 오버레이 소싱 안 함 | 새 터미널마다 source ~/ros2_ws/install/setup.bash |

> 경고는 오류가 아니다. colcon build 마지막의 Summary: N packages finished 가 보이면
> 성공이다. 빨간 Failed 가 없으면 노란 경고는 넘어가도 된다.

---

## 2.9 연습문제

1. ~/ros2_ws 에 my_first_pkg 라는 Python 패키지를 rclpy 의존성으로 추가 생성하고
   빌드하라. ros2 pkg list 에서 보이는지 확인하라.
2. build install log 를 모두 지운 뒤 다시 colcon build 하라. 무엇이 다시 생기는가?
3. 새 터미널을 열어 소싱 없이 ros2 pkg list | grep my_ 를 실행해 보라. 왜 안 보이는가?
   보이게 하려면 무엇을 해야 하는가?
4. package.xml 을 열어 depend 줄을 찾아라. my_cpp_pkg 는 무엇에 의존하는가?
5. (생각해보기) 왜 src 만 git 에 올리고 build/install/log 는 올리지 않을까?

---

## 2.10 마무리 점검

- [ ] 워크스페이스의 src/build/install/log 역할을 각각 한 줄로 말할 수 있다.
- [ ] colcon(빌드 도구)과 ament(빌드 시스템) 차이를 설명할 수 있다.
- [ ] Python(ament_python), C++(ament_cmake) 패키지를 각각 만들어 빌드했다.
- [ ] 오버레이 소싱(source install/setup.bash)이 왜 필요한지 안다.
- [ ] setup.bash 와 local_setup.bash 의 차이를 안다.
- [ ] 경고와 오류를 구분해 빌드 성공 여부를 판단할 수 있다.

> **다음 장 예고** — 3장에서는 방금 만든 my_py_pkg/my_cpp_pkg 안에 첫 노드를
> 작성하고, 토픽(topic)으로 메시지를 발행/구독한다. setup.py 의 console_scripts 가
> 드디어 채워진다.

---

## 2.11 [워크드 예제] 빈 워크스페이스부터 첫 패키지까지 한 호흡

아래를 그대로 따라 하면 2장 전체가 손에 익는다. 각 명령의 결과를 확인하며 진행한다.

```bash
# 1. 워크스페이스 골격
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws
colcon build                         # build/ install/ log/ 생성
ls                                   # build install log src

# 2. Python 패키지 생성
cd src
ros2 pkg create demo_py --build-type ament_python --dependencies rclpy
ls demo_py                           # demo_py/ package.xml setup.py setup.cfg ...

# 3. 빌드 + 오버레이 소싱
cd ~/ros2_ws
colcon build --packages-select demo_py
source ~/ros2_ws/install/setup.bash

# 4. 인식 확인
ros2 pkg list | grep demo_py         # demo_py 가 보이면 성공
ros2 pkg executables demo_py         # (아직 노드 없음 → 비어 있음, 정상)
```

마지막에 demo_py 가 목록에 보이면, 빈 그릇에 첫 패키지를 담아 빌드/인식까지 시킨 것이다.
3장에서 이 패키지 안에 노드를 넣으면 4번의 executables 에 노드 이름이 등장한다.

---

## 2.12 colcon 자주 쓰는 옵션 정리

매번 전체 빌드는 느리다. 실무에서 쓰는 옵션을 외워 두면 개발 속도가 크게 빨라진다.

| 옵션 | 효과 | 언제 |
|---|---|---|
| --packages-select A B | A, B 패키지만 빌드 | 특정 패키지만 수정했을 때 |
| --packages-up-to A | A와 A가 의존하는 것까지 | 의존 패키지가 바뀌었을 때 |
| --symlink-install | 설치를 심볼릭 링크로 | Python 코드 수정 잦을 때 (재빌드 불필요) |
| --event-handlers console_direct+ | 빌드 로그 실시간 출력 | 빌드가 멈춘 듯할 때 원인 파악 |
| rm -rf build install log | 캐시 초기화 | 빌드가 꼬였을 때 |

---

## 2.13 연습문제 해설(요약)

- **1번** ros2 pkg create my_first_pkg --build-type ament_python --dependencies rclpy 후
  워크스페이스 최상위에서 colcon build → source ~/ros2_ws/install/setup.bash → ros2 pkg list.
- **2번** 세 폴더를 지워도 src 만 있으면 colcon build 가 build/install/log 를 다시
  생성한다. 소스가 src 에 있기 때문이다.
- **3번** 새 터미널은 오버레이가 안 걸려 있어 안 보인다. 그 터미널에서
  source ~/ros2_ws/install/setup.bash 를 하면 보인다 (2.7절 오버레이).
- **4번** my_cpp_pkg 는 생성 시 --dependencies rclcpp 를 주었으므로 rclcpp 에 의존한다.
- **5번** build/install/log 는 재생성 가능한 산출물이라 git 에 올리면 용량만 키우고 충돌을
  부른다. 소스(src)만 버전 관리하는 것이 원칙이다.

---

### 참고 자료
- ROS 2 Jazzy — Creating a workspace: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Creating-A-Workspace/Creating-A-Workspace.html
- ROS 2 Jazzy — Creating a package: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Creating-Your-First-ROS2-Package.html
- colcon 문서: https://colcon.readthedocs.io/
- 표윤석/임태훈, ROS 2로 시작하는 로봇 프로그래밍, 루비페이퍼 — 빌드 시스템 장
