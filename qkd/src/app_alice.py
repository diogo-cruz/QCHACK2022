import random
import os

from netqasm.logging.glob import get_netqasm_logger
from netqasm.sdk.external import NetQASMConnection, Socket

from epr_socket import DerivedEPRSocket as EPRSocket

# Output prints are stored in output.txt:
output_path = os.getcwd() + "/output.txt"
f = open(output_path, 'w')

########################
### INPUT PARAMETERS ###
########################

#test_probability -> Set by Bob

mismatch_threshold = 0.14  # Allowed fraction of mismatches bewteen bits (above this, no secure key is generated) 

info_recon         = True  # Set False to disable information reconciliation step


########################
#### AUX FUNCTIONS #####
########################


def flip(p):  # Decides if shared pair is going to be tested for errors
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

def binaryA(endnode, socket, block, idx = 0):
    # assuming there is an odd error parity, does binary search for one wrong bit
        
    n = len(block) 
        
    if n == 1:
        return 'finish'
    
    else:
        block_left  = block[:n//2]

        #determine parity of block
        parity = get_parity(block_left)

        #receive Bob's parity
        bobs_parity = int(socket.recv())
        endnode.flush()

        #determine if parities match
        if parity == bobs_parity:
            same_parity = 'Y'
        elif parity != bobs_parity:
            same_parity = 'N'

        #send answer to Bob
        socket.send(same_parity)

        #if left parities don't match, keep looking in the left side
        if same_parity == 'N':
            return binaryA(endnode, socket, block_left, idx)

        #if left parities match, there is a correction to be made on the right side
        if same_parity == 'Y':
            block_right = block[n//2:]
            new_idx = idx + n // 2
            return binaryA(endnode, socket, block_right, new_idx)


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
    socket = Socket("alice", "bob", log_config=app_config.log_config)
    # Socket for EPR generation
    epr_socket = EPRSocket("bob")

    alice = NetQASMConnection(
        app_name=app_config.app_name,
        log_config=app_config.log_config,
        epr_sockets=[epr_socket],
    )

    with alice:

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

            # Send the basis to bob
            socket.send(str(basis))

            # Receive the outcome from bob
            accept_bit = socket.recv() #can be 'Y' (to accept), 'N' (to reject) or '0'/'1' (to test)
            alice.flush()

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

    if len(matches) > 0:
        mismatch_fraction = 1 - sum(matches) / len(matches)
        print("Mismatch fraction: "+str(mismatch_fraction), file = f)
        if mismatch_fraction > mismatch_threshold:
            print("Above mismatch threshold of "+str(mismatch_threshold), file=f)
            print("Probably Eve, key rejected.", file=f)
        else:
            print("Below mismatch threshold of "+str(mismatch_threshold), file=f)
            print("Key accepted, testing now for noise.", file=f)
    else:
        mismatch_fraction = 1
        print("No matches were tested! Key will be rejected. Try increasing test_probability on Bob's side.", file=f)
    
    # RETURN THE SECRET KEY HERE
    if mismatch_fraction > mismatch_threshold:
        return {
        "secret_key": None,
        }
    else:   
        if info_recon:

            print("\nStarting CASCADE:\n", file=f)
            
            ###################################################
            ### Cascade Information Reconciliation Protocol ###
            ###################################################
            
            # Assume that Alice has the 'correct' key and Bob has the noisy one

            for iteration, block_size in enumerate(block_schedule):
                print("- Iteration "+str(iteration)+" -", file=f)
                # We shuffle the  keys in every iteration except the first
                if iteration == 0:
                    shuffle = [i for i in range(key_length)]

                if iteration >= 1:
                    # receive random shuffle from Bob
                    # (the shuffle can be public as it reveals no info about the keys)
                    shuffle = []
                    for i in range(key_length):
                        shuffle_bit = int(socket.recv())
                        alice.flush()
                        shuffle.append(shuffle_bit)

                shuffled_key = get_shuffled_key(key, shuffle)
                #split into blocks and test parity of each
                blocks   = get_blocks(shuffled_key, block_size)
                parities = [get_parity(block) for block in blocks]

                for parity, block in zip(parities, blocks):

                    #receive Bob's parity
                    bobs_parity = int(socket.recv())
                    alice.flush()

                    #determine if parities match
                    if parity == bobs_parity:
                        parity_bit = 'Y'
                    elif parity != bobs_parity:
                        parity_bit = 'N'
                        print("Found parity error!", file=f)

                    #send answer to Bob
                    socket.send(parity_bit)
                    if parity_bit == 'N':
                        state = binaryA(alice, socket, block) 

        return {
            "secret_key": key,
        }


if __name__ == "__main__":
    main()
