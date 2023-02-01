# mint 1 shiba nft using brownie with the smart contract

from brownie import ShibaERC721, accounts, network

def main():
    dev = accounts.load('deployment_account')
    print(network.show_active())
    shiba_nft = ShibaERC721[len(ShibaERC721) - 1]
    transaction = shiba_nft.safeMint("ADDRESS_HERE", "URI_HERE", {"from": dev})
    transaction.wait(1)
    # show the nft on polygon mumbai scan, var env $POLYGONSCAN_TOKEN required
    print("https://mumbai.polygonscan.com/tx/" + transaction.txid)
