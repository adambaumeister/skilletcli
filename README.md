# SkilletCLI
## Overview
This utility provides a command line interface to Palo Alto "skillets", 
curated configuration templates designed to be imported into firewalls or Panorama.

## Installation
### Pre-requisites
To use skilletcli, a Git client must be installed.

[Installers for windows/OSX can be found here](https://git-scm.com/)

Linux users can use their preferred package manager.

### Getting the code
**windows/linux/OSX**

The latest release can be found [in the releases page for this project](https://github.com/adambaumeister/skilletcli/releases).
skilletCLI does not use an installer and runs using the one binary.

### Preparing the environment
SkilletCLI requires a variable file to be populated before use.

This file is used to template various snippets with environment specific information.
By default, this file is named config_variables.yaml, and it is retrieved from whichever directory
skilletcli is being run from.

[click here to see a complete example, populated with default values](README.md)

## Usage
### Overview of skillet layout
SkilletCLI returns a structure like the below:

Skillet Collection/Skillets/Snippet stacks/Snippet

A skillet collection is a group of skillets associated with a type, such as PANOS or PANORAMA. 
A snippet stack is a collection of snippets that have a specific use case.

By default, SkilletCLI will use the device type of the target firewall to determine which skillet type to use, and 
"snippets" for the snippet stack to use.

### Basic usage
*list all available snippets, skillets, and skillet collections*
```bash
skilletcli
```
This command lists all the available snippets.

*push a snippet to a device*
```bash
skilletcli address
```
This will push a single snippet "address" to the device, prompting for all login settings.

*push multiple snippets*
```bash
skilletcli address tag external_list
```
Same as the above except push multiple snippets in the one command. As many snippets as is required 
can be pushed like this.

### Environment variables
SkilletCLI allows you to use environment variables instead of an interactive prompt.

The variables are:
* SKCLI_USERNAME
* SKCLI_PASSWORD
* SKCLI_ADDRESS
