# https://stackoverflow.com/questions/17104673/incremental-entropy-computation

from math import log
from random import randint

# maps x to -x*log2(x) for x>0, and to 0 otherwise 
h = lambda p: -p*log(p, 2) if p > 0 else 0

# update entropy if new example x comes in 
def update(H, S, x):
    new_S = S+x
    return 1.0*H*S/new_S+h(1.0*x/new_S)+h(1.0*S/new_S)

# entropy of union of two samples with entropies H1 and H2
def update(H1, S1, H2, S2):
    S = S1+S2
    return 1.0*H1*S1/S+h(1.0*S1/S)+1.0*H2*S2/S+h(1.0*S2/S)

# compute entropy(L) using only `update' function 
def test(L):
    S = 0.0 # sum of the sample elements
    H = 0.0 # sample entropy 
    for x in L:
        H = update(H, S, x)
        S = S+x
    return H

# compute entropy using the classic equation 
def entropy(L):
    n = 1.0*sum(L)
    return sum([h(x/n) for x in L])

# entry point 
if __name__ == "__main__":
    L = [randint(1,100) for k in range(100)]
    M = [randint(100,1000) for k in range(100)]

    L_ent = entropy(L)
    L_sum = sum(L)

    M_ent = entropy(M)
    M_sum = sum(M)

    T = L+M

    print("Full = ", entropy(T))
    print("Update = ", update(L_ent, L_sum, M_ent, M_sum))
