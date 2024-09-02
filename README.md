# Terraria Mod Manager
#### Easily Manage Mods for a Remote tModLoader Server
========================================================================================================================================================
#### Video Demo: https://youtu.be/DIWNO6ybL50
#### Description:

Terraria Mod Manager is a Python-based application designed to manage mods for a remote tModLoader server using [JACOBSMILE's](https://github.com/JACOBSMILE/tmodloader1.4) docker image. The application connects to a remote server via SSH, retrieves the list of enabled mods, and provides an interactive interface using Tkinter for enabling or disabling mods. It automates the mod management process, ensuring that dependencies are properly handled, and provides a user-friendly interface for managing mods. This tool is designed for users who manage modded Terraria servers with Docker and want a streamlined way to handle mods and dependencies.

## Files
**project.py**
- ModInfo class - Represents a mod and its properties, such as ID, internal name, workshop name, and dependencies.
- ModManager class - Handles all SSH and SFTP connections. Remotely executes custom commands on a Linux system
- Window class - Uses Tkinter to create several windows and widgets to handle user information. Handles faulty SSH, missing files, and other errors and provides a pop up window specifying the error.
- get_installed_mods(client) - Uses a ModManager object create a list of ModInfo objects containing information of every installed mod. ModManager and regular expressions are used to filter information to store into a ModInfo object.
- get_enabled_mods(client, target_directory) - Finds "enabled.json" using the user provided root directory. Uses ModManager and regular expressions to list the content and returns them as a list
- get_disabled_mods(installed, enabled) - Compares the results from get_installed_mods and get_enabled_mods and returns a list of all mods that are disabled
- get_mod_name(id) - Uses a tModLoader mod's id to create a url to the mod's Steam Workshop page. Requests and beautifulsoup4 are used to parse the HTML to find its workshop title.
- get_mod_requirements(id, processed_ids=None) - Recursively checks a mod's prerequisites using requests and beautifulsoup4.

## Features

- **SSH Integration**: Seamlessly connects to the remote server to fetch and manipulate mod files.
- **Dynamic Mod Detection**: Automatically detects and lists all mods in the specified directory.
- **Dependency Handling**: Automatically enables or disables required dependencies when mods are toggled.
- **User-Friendly Interface**: Built with Tkinter, the interface provides an intuitive way to manage mods, with checkboxes representing mod states.
- **Formats Docker compose file**: Generates a Docker Compose file with all relevant changes, allowing for easy deployment.

## Getting Started

### Prerequisites

- **SSH Access**: A remote server running [JACOBSMILE's](https://github.com/JACOBSMILE/tmodloader1.4) Docker image using Docker Compose. SSH connections must be allowed as well
- **Python 3.6+**: Ensure Python is installed on your local machine.
- **Tkinter**: This library comes pre-installed with Python, but make sure you have it.
- **PyYAML**: To parse YAML files
- **requests and beautifulsoup4**: To scrape and parse Steam Workshop content


## How It Works

1. Connection to the Remote Server

The application first establishes an SSH connection to the remote server where the modded Terraria server is hosted. The user provides credentials and connection details, which the application uses to execute remote commands. The user also provides the location of the Docker compose file on the remote server.

2. Searching for Mod Files

The root directory provided by the user is scanned for all installed mod information. The information is found and stored along with any relevent data taken from its Steam Workshop page. The program dynamically searches for the enabled.json file within the specified root directory. Once the enabled.json file is located, its contents are retrieved and parsed to determine which mods are currently enabled.

3. Interactive Mod Management

The GUI displays a list of all available mods with checkboxes indicating their enabled or disabled states. When a user toggles a mod, the program checks for any dependencies or conflicts and updates the state accordingly. It ensures that any required mods are enabled if a dependent mod is activated.

5. Saving Changes

After making changes to the mod configuration, the user can save these changes. The application updates the enviromental variables in the Docker Compose file and stores it remote server to reflect the new mod states, ensuring the modded Terraria server runs with the correct configuration. The Docker Compose file should be reviewed for accuracy before deployment.
