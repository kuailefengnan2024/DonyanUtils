from setuptools import setup, find_packages

setup(
    name='myutils',
    version='0.1.0',
    description='My personal Python utility library',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(), # Automatically find all packages under 'myutils'
    install_requires=[
        'requests',
        'Pillow', # For placeholder image
        'volcenginesdkarkruntime', # For Volcengine clients
        # Add other dependencies here
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License', # Choose your license
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7', # Specify your minimum Python version
)