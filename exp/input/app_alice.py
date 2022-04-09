from netqasm.logging.glob import get_netqasm_logger
from netqasm.sdk.external import NetQASMConnection, Socket

from epr_socket import DerivedEPRSocket as EPRSocket

logger = get_netqasm_logger()


def main(app_config=None, key_length=16):
    # Socket for classical communication
    socket = Socket("alice", "bob", log_config=app_config.log_config)
    # Socket for EPR generation
    epr_socket = EPRSocket("bob")

    alice = NetQASMConnection(
        app_name=app_config.app_name,
        log_config=app_config.log_config,
        epr_sockets=[epr_socket],
    )

    with alice:
        # Create an entangled pair using the EPR socket to bob
        q_ent = epr_socket.create()[0]
        # Measure the qubit
        m = q_ent.measure()
    # Print the outcome
    print(f"alice's outcome is: {m}")

    # RETURN THE SECRET KEY HERE
    return {
        "secret_key": None,
    }


if __name__ == "__main__":
    main()
