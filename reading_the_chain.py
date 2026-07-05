import random
import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.providers.rpc import HTTPProvider


# If you use one of the suggested infrastructure providers, the url will be of the form
# now_url  = f"https://eth.nownodes.io/{now_token}"
# alchemy_url = f"https://eth-mainnet.alchemyapi.io/v2/{alchemy_token}"
# infura_url = f"https://mainnet.infura.io/v3/{infura_token}"

def connect_to_eth():
  url = "https://eth-mainnet.g.alchemy.com/v2/_iHyNkK24W2Na_hbKuoyk"  
  w3 = Web3(HTTPProvider(url))
  assert w3.is_connected(), f"Failed to connect to provider at {url}"
  return w3

def connect_with_middleware(contract_json):
  with open(contract_json, "r") as f:
    d = json.load(f)
    d = d['bsc']
    address = d['address']
    abi = d['abi']

  url = "https://bnb-testnet.g.alchemy.com/v2/7WIYsxR8on_bP-1YuFskn"
  w3 = Web3(HTTPProvider(url))
  assert w3.is_connected(), f"Failed to connect to provider at {url}"

  w3.middleware_onion.inject(ExtraDataToPOAMiddleware,layer = 0)
  
  contract = w3.eth.contract(
    address=address,
    abi=abi
  )

  return w3, contract

def is_ordered_block(w3, block_num):

  block = w3.eth.get_block(block_num, full_transactions=True)
  ordered = False

  base_fee = block.get("baseFeePerGas",0)
  fees = []

  transactions = block["transactions"]

  if all(["gasPrice" in tx for tx in transactions]):

    for tx in transactions:
      fee = tx["gasPrice"]
      fees.append(fee)
  
  else:
    
    for tx in transactions:

    # Case 2: After EIP-1559, Type 2
    # If a transaction has maxPriorityFeePerGas and maxFeePerGas
    # We should use EIP-1559 formula and ignore gasPrice

      if "maxPriorityFeePerGas" in tx and "maxFeePerGas" in tx:
        priority_fee = min(
          tx["maxPriorityFeePerGas"],
          tx["maxFeePerGas"] - base_fee
        )

        # Total fee paid per gas for type 2 transaction
        fee = priority_fee + base_fee


      # Type 0
      # Use gasPrice directly

      elif "gasPrice" in tx:
        fee = tx["gasPrice"]
    
      else:
        fee = 0
    
      fees.append(fee)

  if fees == sorted (fees, reverse = True):
        ordered = True

  return ordered


def get_contract_values(contract, admin_address, owner_address):

  default_admin_role = int.to_bytes(0, 32, byteorder="big")


  # Get and return the merkleRoot from the provided contract
  onchain_root = contract.functions.merkleRoot().call()

  # Check the contract to see if the address "admin_address" has the role "default_admin_role"
  has_role = contract.functions.hasRole(
    default_admin_role,
    admin_address
  ).call()

    # Call the contract to get the prime owned by "owner_address"
  prime = contract.functions.getPrimeByOwner(owner_address).call()

  return onchain_root, has_role, prime


"""
    This might be useful for testing (main is not run by the grader feel free to change 
    this code anyway that is helpful)
"""
if __name__ == "__main__":
    # These are addresses associated with the Merkle contract (check on contract
    # functions and transactions on the block explorer at
    # https://testnet.bscscan.com/address/0xaA7CAaDA823300D18D3c43f65569a47e78220073
    admin_address = "0xAC55e7d73A792fE1A9e051BDF4A010c33962809A"
    owner_address = "0x793A37a85964D96ACD6368777c7C7050F05b11dE"
    contract_file = "contract_info.json"

    eth_w3 = connect_to_eth()
    cont_w3, contract = connect_with_middleware(contract_file)

    latest_block = eth_w3.eth.get_block_number()
    london_hard_fork_block_num = 12965000
    assert latest_block > london_hard_fork_block_num, f"Error: the chain never got past the London Hard Fork"

    n = 5
    for _ in range(n):
        block_num = random.randint(1, latest_block)
        ordered = is_ordered_block(block_num)
        if ordered:
            print(f"Block {block_num} is ordered")
        else:
            print(f"Block {block_num} is not ordered")
