# Our Submission to the QuTech Quantum Network Explorer QKD Challenge
## O. Amaro, D. Cruz, D. Magano, J. Moutinho, S. Pratapsi

Please find here a description of our QKD implementation.

## 1a. Basic protocols

For our submission, we implemented the two suggested protocols: 

- E91 (Ekert, Artur K. "Quantum Cryptography and Bell’s Theorem." Quantum
  Measurements in Optics. Springer, Boston, MA, 1992. 413-418.)
- BBM92 (Bennett, Charles H., Gilles Brassard, and N. David Mermin. "Quantum
  cryptography without Bell’s theorem." Physical review letters 68.5 (1992):
  557.)

In the noiseless scenario, the E91 protocol uses on average 2/9 of the EPR pairs to construct the key. We found that BBM92 has a better EPR efficieny, with `(1-p)/2`, where `p` is the fraction of EPR pairs measured in the same basis that we use for testing for Eve's presence. Assuming `p=0.5` and a binomial distribution for the noise, the probability that we miss Eve is 1%.

Therefore, we submited the BBM92 approach. However, we leave our E91 attempt in the `qkd-e91` folder for reference.

## 1b. Eavesdropper

To test against interference by an eavesdropper we considered two Eves:

- Eve 1: Randomly chooses between computational or +/- basis and measures the qubit.
- Eve 2: Always measures in the computational basis.

As implemented in the API, the eavesdropper is called for both Alice's and Bob's qubit. We tested both Eves for keys of 1000 bits and found that the final keys differ in about 33% of the bits for Eve 1 and 25% of the bits for Eve 2.

Ultimately, we picked a threshold of 14% above which we discard the keys due to the possibility of Eve interfering. This comes from the upper
bound on the tolerable error rate for key distribution secure against individual attacks, as discussed in the thesis of Chris Erven:

https://uwspace.uwaterloo.ca/bitstream/handle/10012/3021/Thesis_ChrisErven_SubmittedToGSO.pdf

## 2. Noisy qubits

To deal with the noisy channels, we do not assume that Alice and Bob measure the same qubits when they choose the same basis.

As such, we implemented a Information Reconciliation strategy to correct the keys. We implement Brassard's approach -- the Cascade algorithm with binary search correction -- on Bob's key. We found out that 4 correction steps were enough for large keys.

We also found out that the Cascade algorithm without the back-trace steps works well enough for the key lengths that we used. As such, our Information Reconciliation algorithm is small but effective.
