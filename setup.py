from setuptools import setup, find_packages

setup(
    name='DonyanUtils',
    version='0.1.0',
    description='My personal Python utility library',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(), # 自动查找'DonyanUtils'下的所有包
    install_requires=[
        'requests',
        'Pillow', # 用于占位符图像
        'volcengine-python-sdk[ark]>=3.0.0', # 用于火山引擎客户端
        # 在此添加其他依赖项
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License', # 选择您的许可证
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7', # 指定您的最低Python版本
)