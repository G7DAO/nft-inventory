# contracts

Main repo for Game7 contracts

## Setup

### Using Python and [eth-brownie](https://github.com/eth-brownie/brownie)

First, set up a Python3 environment:

- Check if you have Python3 installed on your system: `python3 --version`.
- If the above command errors out, you need to install Python3. You can find instructions for how to
do this at https://python.org.
- Create a Python virtual environment in the root of this directory: `python3 -m venv .game7`
- Activate the virtual environment: `source .game7/bin/activate` (when you are finished working in this
code base, you can deactivate the virtual environment using the `deactivate` command).
- Install the `game7ctl` package: `pip install -e game7ctl/`

Following these steps will make the `game7ctl` command available in your shell. You can use this command-line
tool to deploy and interact with the smart contracts in this repository. For more details:

```
game7ctl --help
```

#### Development

To set up a *development* environment, you have to also install the developer dependencies using:

```
pip install -e "game7ctl/[dev]"
```

You can run Python tests by invoking:

```
bash game7ctl/test.sh
```
