import os
from setuptools import setup, find_packages


if __name__ == "__main__":

    setup(
        name="g3-payless",
        version="1.0.0",
        description="A payless implementation",
        long_description=open("README.md", "r").read(),
        long_description_content_type="text/markdown",
        author="Hermann Krumrey, Mo Shen, Felix John",
        url="https://git.scc.kit.edu/tm-praktika/ppsdn-2020/g3",
        packages=find_packages(),
        install_requires=[
            "ryu"
        ],
        scripts=list(map(lambda x: os.path.join("bin", x), os.listdir("bin"))),
        include_package_data=True,
        zip_safe=False
    )
