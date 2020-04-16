import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
        name="Veracity",
        version="0.1.0",
        author="birb007",
        description="Simple SAT solver",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/birb007/veracity",
        packages=setuptools.find_packages(),
        python_requires=">=3.8",
)
