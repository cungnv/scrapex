#encoding: utf-8

from __future__ import unicode_literals

SURFFIX_LIST = [item.strip() for item in """
B.V.M
CFRE
CLU
CPA
C.S.C
C.S.J
D.C
D.D
D.D.S
D.M.D
D.O.
D.V.M
Ed.D
Esq
II
III
IV
Inc
J.D
Jr
LL.D
Ltd
M.D
O.D
O.S.B
P.C
P.E
Ph.D
Ret
R.G.S
R.N
R.N.C
S.H.C.J
S.J
S.N.J.M
Sr
S.S.M.O
USA
USAF
USAFR
USAR
USCG
USMC
USMCR
USN
USNR

""".strip().split('\n') ]

PREFIX_LIST = [item.strip() for item in """

Mr
Ms
Mrs
Miss
Master
Mx
Dr



""".strip().split('\n') ]
