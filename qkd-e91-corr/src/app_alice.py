from netqasm.logging.glob import get_netqasm_logger
from netqasm.sdk.external import NetQASMConnection, Socket

from epr_socket import DerivedEPRSocket as EPRSocket

logger = get_netqasm_logger()

############### Added myself

from math import pi
import random
from fractions import Fraction
from collections import defaultdict
#f = open('/home/sagar/Projects/hackathons/qchack/2022/QCHACK2022/alice.txt', 'a')
f = open('/home/oscar/QCHACK2022/alice.txt', 'a')
from numpy import sqrt

class Basis:
    def __init__(self, a, b=1):
        fraction = Fraction(a, b)
        self.fraction = fraction
        self.theta = (fraction * pi) if a >=0 else (2*pi - fraction * pi)
        self.id = str(self.fraction.as_integer_ratio())

    def rotate(self, qubit):
        qubit.rot_Z(0, 0, angle=self.theta)

###############


# function that calculates correlation value
# https://www.ux1.eiu.edu/~nilic/Nina%27s-article.pdf
def get_corr(alice_mis_base, alice_mis_res, bob_mis_base, bob_mis_res):

	Pppa1b1 = 0
	Pmma1b1 = 0
	Ppma1b1 = 0
	Pmpa1b1 = 0
	
	Pppa3b3 = 0
	Pmma3b3 = 0
	Ppma3b3 = 0
	Pmpa3b3 = 0
	
	Pppa1b3 = 0
	Pmma1b3 = 0
	Ppma1b3 = 0
	Pmpa1b3 = 0
	
	Pppa3b1 = 0
	Pmma3b1 = 0
	Ppma3b1 = 0
	Pmpa3b1 = 0
	
	corr = 0
				
	for i in range(len(alice_mis_res)):
	
		# a1 b1
		if alice_mis_base[i]=="(1, 4)" and bob_mis_base[i]=="(1, 8)":
			if alice_mis_res[i]==1 and bob_mis_res[i]=='1':
				Pppa1b1 += 1
			elif alice_mis_res[i]==0 and bob_mis_res[i]=='0':
				Pmma1b1 += 1
			elif alice_mis_res[i]==1 and bob_mis_res[i]=='0':
				Ppma1b1 += 1
			elif alice_mis_res[i]==0 and bob_mis_res[i]=='1':
				Pmpa1b1 += 1
		# a3 b3
		elif alice_mis_base[i]=="(0, 1)" and bob_mis_base[i]=="(15, 8)":
			if alice_mis_res[i]==1 and bob_mis_res[i]=='1':
				Pppa3b3 += 1
			elif alice_mis_res[i]==0 and bob_mis_res[i]=='0':
				Pmma3b3 += 1
			elif alice_mis_res[i]==1 and bob_mis_res[i]=='0':
				Ppma3b3 += 1
			elif alice_mis_res[i]==0 and bob_mis_res[i]=='1':
				Pmpa3b3 += 1
		# a1 b3
		elif alice_mis_base[i]=="(1, 4)" and bob_mis_base[i]=="(15, 8)":
			if alice_mis_res[i]==1 and bob_mis_res[i]=='1':
				Pppa1b3 += 1
			elif alice_mis_res[i]==0 and bob_mis_res[i]=='0':
				Pmma1b3 += 1
			elif alice_mis_res[i]==1 and bob_mis_res[i]=='0':
				Ppma1b3 += 1
			elif alice_mis_res[i]==0 and bob_mis_res[i]=='1':
				Pmpa1b3 += 1
		# a3 b1
		elif alice_mis_base[i]=="(0, 1)" and bob_mis_base[i]=="(1, 8)":
			if alice_mis_res[i]==1 and bob_mis_res[i]=='1':
				Pppa3b1 += 1
			elif alice_mis_res[i]==0 and bob_mis_res[i]=='0':
				Pmma3b1 += 1
			elif alice_mis_res[i]==1 and bob_mis_res[i]=='0':
				Ppma3b1 += 1
			elif alice_mis_res[i]==0 and bob_mis_res[i]=='1':
				Pmpa3b1 += 1
	
		# check if all probabilities add to 1
		if Pppa1b1+Pppa3b3+Pppa1b3+Pppa3b1 + Pmma1b1+Pmma3b3+Pmma1b3+Pmma3b1 + Ppma1b1+Ppma3b3+Ppma1b3+Ppma3b1 + Pmpa1b1+Pmpa3b3+Pmpa1b3+Pmpa3b1 != len(alice_mis_res):
			return 1
		
		# normalize
		Pppa1b1 /= len(alice_mis_base)
		Pppa3b3 /= len(alice_mis_base)
		Pppa1b3 /= len(alice_mis_base)
		Pppa3b1 /= len(alice_mis_base)
		#
		Pmma1b1 /= len(alice_mis_base)
		Pmma3b3 /= len(alice_mis_base)
		Pmma1b3 /= len(alice_mis_base)
		Pmma3b1 /= len(alice_mis_base)
		#
		Ppma1b1 /= len(alice_mis_base)
		Ppma3b3 /= len(alice_mis_base)
		Ppma1b3 /= len(alice_mis_base)
		Ppma3b1 /= len(alice_mis_base)
		#
		Pmpa1b1 /= len(alice_mis_base)
		Pmpa3b3 /= len(alice_mis_base)
		Pmpa1b3 /= len(alice_mis_base)
		Pmpa3b1 /= len(alice_mis_base)
		
		# E
		Ea1b1 = Pppa1b1 + Pmma1b1 - Ppma1b1 - Pmpa1b1
		Ea3b3 = Pppa3b3 + Pmma3b3 - Ppma3b3 - Pmpa3b3
		Ea1b3 = Pppa1b3 + Pmma1b3 - Ppma1b3 - Pmpa1b3
		Ea3b1 = Pppa3b1 + Pmma3b1 - Ppma3b1 - Pmpa3b1
	
		# final correlation
		corr = Ea1b1 - Ea1b3 + Ea3b1 + Ea3b3
    
	return corr
	
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

        key = []
        alice_mis_base = [] # array of mismatched bases - base
        alice_mis_res = [] # array of mismatched bases - result
        bob_mis_base = [] # array of mismatched bases - base
        bob_mis_res = [] # array of mismatched bases - result
        
        bases = [
            Basis(0),
            Basis(1, 4),
            Basis(1, 8),
        ]

        while len(key) < key_length:
            # Create EPR pair
            qubit = epr_socket.create_keep()[0]

            basis = random.choice(bases)
            basis.rotate(qubit)

            measurement = qubit.measure()
            alice.flush()
            measurement = int(measurement)

            # Alice sends her basis first
            socket.send(basis.id)
            # Wait for Bob's basis, classical
            bob_basis_id = socket.recv()

            if bob_basis_id == basis.id:
                key.append(measurement)
                
            # save information of mismatched bases
            else:
                # save alice's measurement
                alice_mis_res.append(measurement)
                alice_mis_base.append(basis.id)
                
                # save bob's measurement
                res = socket.recv()
                alice.flush()
                bob_mis_res.append(res)
                res = socket.recv()
                alice.flush()
                bob_mis_base.append(res)
        
        
	# calculate correlation factor
        #print(alice_mis_res, file=f)
        #print(key, file=f)
        #print(len(alice_mis_res)/len(key), file=f)
        
        #print(alice_mis_base, file=f)
        #print(alice_mis_res, file=f)
        #print(type(alice_mis_res[0]), file=f)
        #print(alice_mis_res, file=f) # int
        #print(bob_mis_base, file=f)
        #print(bob_mis_res[0], file=f)
        #print(type(alice_mis_res[0]), file=f) # str
        #print(type(bob_mis_res[0]), file=f) # str
        S = str( get_corr(alice_mis_base, alice_mis_res, bob_mis_base, bob_mis_res) );
        print(S, file=f)
        # send result to Bob
        socket.send(S)
        alice.flush()
        
        if float(S) > 2:
        	return {
        		"secret_key": key,
        	}
        else:
        	return {
        		"secret_key": None,
        	}


if __name__ == "__main__":
    main()
