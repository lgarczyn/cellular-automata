#!/usr/bin/env python3
"""The REAL automaton: a faithful Python port of CA.CollatzStep (ca-collatz-step.js).

Verified: each row is exactly one ODD Collatz step (3n+1 then strip all trailing
zeros). Seed 27 gives rows 27, 41, 31, 47, 71, 107, 161, 121, 91, 137, ... = the
odd trajectory of 27.

Geometry (this is the "diagonalized" layout Lou meant): the number is a DIAGONAL
BAND. Column 0 is the LeastEdge/LSB side (left); the LeastEdge (the halving front)
eats from the low-c/left and advances right; the MSB grows at high-c/right; the
active band drifts down-and-right as steps proceed. A "pattern" is a spatial
configuration of (digit, carry) cells and the LeastEdge - NOT a fixed-position
integer stack. Every earlier CA experiment that used x3 / 3n+1-then-halve integer
arithmetic at fixed positions was the wrong layout; use THIS module instead.

cell = None | {'d':digit, 'c':carry, 'le':bool}. LE = LeastEdge (d=0, c=1) - the
carry:1 is the +1 of 3n+1.
"""
# The REAL automaton: CA.CollatzStep (ca-collatz-step.js). Verified: each row is
# one odd Collatz step. cell = None | {'d','c','le'}. LE = LeastEdge (d0,c1).
LE={'d':0,'c':1,'le':True}
def isLE(x): return x is not None and x.get('le')
def step_cell(get,r,c):
    above=get(r-1,c)
    if isLE(above): return LE
    shifted=get(r-1,c-1); same=above; left=get(r,c-1)
    carryIn=left['c'] if left is not None else 0
    if shifted is None and same is None and carryIn==0: return None
    s=(shifted['d'] if shifted else 0)+(same['d'] if same else 0)+carryIn
    digit=s%2; carry=1 if s>=2 else 0
    if isLE(left):
        if digit==0 and carry==1: return LE
        if (same and same['d']==0) and isLE(shifted): return LE
    return {'d':digit,'c':carry,'le':False}
def run(n,W,H):
    g=[[None]*W for _ in range(H)]
    msb=max(1,n.bit_length()); g[0][0]=LE
    for c in range(1,W): g[0][c]={'d':(n>>(c-1))&1,'c':0,'le':False} if (c-1)<msb else None
    def get(r,c): return g[r][c] if 0<=r<H and 0<=c<W else None
    for r in range(1,H):
        for c in range(W): g[r][c]=step_cell(get,r,c)
    return g
def readrow(g,r):
    W=len(g[0]); n=0
    for c in range(W-1,-1,-1):
        cell=g[r][c]
        if cell is not None and not cell.get('le'): n=n*2+cell['d']
    return n
if __name__=='__main__':
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, numpy as np
    from matplotlib.colors import ListedColormap
    g=run(27,70,46)
    a=np.zeros((len(g),len(g[0])))
    for r in range(len(g)):
        for c in range(len(g[0])):
            x=g[r][c]
            a[r][c]=2 if isLE(x) else (1 if (x and x['d']) else (0 if x is None else 0.4))
    fig,ax=plt.subplots(figsize=(15,10),dpi=130)
    ax.imshow(a,cmap=ListedColormap(['#0b0b14','#20304a','#7ee6a0','#ff2d6f']),interpolation='nearest',aspect='equal')
    ax.set_title('The REAL automaton CA.CollatzStep, seed 27. green=1-digit, dark-blue=0-digit, pink=LeastEdge (halving front). col 0 left.',fontsize=10)
    ax.set_xlabel('column c  (0 = LSB side / LeastEdge, high c = MSB)'); ax.set_ylabel('row = odd Collatz step')
    fig.tight_layout(); fig.savefig('/home/lou/Projects/cellular-automata/images/collatz-real-grids.png',facecolor='white')
    print('verified odd trajectory:', [readrow(g,r) for r in range(10)])
