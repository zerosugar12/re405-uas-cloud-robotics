from setuptools import setup
from glob import glob
import os

package_name = 'robot_description'

def data_files_from(pattern):
    return [f for f in glob(pattern) if os.path.isfile(f)]

setup(
    name=package_name,
    version='0.0.0',
    packages=[],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'urdf'), data_files_from('urdf/*')),
        (os.path.join('share', package_name, 'urdf/components'), data_files_from('urdf/components/*')),
        (os.path.join('share', package_name, 'meshes'), data_files_from('meshes/*')),
        (os.path.join('share', package_name, 'rviz'), data_files_from('rviz/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='rei',
    maintainer_email='rei@rei.todo',
    description='Robot description package',
    license='Apache-2.0',
    tests_require=['pytest'],
)
