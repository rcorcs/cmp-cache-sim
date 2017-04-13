
import matplotlib.pyplot as plt
import numpy as np

plt.clf()
maxy = 0

ys = {}
#ys[32] = 14.1228607415
ys[64] = 9.63720986025
ys[128] = 7.19268449418
ys[256] = 5.38762241777
ys[512] = 4.36621055428
ys[1024] = 4.36621055428
ys[2048] = 4.36621055428
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Snooping (MSI)')
maxy = max(maxy,max(ys.values()))

ys = {}
#ys[32] = 10.0533008885
ys[64] = 6.87596199159
ys[128] = 5.09361585455
ys[256] = 3.73919510586
ys[512] = 3.10640984997
ys[1024] = 3.10640984997
ys[2048] = 3.10640984997
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Directory-based')
maxy = max(maxy,max(ys.values()))

ys = {}
#ys[32] = 14.2175750358
ys[64] = 9.70572096889
ys[128] = 7.11097497237
ys[256] = 5.18998723342
ys[512] = 4.16998226388
ys[1024] = 4.16998226388
ys[2048] = 4.16998226388
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Snooping (MESI)')
maxy = max(maxy,max(ys.values()))


ys = {}
#ys[32] = 13.5096417647
ys[64] = 9.17715553804
ys[128] = 6.76582327287
ys[256] = 5.05097891373
ys[512] = 4.16798245238
ys[1024] = 4.16798245238
ys[2048] =  4.16798245238
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Snooping (MESI) + 1KB Cache L2')
maxy = max(maxy,max(ys.values()))


plt.xlabel('Number of Cache Lines')
plt.ylabel('Average Number of Cycles Per Request')
plt.xlim(0,max(ys.keys()))
plt.ylim(0,maxy)
plt.xticks([64,256,512,1024,2048])
plt.legend(loc='best')
#plt.show()
plt.savefig('fig-2-1.pdf')



plt.clf()
maxy = 0

ys = {}
ys[1] = 5.34397957348
ys[2] = 4.89520782103
ys[4] = 4.36621055428
ys[6] = 4.36621055428
ys[8] = 4.5131701382
ys[10] = 4.5131701382
ys[12] = 4.5131701382
ys[16] = 4.79532691863
ys[20] = 4.79532691863
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Snooping (MSI)')
maxy = max(maxy,max(ys.values()))

ys = {}
ys[1] = 4.00233054297
ys[2] = 3.47396218009
ys[4] = 3.10640984997
ys[6] = 3.10640984997
ys[8] = 3.18721285911
ys[10] = 3.18721285911
ys[12] = 3.18721285911
ys[16] = 3.29677236936
ys[20] = 3.29677236936
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Directory-based')
maxy = max(maxy,max(ys.values()))

ys = {}
ys[1] = 4.86718304187
ys[2] = 4.52638226046
ys[4] = 4.16998226388
ys[6] = 4.16998226388
ys[8] = 4.44888656596
ys[10] = 4.44888656596
ys[12] = 4.44888656596
ys[16] = 4.78725741361
ys[20] = 4.78725741361
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Snooping (MESI)')
maxy = max(maxy,max(ys.values()))

ys = {}
ys[1] = 4.74907592258
ys[2] = 4.45592960389
ys[4] = 4.16798245238
ys[6] = 4.16806813411
ys[8] = 4.44746596293
ys[10] = 4.44755164466
ys[12] = 4.44762019004
ys[16] = 4.78654111438
ys[20] = 4.7866267961
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Snooping (MESI) + 1KB Cache L2')
maxy = max(maxy,max(ys.values()))


plt.xlabel('Memory Block Size')
plt.ylabel('Average Number of Cycles Per Request')
plt.xlim(0,max(ys.keys()))
plt.ylim(0,maxy)
#plt.xticks([64,256,512,1024,2048])
plt.legend(loc='best')
#plt.show()
plt.savefig('fig-2-2.pdf')
