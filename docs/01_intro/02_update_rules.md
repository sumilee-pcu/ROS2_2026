# 참고 자료
- ~/Projects/ROS2_2026/refs/ 오로카, 핑크랩 문서    
- 이 문서들은 foxy, humble 기준이므로 내용 참고만 하도록 한다
- pdf 폴더에 공동작성자의 pdf 파일을 참조해서 각 챕터간 톤과 스타일이
  일관되도록 한다.

# 공통 사항
- 제목, 소제목, 목차, 캡션, 각주 등에 이모지 사용 금지 - AI작성글로 보임
- 따음표 사용 금지 
- 각절에 추가되었으면 하는 내용있으면 나에게 먼저 물어보고  okay하면 진행
- 나의 개인 정보가 있으면 적절한 다른 단어나 숫자로 대체한다.

# 수정할 부분
## 2.1
- 시작부분에 ros2_ws 로 언급은 되어 있지만 이 절에서 ros2_ws 만드는 부분을 추가한다.
- 트리구조 최상단에 ros2_ws이 오도록 한다.
- 워크스페이스 이름은 사용자가 임의로 정의할 수 있다고 언급한다.
- 패키지를 빌드하기 전에 환경 체크를 위해 src 아래 빈 상태에서 colcon build를 수행해서 build,install,log 
  폴더가 정상적으로 생성되는지 확인한다. 확인 후 이 세 폴더를 삭제한다
- 이 부분을 2.1에 넣을지 2.2에 넣을지 내용 전개상 자연스러운 곳에 넣는다

## 2.2
- colcon이 Collective Constructio 의 약자라는 것을 명시
- colcon과 ament 비유를 다른 것으로 작성(e.g. ament는 패키지 내부를 구성하고 빌드하는 명세(API), colcon build는 이 ament 패키지들을 전체적으로 모아서(Collection) 순서대로 빌드해 주는 빌드 도구(Build Tool))
- "첫 빌드는 패키지가 없어도 30초 안팎이.." 이 부분 다시 검증하고 수정
- 
## 2.3
- mkdir p 옵션에 행행해 간단하게 설명
- colcon build 는 항상 워크스페이스 최상위 폴더에서 해야한다고 강조
- 비어있는 src를 빌드하면 3개의 폴더가 생기는데 각 폴더의 역할에 대해 추가

  minodori@16Z95P:~/ros2_ws$ ls ./*
  ./build:
  COLCON_IGNORE

  ./install:
  COLCON_IGNORE     local_setup.ps1  _local_setup_util_ps1.py  local_setup.zsh  setup.ps1  setup.zsh
  local_setup.bash  local_setup.sh   _local_setup_util_sh.py   setup.bash       setup.sh

  ./log:
  build_2026-06-14_15-49-02  COLCON_IGNORE  latest  latest_build

  ./src:

- 빌드한 결과를 셸에 알려 줘야... '셸', '쉘', '셀' 어느게 적절한지 판단하고 수정

## 2.4
- opt/ros/jazzy/setup.bash, ~/ros2_ws/install/setup.bash 차이에 대해 기술
- setup.cfg 핵심 부분 설명이 실제 jazzy에서 실행했을때와 다르다. 체크하고 수정하라
  실행결과  setup.cfg
  [develop]
  script_dir=$base/lib/my_py_pkg
  [install]
  install_scripts=$base/lib/my_py_pkg


## 2.6 
- package.xml 실제 내용이다. 참고해서 현재 문서를 업데이트해라
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>my_py_pkg</name>
  <version>0.0.0</version>
  <description>TODO: Package description</description>
  <maintainer email="minodori@gmail.com">minodori</maintainer>
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

# 추가 수정 사항(26년 6월 15일)
## 2.1 
- 폴더 구조가 워드에서 깔끔하게 보이지 않는다. 그림 파일로 변경
## 2.2
- 그림 2-2 '의존성 순서 정렬 후 각 패키지를 ...' 부분이 그림의 선과 겹쳐있다. 문장을 좌측으로 이동해서 화살표 선과 겹치지 않도록 한후 md,docx를 업데이트하자.                                       