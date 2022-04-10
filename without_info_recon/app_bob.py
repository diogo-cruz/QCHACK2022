import random
import logging

from netqasm.logging.glob import get_netqasm_logger
from netqasm.sdk.external import NetQASMConnection, Socket

from epr_socket import DerivedEPRSocket as EPRSocket

#f = open('/home/duarte/projects/QuTech/QCHACK2022/bob.txt', 'a')

logger = get_netqasm_logger("bob")

# fileHandler = logging.FileHandler("logfile_bob.log")
# logger.setLevel(logging.INFO)
# logger.addHandler(fileHandler)

test_probability   = 0.5    # fraction of shared bits that are tested 
mismatch_threshold = 0.14  # allowed fraction of mismatches bewteen bits (above this, no secure key is generated) 

def flip(p):
    # Biased coin - probability of 0 is 1-p and probability of 1 is p
    if random.random() < p:
        return 1
    else: 
        return 0

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
        logger.info("IMPLEMENT YOUR SOLUTION HERE - BOB")

        n = 0
        bases = []
        key = []
        matches = []
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
                #assert m_bob_corr == m_alice, "Bits should be equal!"
                test = flip(test_probability) # whether they test this bit
                
                #print(test, file = f)

                if test:
                    accept_bit = str(m_bob_corr) #for alice to compare with hers
                else:
                    accept_bit = 'Y' #tells alice to accept
                    key.append(m_bob_corr)
                    n += 1
            else:
                accept_bit = 'N' #tells alice to reject

            logger.info("B0")

            # Send the outcome to alice
            socket.send(accept_bit)

            logger.info("B1")

            if accept_bit == '0' or accept_bit == '1':
                #Receive result of test
                test_result = socket.recv()
                bob.flush()
                matches.append(int(test_result))

    logger.info("BOB BASES: {}".format(bases))
    logger.info("BOB KEY: {}".format(key))

    mismatch_fraction = 1 - sum(matches) / len(matches)

    logger.info("BOB FRACTION: {}".format(mismatch_fraction))

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
