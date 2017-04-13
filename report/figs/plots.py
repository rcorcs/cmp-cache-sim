
import matplotlib.pyplot as plt
import numpy as np

plt.clf()
maxy = 0

ys = {}
#ys[32] = 19.4578348796
ys[64] = 6.56852213542
ys[128] = 4.02166239421
ys[256] = 4.02166239421
ys[512] = 4.02166239421
ys[1024] = 3.12789408366
ys[2048] = 3.02795918783
#ys[4096] = 3.02795918783
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Snooping (MSI)')
maxy = max(maxy,max(ys.values()))

ys = {}
#ys[32] = 10.9380747477
ys[64] = 4.28483072917
ys[128] = 2.9710337321
ys[256] = 2.9710337321
ys[512] = 2.9710337321
ys[1024] = 2.5464630127
ys[2048] = 2.49893697103
#ys[4096] = 
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Directory-based')
maxy = max(maxy,max(ys.values()))

ys = {}
#ys[32] = 18.8328348796
ys[64] = 5.93337504069
ys[128] = 3.39017740885
ys[256] = 3.39017740885
ys[512] = 3.39017740885
ys[1024] = 2.78922526042
ys[2048] = 2.71782430013
#ys[4096] = 
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Snooping (MESI)')
maxy = max(maxy,max(ys.values()))


ys = {}
#ys[32] = 16.9708760579
ys[64] = 5.24739074707
ys[128] = 3.21384175618
ys[256] = 3.39826965332
ys[512] = 3.37238057454
ys[1024] = 2.69644673665
ys[2048] = 2.63219706217
#ys[4096] = 
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Snooping (MESI) + 1KB Cache L2')
maxy = max(maxy,max(ys.values()))


plt.xlabel('Number of Cache Lines')
plt.ylabel('Average Number of Cycles Per Request')
plt.xlim(0,max(ys.keys()))
plt.ylim(0,maxy)
plt.xticks([64,256,512,1024,2048])
plt.legend(loc='best')
#plt.show()
plt.savefig('fig-1-1.pdf')

plt.clf()
maxy = 0

ys = {}
ys[1] = 10.0403289795
ys[2] = 6.04210408529
ys[4] = 4.02166239421
ys[6] = 4.02166239421
ys[8] = 2.56514994303
ys[10] = 2.56514994303
ys[12] = 2.56514994303
ys[16] = 2.2581837972
ys[20] = 2.2581837972
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Snooping (MSI)')
maxy = max(maxy,max(ys.values()))

ys = {}
ys[1] = 5.86500549316
ys[2] = 3.94157918294
ys[4] = 2.9710337321
ys[6] = 2.9710337321
ys[8] = 2.27383931478
ys[10] = 2.27383931478
ys[12] = 2.27383931478
ys[16] = 2.12540181478
ys[20] = 2.12540181478
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Directory-based')
maxy = max(maxy,max(ys.values()))

ys = {}
ys[1] = 7.55543518066
ys[2] = 4.78012593587
ys[4] = 3.39017740885
ys[6] = 3.39017740885
ys[8] = 2.3955485026
ys[10] = 2.3955485026
ys[12] = 2.3955485026
ys[16] = 2.18059285482
ys[20] = 2.18059285482
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Snooping (MESI)')
maxy = max(maxy,max(ys.values()))

ys = {}
ys[1] = 7.62646484375
ys[2] = 4.79508972168
ys[4] = 3.37238057454
ys[6] = 3.37238057454
ys[8] = 2.34948221842
ys[10] = 2.34948221842
ys[12] = 2.34953308105
ys[16] = 2.15936787923
ys[20] = 2.15936787923
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Snooping (MESI) + 1KB Cache L2')
maxy = max(maxy,max(ys.values()))


plt.xlabel('Memory Block Size')
plt.ylabel('Average Number of Cycles Per Request')
plt.xlim(0,max(ys.keys()))
plt.ylim(0,maxy)
#plt.xticks([64,256,512,1024,2048])
plt.legend(loc='best')
#plt.show()
plt.savefig('fig-1-2.pdf')


plt.clf()

ys = {}
#ys[32] = 0.415323893229
ys[64] = 0.830647786458
ys[128] = 0.912679036458
ys[256] = 0.912679036458
ys[512] = 0.912679036458
ys[1024] = 0.951049804688
ys[2048] = 0.954325358073
#ys[4096] = 0.954325358073
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],label='Snooping (MSI)')

ys = {}
#ys[32] = 0.415323893229
ys[64] = 0.830647786458
ys[128] = 0.912679036458
ys[256] = 0.912679036458
ys[512] = 0.912679036458
ys[1024] = 0.951049804688
ys[2048] = 0.954325358073
#ys[4096] = 
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],label='Directory-based')

maxy = max(maxy,max(ys.values()))

plt.xlabel('Number of Cache Lines')
plt.ylabel('Cache Hit Rate')
plt.xlim(0,max(ys.keys()))
plt.ylim(0,1)
plt.xticks([64,256,512,1024,2048])
plt.legend(loc='best')
#plt.show()
plt.savefig('fig-1-3.pdf')

