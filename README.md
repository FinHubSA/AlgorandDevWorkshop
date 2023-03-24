# Algorand Developer Workshop

## Acknowledgements
Thank you to [Joe Polny](https://github.com/joe-p) for the Docker image and GitPod setup.

## Getting Started
1. Make sure you have a [GitHub account](https://github.com/join).
2. Log into [GitPod](https://www.gitpod.io/) by using your GitHub credentials.
    1. Choose VS Code **BROWSER** as the default editor.
3. Enter [https://github.com/FinHubSA/AlgorandDevWorkshop](https://github.com/FinHubSA/AlgorandDevWorkshop) as the workshop to open in GitPod.
    1. Keep the default settings (VS Code browser editor and standard class CPU).

### Notes
*  Do NOT stop the Algorand Indexer process running in a terminal tab unless you know what you're doing.
*  Do not delete `.venv` unless you know what you're doing.
*  While this GitPod setup is great to get into smart contract development quickly, it is recommended that you set up a local environment on your computer for prolonged learning. Take a look at the [Sandbox](https://github.com/algorand/sandbox).

## Testing
1. Compile your Tealish smart contracts in the `contracts` folder by running `tealish compile contracts` in the project root directory.
2. Run `pytest` in the project root directory to run all the tests in the `tests` folder.
