import sys

if __name__=='__main__':
   from architecture import *
   import snooping
   import directory

   nprocs = 4 #number of processors
   block_size=4 #number of bits used to index a word within a block
   num_lines=512 #number of cache lines per processor

   arch = Architecture(nprocs,block_size,num_lines)
   #mem = snooping.SnoopingProtocol(arch)
   mem = directory.DirectoryProtocol(arch)
   mem._debug = ('-v' in sys.argv)

   f = open(sys.argv[1])
   for line in f:
      tmp = line.strip().split()
      proc_id = int(tmp[0][1:])
      opcode = tmp[1]
      addr = int(tmp[2])
      #print line, (proc_id,opcode,addr)
      if opcode=='R':
         tmp = mem.read(proc_id,addr)
         if mem._debug:
            print tmp 
      elif opcode=='W':
         tmp = mem.write(proc_id,addr)
         if mem._debug:
            print tmp
   f.close()

   #mem.dump()
   print 'Cache Size (bits):',mem.sizeInBits(32)
   print 'Hit Rate:',mem.stats.hitRate()
   print 'Invalidations:',mem.stats.invalidations
   print 'Private Accesses:',mem.stats.private_access
   print 'Remote Accesses:',mem.stats.remote_access
   print 'Off-chip Accesses:',mem.stats.offchip_access
   print 'Protocol Writeback:',mem.stats.protocol_writeback
   print 'Replacement Writeback:',mem.stats.replacement_writeback
   print 'Total Cycle Count:',mem.stats.cycle_count
   print 'Mean Cycle Per Req.:',mem.stats.cyclePerRequest()
