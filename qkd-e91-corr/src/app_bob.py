from netqasm.logging.glob import get_netqasm_logger
from netqasm.sdk.external import NetQASMConnection, Socket

from epr_socket import DerivedEPRSocket as EPRSocket

logger = get_netqasm_logger()

############### Added myself

from math import pi
import random
from fractions import Fraction
f = open('/home/sagar/Projects/hackathons/qchack/2022/QCHACK2022/alice.txt', 'a')

class Basis:
    def __init__(self, a, b=1):
        fraction = Fraction(a, b)
        self.fraction = fraction
        self.theta = (fraction * pi) if a >=0 else (2*pi - fraction * pi)
        self.id = str(self.fraction.as_integer_ratio())

    def rotate(self, qubit):
        qubit.rot_Z(0, 0, angle=self.theta)

###############


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
        logger.info("IMPLEMENT YOUR SOLUTION HERE")

        key = []

        bases = [
            Basis(0),
            Basis(15, 8),
            Basis(1, 8),
        ]

        while len(key) < key_length:
            qubit = epr_socket.recv_keep()[0]
            bob.flush()

            basis = random.choice(bases)
            basis.rotate(qubit)

            measurement = qubit.measure()
            bob.flush()
            measurement = int(measurement)

            # Wait for Alice's basis
            alice_basis_id = socket.recv()
            # Bob sends his basis second
            socket.send(basis.id)

            if alice_basis_id == basis.id:
                key.append(measurement)
                
            # if bases mismatch
            if bob_basis_id != basis.id:
            	# send bob's 
		    # send measurement result
		    socket.send(measurement)
		    # send basis
		    socket.send(basis.id)

	# get correlation
        S = socket.recv()
	bob.flush()
	        
	if S > 0.9* 2*sqrt(2):
	    # RETURN THE SECRET KEY HERE
	    return {
		"secret_key": key,
	    }
	else:
	    # RETURN THE SECRET KEY HERE
	    return {
		"secret_key": None,
	    }


if __name__ == "__main__":
    main()
