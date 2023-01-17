# mint 1 shiba nft using brownie with the smart contract

from brownie import ShibaERC721, accounts, network

def main():
    dev = accounts.load('deployment_account')
    print(network.show_active())
    shiba_nft = ShibaERC721[len(ShibaERC721) - 1]
    shiba_nft.tokenCounter()
    transaction = shiba_nft.safeMint("0xa2F5785506b0344abFD15EEFc4BDe21D4cD3125b", "https://gateway.pinata.cloud/ipfs/QmTVkd2oDF5Wnf8ZTntvyU5izfjbfvLPbnWDtjsAvfY1y3", {"from": dev})
    transaction.wait(1)
    # show the nft on polygon mumbai scan
    print("https://mumbai.polygonscan.com/tx/" + transaction.txid)
