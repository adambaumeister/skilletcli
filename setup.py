from setuptools import setup

setup(
    name='skilletcli',
    version='1.9.5',
    packages=['Remotes', 'panos'],
    scripts=['skilletcli.py'],
    url='https://github.com/adambaumeister/skilletcli',
    license='Apache 2.0',
    author='abigs',
    author_email='abaumeister@paloaltonetworks.com',
    description='Packages and CLI tools for interacting with hosted Skillets.',
    install_requires=[
        "oyaml",
        "GitPython",
        "colorama",
        "jinja2",
        "passlib",
        "requests",
    ]
)
