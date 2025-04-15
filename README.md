# Terraria Mod Manager
#### Effortlessly Manage Mods for Your Remote tModLoader Server

#### Video Demo: [Watch Here](https://youtu.be/DIWNO6ybL50)

Terraria Mod Manager is a Python app that simplifies mod management for remote tModLoader servers using [JACOBSMILE's Docker image](https://github.com/JACOBSMILE/tmodloader1.4). It connects to a server via SSH, retrieves the list of mods, and provides a user-friendly Tkinter interface for enabling/disabling mods. The app also handles mod dependencies and automates the process, making it ideal for server admins managing modded Terraria servers with Docker.

### Notes

- **SSH Access**: A remote server running [JACOBSMILE's](https://github.com/JACOBSMILE/tmodloader1.4) Docker image using Docker Compose must already be configured. SSH connections must be allowed as well

- **Docker Compose**: Review the generated Docker Compose file for accuracy before deploying the server.


## Installation

1. Clone the repository:
```bash
git clone https://github.com/haroonstar2/Terraria-Mod-Manager.git
```

2. Navigate to the project folder:

```bash
cd Terraria-Mod-Manager
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Run the application
```bash
python project.py
```

