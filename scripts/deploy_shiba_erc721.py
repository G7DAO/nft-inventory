from brownie import ShibaERC721, accounts, network, config

def main():
    dev = accounts.load('deployment_account')

    shiba = ShibaERC721.deploy(
        {"from": dev},
        publish_source=True
    )
    return shiba
