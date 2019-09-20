from setuptools import setup
import pathlib

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

setup(
    name='skilletcli',
    version='2.0.0',
    packages=['Remotes', 'panos'],
    scripts=['skilletcli.py'],
    url='https://github.com/adambaumeister/skilletcli',
    license='Apache 2.0',
    author='abaumeister',
    author_email='abaumeister@paloaltonetworks.com',
    description='Packages and CLI tools for interacting with hosted Skillets.',
    install_requires=[
        "oyaml",
        "GitPython",
        "colorama",
        "jinja2",
        "passlib",
        "requests",
        "beautifultable",
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    download_url='https://github.com/adambaumeister/skilletcli/releases/latest/download/skilletcli.tar.gz',
    long_description=README,
    long_description_content_type="text/markdown"
)
