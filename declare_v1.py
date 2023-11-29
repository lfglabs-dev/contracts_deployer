import toml
import logging
from asyncio import run
from pathlib import Path
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.models.chains import StarknetChainId
from starknet_py.net.account.account import Account

# Set up logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

with open("config.toml", "r") as config_file:
    config = toml.load(config_file)

# Accessing variables
ADDRESS = config.get("ADDRESS")
PRIV_KEY = config.get("PRIV_KEY")
NODE_URL = config.get("NODE_URL")


async def main():
    key_pair = KeyPair.from_private_key(PRIV_KEY)

    account = Account(
        address=ADDRESS,
        client=FullNodeClient(node_url=NODE_URL),
        chain=StarknetChainId.TESTNET,
        key_pair=key_pair,
    )
    logger.info("ℹ️  Using account %s as deployer", hex(account.address))

    contract_file = Path("contracts/naming.json").read_text()
    declare_v1_tx = await account.sign_declare_transaction(
        compiled_contract=contract_file,
        max_fee=int(1e17),
    )

    resp = await account.client.declare(transaction=declare_v1_tx)
    logger.info(f"ℹ️ tx hash: {hex(resp.transaction_hash)}")
    await account.client.wait_for_tx(resp.transaction_hash)

    logger.info(f"✅ class hash: {hex(resp.class_hash)}")


if __name__ == "__main__":
    run(main())
