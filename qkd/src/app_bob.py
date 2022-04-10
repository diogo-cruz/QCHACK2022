import random
import os

from netqasm.logging.glob import get_netqasm_logger
from netqasm.sdk.external import NetQASMConnection, Socket

from epr_socket import DerivedEPRSocket as EPRSocket

# Output prints are stored in output.txt:
output_path = os.getcwd() + "/output.txt"
f = open(output_path, 'a')

########################
### INPUT PARAMETERS ###
########################

test_probability   = 0.5  # Fraction of shared bits that are tested. If the value is too low
                           # some runs will results in no tested bits, and the key gets rejected.
                           # If the value is too high many tests will be done, leading to a better
                           # estimate of Eve's presence but requiring more shared entangled pairs
                           # to reach the final private key.
                           
mismatch_threshold = 0.14  # Allowed fraction of mismatches bewteen bits (above this, no secure key is generated). 

info_recon         = True  # Set False to disable information reconciliation step

########################
#### AUX FUNCTIONS #####
########################

def flip(p):
    # Biased coin - probability of 0 is 1-p and probability of 1 is p
    if random.random() < p:
        return 1
    else: 
        return 0

def get_shuffle(n):
    mylist = [i for i in range(n)]
    random.shuffle(mylist)
    return mylist

def get_shuffled_key(key, shuffle):
    # the i-th position of the suffled key is the shuffle[i]-th position of the key
    shuffled_key = [key[s] for s in shuffle]
    return shuffled_key

def get_inv_shuffled_key(inv_key, shuffle):
    inversion = [[i, shuffle[i]] for i in range(len(shuffle))]
    def take_second(elem):
        return elem[1]
    inversion.sort(key = take_second)
    new_shuffle = [x[0] for x in inversion]
    key = get_shuffled_key(inv_key, new_shuffle)
    return key

def get_parity(block):
    s = sum(block)
    parity = s % 2
    return parity

def get_blocks(key, k):
    # split key into blocks of size k
    blocks = []
    i = 0
    while i*k < len(key):
        blocks.append(key[i*k : i*k + k])
        i += 1
    return blocks

def binaryB(endnode, socket, block, idx = 0):
    # assuming there is an odd error parity, does binary search for one wrong bit
    
    n = len(block)
    
    if n == 1:
        return idx
    
    else:
        block_left  = block[:n//2]

        #determine parity of block
        parity = get_parity(block_left)

        #send parity to Alice and ask her to confirm if matches
        socket.send(str(parity))

        #receive answer from Alice
        same_parity = socket.recv()
        endnode.flush()

        #if left parities don't match, keep looking in the left side
        if same_parity == 'N':
            return binaryB(endnode, socket, block_left, idx)

        #if left parities match, there is a correction to be made on the right side
        if same_parity == 'Y':
            block_right = block[n//2:]
            new_idx = idx + n // 2
            return binaryB(endnode, socket, block_right, new_idx)


### Block schedule for cascade information reconciliation protocol ###

# Estimate quantum bit error rate
QBER = 0.1

def get_block_schedule(Q):
    ks = [0.73 / Q]
    for i in range(3):
        ks.append(ks[-1] * 2)
    ks_int = [int(k) for k in ks]
    return ks_int

# Size of blocks over the various cascade iterations
block_schedule = get_block_schedule(QBER)


########################
#### MAIN FUNCTION #####
########################

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
                test = flip(test_probability) # whether they test this bit

                if test:
                    accept_bit = str(m_bob_corr) #for alice to compare with hers
                else:
                    accept_bit = 'Y' #tells alice to accept
                    key.append(m_bob_corr)
                    n += 1
            else:
                accept_bit = 'N' #tells alice to reject

            # Send the outcome to alice
            socket.send(accept_bit)

            if accept_bit == '0' or accept_bit == '1':
                #Receive result of test from alice
                test_result = socket.recv()
                bob.flush()
                matches.append(int(test_result))

    # Some progress prints are done on Alice's side
    if len(matches) > 0:
        mismatch_fraction = 1 - sum(matches) / len(matches)
            
    else:
        mismatch_fraction = 1
    
    # RETURN THE SECRET KEY HERE
    if mismatch_fraction > mismatch_threshold:
        return {
        "secret_key": None,
        }
    else:  

        if info_recon:

            ###################################################
            ### Cascade Information Reconciliation Protocol ###
            ###################################################
            
            # Assume that Alice has the 'correct' key and Bob has the noisy one

            recon_key = key #reconciliated key

            for iteration, block_size in enumerate(block_schedule):

                # We shuffle the  keys in every iteration except the first
                if iteration == 0:
                    shuffle = [i for i in range(key_length)]

                if iteration >= 1:
                    shuffle = get_shuffle(key_length)

                    # send shuffle to Alice
                    # (the shuffle can be public as it reveals no info about the keys)
                    for shuffle_bit in shuffle:
                        socket.send(str(shuffle_bit))

                shuffled_key = get_shuffled_key(recon_key, shuffle)
                #split into blocks and test parity of each
                blocks   = get_blocks(shuffled_key, block_size)
                parities = [get_parity(block) for block in blocks]

                for parity, block in zip(parities, blocks):

                    #send parity to Alice and ask her to confirm if matches
                    socket.send(str(parity))

                    #receive answer from Alice
                    parity_bit = socket.recv()
                    bob.flush()

                    if parity_bit == 'N': # if there is a parity mismatch Bob does an error correction
                        error_idx = binaryB(bob, socket, block)
                        block[error_idx] = abs(block[error_idx]-1) #flip this bit

                recon_key_shuffled = [item for sublist in blocks for item in sublist] #flatten list of blocks
                recon_key = get_inv_shuffled_key(recon_key_shuffled, shuffle)

            return {
                "secret_key": recon_key,
            }
        
        else:
            return {
                "secret_key": key,
            }


if __name__ == "__main__":
    main()
