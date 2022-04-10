import random
import logging

from netqasm.logging.glob import get_netqasm_logger
from netqasm.sdk.external import NetQASMConnection, Socket

from epr_socket import DerivedEPRSocket as EPRSocket

#f = open('/home/duarte/projects/QuTech/QCHACK2022/alice.txt', 'a')

logger = get_netqasm_logger("alice")

# fileHandler = logging.FileHandler("logfile_alice.log")
# logger.setLevel(logging.INFO)
# logger.addHandler(fileHandler)

#test_probability   = 0.5    # fraction of shared bits that are tested 
mismatch_threshold = 0.14  # allowed fraction of mismatches bewteen bits (above this, no secure key is generated) 

def flip(p):
    # Biased coin - probability of 0 is 1-p and probability of 1 is p
    if random.random() < p:
        return 1
    else: 
        return 0

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
        logger.info("IMPLEMENT YOUR SOLUTION HERE - ALICE")

        n = 0
        bases = []
        key = []
        matches = []
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

            logger.info("A0")

            # Receive the outcome from bob
            accept_bit = socket.recv() #can be 'Y' (to accept), 'N' (to reject) or '0'/'1' (to test)
            alice.flush()

            logger.info("A1")

            if accept_bit == "Y":
                key.append(m_alice)
                n += 1
            elif accept_bit == "N":
                pass
            else: #test if there is a mismatch
                if m_alice == int(accept_bit):
                    test_result = 1
                else:
                    test_result = 0
                matches.append(test_result)

                #send result of test to bob
                socket.send(str(test_result))

    logger.info("ALICE BASES: {}".format(bases))
    logger.info("ALICE KEY: {}".format(key))

    mismatch_fraction = 1 - sum(matches) / len(matches)

    logger.info("ALICE FRACTION: {}".format(mismatch_fraction))

    # RETURN THE SECRET KEY HERE
    if mismatch_fraction > mismatch_threshold:
        return {
        "secret_key": None,
        }
    else:   
        return {
            "secret_key": key,
        }


if __name__ == "__main__":
    main()
