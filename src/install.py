import os
import subprocess
from colorama import Fore
from config import print_stuff, config
from shared import ask_yes_no, process_command, run_command, set_var, finish_node

# Setup print stuff from config class print_stuff
print_whitespace = print_stuff.printWhitespace
print_stars = print_stuff().printStars
string_stars = print_stuff().stringStars
print_stars_reset = print_stuff(reset=1).printStars
string_stars_reset = print_stuff(reset=1).stringStars


def install_check() -> None:
    print_stars()
    if (
        os.path.isdir(config.serv_dir)
        and os.path.isdir(config.serv_config_dir)
        and os.path.isfile(config.serv_conf)
        and os.path.isdir(config.toolbox_location)
    ):
        # Already installed, return and run main app
        return
    else:
        # Not installed! Let's install it!
        print(f"* SERV Node is not installed at {config.serv_dir}")
        answer = ask_yes_no("* Would you like to install SERV Node now? (y/n)")
        if answer:
            # Install SERV Node
            print_stars()
            print("* Installing SERV Node")
            print_stars()
            install_serv_node()
            print(Fore.MAGENTA)
        else:
            print_stars()
            print("* Exiting SERV Node Installer")


def install_serv_node() -> None:
    if not os.path.isdir(config.serv_dir):
        os.makedirs(config.serv_dir)
        process_command(f"wget -O {config.servnode} rpc.serv.services/servnode")
        process_command(f"wget -O /tmp/genesis.json rpc.serv.services/genesis")
        process_command(f"wget -O /tmp/config.toml rpc.serv.services/config")
        process_command(f"chmod +x {config.servnode}")
        print(f"* Created {config.serv_dir} directory & files")
        # open genesis.json and config.toml to read & update
        short_name = input(
            f"* Pick a short name to identify your validator node (Example: SuperNode): "
        )
        if short_name:
            answer = ask_yes_no(
                f"* You picked {short_name} as your validator short code name, is this correct? (y/n)"
            )
            if answer:
                # Open file
                with open("/tmp/config.toml", "r") as file:
                    filedata = file.read()
                # Update settings
                filedata = filedata.replace(
                    'moniker = "Serv-0"', f'moniker = "{short_name}"'
                )
                filedata = filedata.replace('log_level = "info"', 'log_level = "warn"')
                # Save file
                with open("/tmp/config.toml", "w") as file:
                    file.write(filedata)
                # Init network
                process_command(
                    f"{config.servnode} init {short_name} --chain-id serv_43970-1"
                )
                # Move custom files
                process_command(f"mv /tmp/genesis.json {config.serv_genesis}")
                process_command(f"mv /tmp/config.toml {config.serv_conf}")
                # Update chain-id
                with open(config.serv_client, "r") as file:
                    filedata = file.read()
                filedata = filedata.replace(
                    'chain-id = ""', 'chain-id = "serv_43970-1"'
                )
        print(f"* SERV Node installed at {config.serv_dir}")
        print_stars()
        # Wallet Creation or Import
        print("* Creating/Importing SERV wallet")
        answer = ask_yes_no(
            f"* Would you like to create a wallet for your validator node? (y/n)"
        )
        if answer:
            print(Fore.WHITE)
            address, mnemonic = run_command(f"{config.servnode} keys add {config.active_user}")
            set_var(config.dotenv_file, "SERV_ADDRESS", address)
            with open(config.serv_mnemonic, "w") as file:
                    file.write(mnemonic)
            print("* We saved a copy of your mnemonic phrase at ~/.serv/config/mnemonic.txt")
            input(f"{Fore.YELLOW}* Backup your mnemonic phrase and press enter to continue. Do not give your phrase away or lose it!{Fore.MAGENTA}")
        else:            
            answer = ask_yes_no(f"* Skipping wallet creation, would you like to import a wallet now instead? (y/n)")
            if answer:
                address, mnemonic = run_command(
                    f'{config.servnode} keys add {config.active_user} --recover --algo="eth_secp256k1"'
                )
                set_var(config.dotenv_file, "SERV_ADDRESS", address)
            else:
                finish_node()
        # Service Configuration Stuff
        with open(config.servnode_service_file, "r") as file:
            filedata = file.read()
        filedata = filedata.replace("User=servuser", f"User={config.active_user}")
        filedata = filedata.replace(
            "WorkingDirectory=/home/servuser/serv",
            f"WorkingDirectory={config.serv_dir}",
        )
        filedata = filedata.replace(
            "ExecStart=/home/servuser/serv/servnode start",
            f"ExecStart={config.servnode} start",
        )
        # Save file in /tmp as we need to be sudo to move it to /etc/systemd/system
        with open("/tmp/servnode.service", "w") as file:
            file.write(filedata)
        # Move file to /etc/systemd/system
        subprocess.run(
            f"sudo mv /tmp/servnode.service /etc/systemd/system/servnode.service",
            shell=True,
            check=True,
        )
        # Enable service
        subprocess.run("sudo systemctl enable servnode.service", shell=True, check=True)
        # Start service
        subprocess.run("sudo systemctl start servnode.service", shell=True, check=True)
    else:
        print(f"* {config.serv_dir} directory already exists, skipping!")
