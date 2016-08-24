from setuptools import setup
from pip.req import parse_requirements


install_reqs = parse_requirements('requirements.txt', session=False)
requirements = [str(ir.req) for ir in install_reqs]

setup(
    name='mergeit',
    version='0.1.0',
    packages=['mergeit'],
    url='https://github.com/insolite/mergeit',
    author='Oleg Krasnikov',
    author_email='a.insolite@gmail.com',
    description='GIT auto merge tool with branch dependencies, merge preprocessing and hooks',
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'mergeit = mergeit.scripts.run_server:main',
        ],
    },
)
