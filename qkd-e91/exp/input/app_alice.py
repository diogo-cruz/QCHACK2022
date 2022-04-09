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
            # Wait for Bob's basis
            bob_basis_id = socket.recv()

            if bob_basis_id == basis.id:
                key.append(measurement)


    # RETURN THE SECRET KEY HERE
    return {
        "secret_key": key,
    }


if __name__ == "__main__":
    main()
