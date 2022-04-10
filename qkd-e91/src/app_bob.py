from netqasm.logging.glob import get_netqasm_logger
from netqasm.sdk.external import NetQASMConnection, Socket

from epr_socket import DerivedEPRSocket as EPRSocket

logger = get_netqasm_logger()

############### Added myself

from math import pi, log2
import random
from fractions import Fraction

class Basis(Fraction):
    def rotate(self, qubit):
        num, den = self.as_integer_ratio()
        n = num if num >= 0 else 2*den - num
        d = int(log2(den))
        theta = pi * (self if self > 0 else (2-self))

        qubit.rot_X(n, d)

bases = {
    'a3': Basis(0, 1),
    'a2': Basis(1, 8),
    'a1': Basis(1, 4),

    'b2': Basis(0, 1),
    'b3': Basis(-1, 8),
    'b1': Basis(1, 8),
}

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
        # logger.info("IMPLEMENT YOUR SOLUTION HERE")

        key = []

        while len(key) < key_length:
            runs -= 1

            # Receive EPR pair
            qubit = epr_socket.recv_keep()[0]
            bob.flush()

            basis_name = random.choice(['b1', 'b2', 'b3'])
            basis = bases[basis_name]
            basis.rotate(qubit)

            measurement = qubit.measure()
            bob.flush()
            measurement = int(measurement)

            # Wait for Alice's basis
            alice_basis_name = socket.recv()
            alice_basis = bases[alice_basis_name]
            # Bob sends his basis second
            socket.send(basis_name)

            if alice_basis == basis:
                key.append(measurement)
            else:
                socket.send(str(measurement))
                bob.flush()

        accept_string = socket.recv()
        bob.flush()

        accept_key = True if accept_string == '1' else False


    # RETURN THE SECRET KEY HERE
    return {
        "secret_key": key if accept_key else None,
    }


if __name__ == "__main__":
    main()
