# Algorand Developer Workshop

## About
A set of Tealish smart contracts and corresponding tests intended for the FinHub Workshop Series.

## Getting Started
1. Make sure you have a [GitHub account](https://github.com/join).
2. Log into [GitPod](https://www.gitpod.io/) by using your GitHub credentials.
    1. Choose VS Code **BROWSER** as the default editor.
    2. If it pops up, fill out the "Tell us more about you" form.
3. On the dashboard, click the "New Workspace" button and copy/paste [https://github.com/FinHubSA/AlgorandDevWorkshop](https://github.com/FinHubSA/AlgorandDevWorkshop) as the Context URL.
    1. Keep the default settings (VS Code browser editor and standard class CPU).
 4. Wait for the workspace to be set up.
    1. You may safely close all the welcome panels.
 5. There is a `tealish-0.0.1.vsix` VS Code extension in the project root - install it by right clicking it on the file explorer to the left of the editor and selecting "Install Extension VSIX".

### Notes
*  Do not stop the Algorand Indexer process running in a terminal tab unless you know what you're doing.
*  Do not delete `.venv` unless you know what you're doing.
*  While this GitPod setup is great to get into smart contract development quickly, it is recommended that you set up a local environment on your computer for prolonged learning. Take a look at the [Sandbox](https://github.com/algorand/sandbox) or, alternatively, [AlgoKit](https://github.com/algorandfoundation/algokit-cli).

## Testing
1. Compile your Tealish smart contracts in the `contracts` folder by running `tealish compile contracts` in the terminal at the project root directory (`/workspace/AlgorandDevWorkshop`).
2. Run `pytest` in the project root directory to run all the tests in the `tests` folder.

## Acknowledgements
Thank you to [Joe Polny](https://github.com/joe-p) for the Docker image and GitPod setup.