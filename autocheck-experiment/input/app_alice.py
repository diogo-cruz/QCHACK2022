import random
import logging

from netqasm.logging.glob import get_netqasm_logger
from netqasm.sdk.external import NetQASMConnection, Socket

from epr_socket import DerivedEPRSocket as EPRSocket

logger = get_netqasm_logger()

# fileHandler = logging.FileHandler("logfile_alice.log")
# logger.setLevel(logging.INFO)
# logger.addHandler(fileHandler)


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
        # IMPLEMENT YOUR SOLUTION HERE
        # logger.info("IMPLEMENT YOUR SOLUTION HERE - ALICE")

        n = 0
        bases = []
        key = []
        while n < key_length:
            # Create an entangled pair using the EPR socket to bob
            q_ent = epr_socket.create_keep()[0]
            q_ent.Z()

            # Choose basis randomly
            basis = random.randint(0, 1)
            bases.append(basis)
            if basis:
                q_ent.H()

            # Measure the qubit
            m_alice = q_ent.measure()
            alice.flush()
            m_alice = int(m_alice)

            # Send the outcome to bob
            socket.send(str(basis))

            # Receive the outcome from bob
            accept_bit = socket.recv()
            alice.flush()

            if accept_bit == "Y":
                key.append(m_alice)
                n += 1
            else:
                pass

    # logger.info("ALICE BASES: {}".format(bases))
    # logger.info("ALICE KEY: {}".format(key))

    # RETURN THE SECRET KEY HERE
    return {
        "secret_key": key,
    }


if __name__ == "__main__":
    main()
