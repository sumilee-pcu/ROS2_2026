# 예제 코드 — ROS2 프로그래밍 첫걸음 (1권)

이 책 전 장이 공유하는 실습 코드다. 공저 4인은 각자 장을 쓸 때 새 노드를 만들지 말고,
아래 노드를 기준으로 예제를 맞춘다. 독자도 이 코드를 그대로 빌드해 실행한다.

기준 환경: Ubuntu 24.04 / ROS 2 Jazzy.

## 패키지

| 패키지 | 언어 | 상태 |
|---|---|---|
| `my_py_pkg` | Python | 3~7장 노드 수록 (완성) |
| `my_cpp_pkg` | C++ | 예정 (동일 기능을 rclcpp로) |
| `my_robot_interfaces` | 인터페이스 | 예정 (6장 커스텀 메시지·서비스·액션) |

6장 전(3·4·5장)은 커스텀 인터페이스를 만들지 않고 표준 타입(`example_interfaces`)만 쓴다.

## 노드 ↔ 장 매핑 (`my_py_pkg`)

| 장 | 노드 | 실행 파일 | 쓰는 타입 |
|---|---|---|---|
| 2장 | 첫 노드 | `my_first_node` | - |
| 3장 토픽 | 발행 | `number_publisher` | `example_interfaces/msg/Int64` |
| 3장 토픽 | 구독 | `number_subscriber` | 〃 |
| 4장 서비스 | 서버 | `add_two_ints_server` | `example_interfaces/srv/AddTwoInts` |
| 4장 서비스 | 클라이언트 | `add_two_ints_client` | 〃 |
| 5장 액션 | 서버 | `fibonacci_server` | `example_interfaces/action/Fibonacci` |
| 5장 액션 | 클라이언트 | `fibonacci_client` | 〃 |
| 6장 파라미터 | 파라미터 퍼블리셔 | `configurable_publisher` | `example_interfaces/msg/Int64` |

7장 런치는 위 노드들(`number_publisher`·`number_subscriber`·`configurable_publisher`)을
`my_robot_bringup`의 런치 파일로 묶어 실행한다.

## 빌드와 실행

```bash
# 1. 워크스페이스로 복사 (또는 심볼릭 링크)
mkdir -p ~/ros2_ws/src
cp -r my_py_pkg ~/ros2_ws/src/

# 2. 빌드
cd ~/ros2_ws
colcon build --packages-select my_py_pkg
source install/setup.bash

# 3. 실행 예시
ros2 run my_py_pkg number_publisher       # 3장 토픽 발행
ros2 run my_py_pkg number_subscriber      # 3장 토픽 구독 (다른 터미널)
ros2 run my_py_pkg add_two_ints_server    # 4장 서비스 서버
ros2 run my_py_pkg fibonacci_server       # 5장 액션 서버
```

## 코드 규칙 (공저 공통)

- 노드 이름·토픽 이름·실행 파일 이름을 이 표와 똑같이 쓴다.
- Python과 C++를 나란히 제시한다(C++는 `my_cpp_pkg`가 준비되면 동일 이름으로).
- 코드는 실제로 빌드·실행되는 것만 싣는다. 자세한 규칙은 `../../ROS2_SKILL.md` 5절 참고.
