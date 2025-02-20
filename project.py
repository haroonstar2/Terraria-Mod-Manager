import tkinter
import tkinter.messagebox
import re
import os

import paramiko
import yaml
import requests
from bs4 import BeautifulSoup

class ModInfo:
    def __init__(self, workshop_id, internal_name):
        self.workshop_id = workshop_id
        self.internal_name = internal_name
        self.workshop_name = get_mod_name(workshop_id)
        self.required_items = get_mod_requirements(workshop_id)
        self.var = None
        self.checkbutton = None

class ModManager: 
    def __init__(self, hostname, username, password):
        match = re.search(r"\b[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b", hostname)
        if match:
            self.hostname = hostname
        else:
            raise ValueError
        
        self.username = username
        self.password = password

        try:
            self.client = self.create_ssh_client()
            self.sftp = self.create_sftp_client()
        except paramiko.SSHException:
            raise

    def create_ssh_client(self):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.hostname, username=self.username, password=self.password)
        return client

    def create_sftp_client(self):
        sftp = self.client.open_sftp()
        return sftp

    def execute_ssh_command(self, command):
        stdin, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode("utf-8")
    
    def close(self):
        self.client.close()
        self.sftp.close()

class Window:
    def __init__(self) -> None:
        # Initial login window
        self.login_window = tkinter.Tk()
        self.login_window.geometry("800x600")
        self.login_window.title("tModLoader Manager")
        frame = tkinter.Frame()

        # Adding Labels and Input Fields for SSH login
        ip_label = tkinter.Label(frame, text="Enter server ip", font=("Ariel", 18))
        username_label = tkinter.Label(frame, text="Enter server username", font=("Ariel", 18))
        password_label = tkinter.Label(frame, text="Enter server password", font=("Ariel", 18))
        target_directroy_label = tkinter.Label(frame, text="Enter path of docker compose file", font=("Ariel", 18))
        
        self.ip_entry = tkinter.Entry(frame)
        self.username_entry = tkinter.Entry(frame)
        self.password_entry = tkinter.Entry(frame, show="*")
        self.target_directroy_entry = tkinter.Entry(frame)
        login_button = tkinter.Button(frame, text= "Login", command=lambda: Window.login(self))

        # Placing Widgets on the grid
        ip_label.grid(row=0,column=0,pady=40)
        username_label.grid(row=1,column=0,pady=40)
        password_label.grid(row=2,column=0,pady=40)
        target_directroy_label.grid(row=3,column=0,pady=40)
        
        self.ip_entry.grid(row=0,column=1, pady=40, columnspan = 3)
        self.username_entry.grid(row=1,column=1,pady=40, columnspan = 3)
        self.password_entry.grid(row=2,column=1,pady=40, columnspan = 3)
        self.target_directroy_entry.grid(row=3,column=1,pady=40, columnspan = 3)
        login_button.grid(row=4,column=0,columnspan=2,pady=30)

        # Display the login window
        frame.pack()
        self.login_window.mainloop()
    
    def login(self):
        hostname = self.ip_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
        self.target_directory = self.target_directroy_entry.get()

        try:
            
            self.mod_manager = ModManager(hostname, username, password)
            self.check_remote_path_exists(self.target_directory)
            self.show_mods(self.mod_manager)
        except (AttributeError, ValueError, paramiko.SSHException, FileNotFoundError) as e:
            tkinter.messagebox.showerror(title="Error", message=f"Invalid Information Provided: {e}")

    def check_remote_path_exists(self, target_directory):
        output = self.mod_manager.execute_ssh_command(f"if [ -e '{target_directory}' ]; then echo 'Exists'; else echo 'Not Found'; fi").strip()
        if output == "Not Found":
            raise FileNotFoundError(f"The specified path was not found on the remote server: {target_directory}")

        # Search for docker-compose.yml in the directory
        find_command = f"find {target_directory} -type f -name 'docker-compose.yml'"
        docker_compose_path = self.mod_manager.execute_ssh_command(find_command).strip()
        if not docker_compose_path:
            raise FileNotFoundError(f"No 'docker-compose.yml' file found within the specified root directory: {target_directory}")

        # Ensure the docker-compose.yml file is valid
        file_content = self.mod_manager.execute_ssh_command(f"cat {docker_compose_path}")
        try:
            yaml_content = yaml.safe_load(file_content)
            if not isinstance(yaml_content, dict) or "services" not in yaml_content:
                raise ValueError(f"The file at {target_directory} is not a valid docker-compose file.")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing the YAML file at {target_directory}: {e}")

    def show_mods(self, mod_manager):
        self.login_window.destroy()
        self.mod_manager_window = tkinter.Tk()
        self.mod_manager_window.title("tModLoader Manager")

        # Create a canvas and a scrollbar
        canvas = tkinter.Canvas(self.mod_manager_window)
        scrollbar = tkinter.Scrollbar(self.mod_manager_window, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tkinter.Frame(canvas)
        
        # Update scroll region dynamically when new mods are loaded
        self.scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.installed_mods = get_installed_mods(mod_manager)
        self.enabled_mods = get_enabled_mods(mod_manager, self.target_directory)
        self.disabled_mods = get_disabled_mods(self.installed_mods, self.enabled_mods)
             
        finish_button = tkinter.Button(self.scrollable_frame, text= "Done", command=lambda: Window.modify_docker_compose_file(self, self.installed_mods, self.enabled_mods))
        finish_button.pack()

        for mod_object in self.installed_mods:
            workshop_name = mod_object.workshop_name
            internal_name = mod_object.internal_name

            mod_object.var = tkinter.BooleanVar(value=(internal_name in self.enabled_mods))
            mod_name = tkinter.StringVar(value=internal_name)
            checkbutton = tkinter.Checkbutton(self.scrollable_frame, text=workshop_name, variable=mod_object.var, command=lambda m = mod_name, ob = mod_object: self.on_checkbox_toggle(m, ob))
            checkbutton.pack(anchor="w")

            mod_object.checkbutton = checkbutton 

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.mod_manager_window.mainloop()

    def on_checkbox_toggle(self, mod_name, mod_object):
        name = mod_name.get()

        if mod_object.var.get():
            # If a mod is enabled, check its dependencies
            if mod_object.required_items:
                result = tkinter.messagebox.askyesno(
                    title="Prerequisites Found", 
                    message=f"The mod '{mod_object.workshop_name}' you have chosen requires the following mods to be enabled {', '.join(mod_object.required_items)} \n Would you like to activate them?"
                    )
   
                if result:
                    # Activate required mods if the user agrees
                    required_mod_objects = [mod for mod in self.installed_mods if mod.workshop_name in mod_object.required_items]
                    for required_mod in required_mod_objects:
                        if not required_mod.var.get():
                            required_mod.var.set(True)
                            required_mod.checkbutton.select()
                            self.enabled_mods.append(required_mod.internal_name)
                        if required_mod.internal_name in self.disabled_mods:
                            self.disabled_mods.remove(required_mod.internal_name)

                    if name not in self.enabled_mods:
                        self.enabled_mods.append(name)
                    if name in self.disabled_mods:     
                        self.disabled_mods.remove(name)

                if not result:
                    mod_object.var.set(False)
                    mod_object.checkbutton.deselect()

        else:
            if name not in self.disabled_mods:
                self.disabled_mods.append(name)
            if name in self.enabled_mods:
                self.enabled_mods.remove(name)

        self.mod_manager_window.update()
        self.mod_manager_window.update_idletasks()

    def modify_docker_compose_file(self, installed_mods, enabled_mods):
        self.mod_manager_window.destroy()
        enabled_mods_ids = []
        [enabled_mods_ids.append(x.workshop_id) for x in installed_mods if x.internal_name in enabled_mods]

        tmod_enabledmods = f"TMOD_ENABLEDMODS={','.join(enabled_mods_ids)}"

        sftp_client = self.mod_manager.create_sftp_client()

        # Fetch the existing docker-compose.yml file from the server
        current_directory = os.path.dirname(os.path.abspath(__file__))
        local_path = os.path.join(current_directory, "docker-compose.yml")
        remote_path = self.target_directory + "/test_docker-compose.yml"
        sftp_client.get(remote_path, local_path)

        # Update the docker-compose.yml file with enabled mods
        with open(local_path, "r+") as file:
            lines = file.readlines()
            file.seek(0)
            for line in lines:
                if "Enabled the" in line:
                    file.write(f"      # Enabled the {' ,'.join(enabled_mods)}\n")
                elif "TMOD_ENABLEDMODS=" in line:
                    file.write(f"      - '{tmod_enabledmods}'\n")
                else:
                    file.write(line)
            file.truncate()
        
        temp_remote_path = "/tmp/temp_upload_file"

        # Upload the modified docker-compose.yml back to the server
        sftp_client.put(local_path, temp_remote_path)

        sudo_command = f"sudo mv {temp_remote_path} {remote_path} && sudo chmod 644 {remote_path}"
        self.mod_manager.execute_ssh_command(sudo_command)
        self.mod_manager.close()

def get_installed_mods(client):
    file_paths = client.execute_ssh_command("find ./ -type f -name '*.tmod'")
    installed_mods_ids = re.findall(r".*/1281930/(.*)/20", file_paths)
    installed_mods = re.findall(r".*/(.*).tmod\n", file_paths)

    cleaned_mod_ids = []
    [cleaned_mod_ids.append(x) for x in installed_mods_ids if x not in cleaned_mod_ids]
    cleaned_mods = []
    [cleaned_mods.append(x) for x in installed_mods if x not in cleaned_mods]

    mod_list = []

    for workshop_id, internal_name in zip(cleaned_mod_ids, cleaned_mods):
        mod_list.append(ModInfo(workshop_id, internal_name))

    return mod_list 

def get_enabled_mods(client, target_directory):

    find_command = f"find {target_directory} -type f -name 'enabled.json'"
    enabled_json_path = client.execute_ssh_command(find_command).strip()

    if not enabled_json_path:
        raise FileNotFoundError("Could not find 'enabled.json' within the specified root directory.")
    
    file_content = client.execute_ssh_command(f"cat {enabled_json_path}")   

    enabled_mods = re.findall(r"\"(.+)\",?", file_content)
    
    cleaned_mods = []
    [cleaned_mods.append(x) for x in enabled_mods if x not in cleaned_mods]
    return cleaned_mods

def get_disabled_mods(installed, enabled):
    disabled_mods = []
    for mod in installed:
        if mod.internal_name not in enabled:
            disabled_mods.append(mod.internal_name)
    return sorted(disabled_mods)

def get_mod_name(id):  
    
    url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={id.strip()}"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        title_tag = soup.find("div", {"class": "workshopItemTitle"})
        
        if title_tag:
            return title_tag.text.strip()
        else:
            return "Title not found"
    else:
        return "Error fetching page"

def get_mod_requirements(id, processed_ids=None):

    if processed_ids is None:
        processed_ids = set()
    if id in processed_ids:
        return []

    processed_ids.add(id)
    required_items = []

    url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        required_items_section = soup.find("div", {"id": "RequiredItems"})

        if required_items_section:
            for item_link in required_items_section.find_all("a"):
                item_title_div = item_link.find("div", {"class": "requiredItem"})
                
                if item_title_div:
                    item_title = item_title_div.text.strip()
                    item_id = item_link["href"].split("id=")[-1]

                    sub_requirements = get_mod_requirements(item_id, processed_ids)

                    if item_title not in required_items:
                            required_items.append(item_title)

                    if sub_requirements:
                            for sub_item in sub_requirements:
                                if sub_item not in required_items:
                                    required_items.append(sub_item)

    return required_items

def main():
    client = Window()
    
if __name__ == "__main__":
    main()
