import toml
import logging
from asyncio import run
from pathlib import Path
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.models.chains import StarknetChainId
from starknet_py.net.account.account import Account
from starknet_py.common import create_casm_class, create_sierra_compiled_contract
from starknet_py.hash.casm_class_hash import compute_casm_class_hash
from starknet_py.hash.sierra_class_hash import compute_sierra_class_hash

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
NAME = "identity_Identity"
CASM_FILE = "contracts/identity_Identity.compiled_contract_class.json"
SIERRA_FILE = "contracts/identity_Identity.contract_class.json"


async def main():
    key_pair = KeyPair.from_private_key(PRIV_KEY)
    client = FullNodeClient(node_url=NODE_URL)
    account = Account(
        address=ADDRESS,
        client=client,
        chain=StarknetChainId.TESTNET,
        key_pair=key_pair,
    )
    logger.info("ℹ️  Using account %s as deployer", hex(account.address))

    contract_compiled_casm = Path(CASM_FILE).read_text()
    casm_class = create_casm_class(contract_compiled_casm)
    casm_class_hash = compute_casm_class_hash(casm_class)

    contract_compiled_sierra = Path(SIERRA_FILE).read_text()
    sierra_class = create_sierra_compiled_contract(contract_compiled_sierra)
    sierra_class_hash = compute_sierra_class_hash(sierra_class)

    try:
        await client.get_class_by_hash(class_hash=sierra_class_hash)
        logger.info(f"✅ Class {hex(sierra_class_hash)} already declared, skipping")
        return sierra_class_hash
    except Exception:
        pass

    declare_v2_tx = await account.sign_declare_v2_transaction(
        compiled_contract=contract_compiled_sierra,
        compiled_class_hash=casm_class_hash,
        max_fee=int(1e17),
    )

    resp = await account.client.declare(transaction=declare_v2_tx)
    logger.info(f"ℹ️ tx hash: {hex(resp.transaction_hash)}")
    await account.client.wait_for_tx(resp.transaction_hash)

    logger.info(f"✅ class hash: {hex(resp.class_hash)}")


if __name__ == "__main__":
    run(main())
