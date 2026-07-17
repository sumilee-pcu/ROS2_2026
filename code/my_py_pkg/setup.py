from setuptools import find_packages, setup

package_name = "my_py_pkg"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages",
            ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="이수미",
    maintainer_email="sumileigh@gmail.com",
    description="ROS2 프로그래밍 첫걸음 - 파이썬 예제 패키지 (1권 3~7장)",
    license="MIT",
    entry_points={
        "console_scripts": [
            # 2장 - 첫 노드
            "my_first_node = my_py_pkg.my_first_node:main",
            # 3장 - 토픽
            "number_publisher = my_py_pkg.number_publisher:main",
            "number_subscriber = my_py_pkg.number_subscriber:main",
            # 4장 - 서비스
            "add_two_ints_server = my_py_pkg.add_two_ints_server:main",
            "add_two_ints_client = my_py_pkg.add_two_ints_client:main",
            # 5장 - 액션
            "fibonacci_server = my_py_pkg.fibonacci_server:main",
            "fibonacci_client = my_py_pkg.fibonacci_client:main",
            # 6장 - 파라미터
            "configurable_publisher = my_py_pkg.configurable_publisher:main",
        ],
    },
)
