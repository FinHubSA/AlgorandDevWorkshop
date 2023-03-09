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

### Notes
* You must enter the virtual environment created for you by running `source .venv/bin/activate` every time you open a new terminal tab. The default "dev" tab is already within the virtual environment.
*  Do NOT cancel the running processes of any terminals opened by defaul unless you know what you're doing.
*  Do not delete `.venv` unless you know what you're doing.

## Testing
1. Compile your Tealish smart contracts in the `contracts` folder by running `tealish compile contracts` in the project root directory.
2. Run `pytest` to run the tests in the `tests` folder.