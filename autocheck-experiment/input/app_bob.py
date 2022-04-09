import random
import logging

from netqasm.logging.glob import get_netqasm_logger
from netqasm.sdk.external import NetQASMConnection, Socket

from epr_socket import DerivedEPRSocket as EPRSocket

logger = get_netqasm_logger()

# fileHandler = logging.FileHandler("logfile_bob.log")
# logger.setLevel(logging.INFO)
# logger.addHandler(fileHandler)


def main(app_config=None, key_length=16):
    # Socket for classical communication
    socket = Socket("bob", "alice", log_config=app_config.log_config)
    # Socket for EPR generation
    epr_socket = EPRSocket("alice")

    bob = NetQASMConnection(
        app_name=app_config.app_name,
        log_config=app_config.log_config,
        epr_sockets=[epr_socket],
    )

    with bob:
        # IMPLEMENT YOUR SOLUTION HERE
        #logger.info("IMPLEMENT YOUR SOLUTION HERE - BOB")

        n = 0
        bases = []
        key = []
        while n < key_length:
            # Receive an entangled pair using the EPR socket to alice
            q_ent = epr_socket.recv_keep()[0]
            bob.flush()
            q_ent.X()

            # Choose basis randomly
            basis = random.randint(0, 1)
            bases.append(basis)
            if basis:
                q_ent.H()

            # Measure the qubit
            m_bob = q_ent.measure()
            bob.flush()
            m_bob = int(m_bob)
            
            if m_bob == 1:
                m_bob_corr = 0
            else:
                m_bob_corr = 1

            # Receive the outcome from alice
            basis_alice = socket.recv()
            bob.flush()
            basis_alice = int(basis_alice)

            if basis_alice == basis:
                accept_bit = 'Y'
                #assert m_bob_corr == m_alice, "Bits should be equal!"
                key.append(m_bob_corr)
                n += 1
            else:
                accept_bit = 'N'

            # Send the outcome to alice
            socket.send(accept_bit)

    # logger.info("BOB BASES: {}".format(bases))
    # logger.info("BOB KEY: {}".format(key))

    # RETURN THE SECRET KEY HERE
    return {
        "secret_key": key,
    }


if __name__ == "__main__":
    main()
