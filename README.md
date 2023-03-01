# Algorand Developer Workshop

## Acknowledgements
Thank you to [Joe Polny](https://github.com/joe-p) for the Docker image and GitPod setup.

## Getting Started
1. Make sure you have a [GitHub account](https://github.com/join).
1. Ensure you have [VS Code](https://code.visualstudio.com/).
    1. Install the `Remote - SSH` VS Code extension.
    1. Install the `GitPod` (not GitPod Remote) VS Code extension.
1. Log into [GitPod](https://www.gitpod.io/) by using your GitHub credentials.
    1. Choose VS Code **DESKTOP** as the default editor.
1. Enter [https://github.com/FinHubSA/AlgorandDevWorkshop](https://github.com/FinHubSA/AlgorandDevWorkshop) as the workshop to open in GitPod.
    1. Keep the default settings (VS Code desktop editor and standard class CPU).
    1. Set up an SSH key pair if none exists by following these [instructions](https://www.gitpod.io/docs/configure/user-settings/ssh#create-an-ssh-key).
    1. If you are asked what OS to use for the remote host, select Linux.
1. Once set up and VS Code has opened with the environment deployed, you may be asked to trust the authors of the files. Be sure to check the box that trusts the entire `workspace/` and select "Yes, I trust the authors".
    1. Run `python3 -m venv .venv` in the root directory (`workspace/AlgorandDeveloperWorkshop/`) to create a new virtual Python3 environment (select yes if popup detects new environment and asks to switch the interpreter).
    1. Run `source .venv/bin/activate` in the root directory to activate the virtual environment.
    1. Run `pip3 install -r requirements.txt` in the root directory to install all required dependencies.
    1. Run `./compile.sh` in the root directory to compile all Tealish programs in the `contracts/` directory. You will have to rerun this command every time you make changes to any of the contracts before testing.
    2. Do NOT cancel any of the running processes of any terminals opened by default. This includes exiting the terminal itself (don't do it).

run `pytest` to test the contracts. If they all succeed, you're ready to go!