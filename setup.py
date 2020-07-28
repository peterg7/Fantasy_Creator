from setuptools import setup

setup(
    name='Fantasy Creator',
    version='0.1',
    author='Peter C Gish',
    author_email='peter.gish11@gmail.com',
    description='Bring your fantasy to life',
    long_description=open('docs/README.rst', 'r').read(),
    license='MIT',
    packages=['fantasycreator'],
    # , 'fantasycreator.resources', 'fantasycreator.resources.samples',
    #             'fantasycreator.resources.icons', 'fantasycreator.resources.images',
    #             'fantasycreator.resources.icons.map', 'fantasycreator.resources.icons.tabbar',
    #             'fantasycreator.resources.icons.toolbar', 'fantasycreator.resources.images.test'],
    install_requires=['PyQt5', 'numpy', 'tinydb', 'sortedcontainers'],
    python_requires='>=3.8',
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'fantasycreator = fantasycreator.__main__:main'
        ]
    }
)7