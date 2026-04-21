from setuptools import setup, find_packages

setup(
    name="pwm-miner",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "web3>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "pwm-miner=pwm_miner.__main__:main",
        ],
    },
)
