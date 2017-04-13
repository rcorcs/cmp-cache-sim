import sys

if __name__=='__main__':
   from architecture import *
   import snooping
   import directory

   nprocs = 4 #number of processors
   block_size=4 #number of bits used to index a word within a block
   num_lines=512 #number of cache lines per processor

   arch = Architecture(nprocs,block_size,num_lines)
   mem = snooping.MSIProtocol(arch)
   if '-mesi' in sys.argv:
      mem = snooping.MESIProtocol(arch)
   if '-dir' in sys.argv:
      mem = directory.DirectoryProtocol(arch)
   mem._debug = ('-v' in sys.argv)
   showStats = ('-stats' in sys.argv)
   verboseMode = False
   f = open(sys.argv[1])
   for line in f:
      if '#' in line:
         if mem._debug:
            print line[line.index('#'):].strip()
         line = line[:line.index('#')]
      operation = line.strip()
      if len(operation)==0:
         continue
      if operation=='v': #toggle verbose mode
         verboseMode = not verboseMode
      elif operation=='i':
         print mem.stats.invalidation_messages, mem.stats.invalidations
      elif operation=='p':
         mem.dump()
      elif operation=='h':
         print mem.stats.hitRate()
      else:
         tmp = operation.split()
         proc_id = int(tmp[0][1:])
         opcode = tmp[1]
         addr = int(tmp[2])
         #print line, (proc_id,opcode,addr)
         if mem._debug:
            print 'P'+str(proc_id),opcode,addr
         if opcode=='R':
            tmp = mem.read(proc_id,addr)
            #if mem._debug:
            #   print tmp
            #   print '' 
         elif opcode=='W':
            tmp = mem.write(proc_id,addr)
            #if mem._debug:
            #   print tmp
            #   print ''
   f.close()

   #mem.dump()
   #print 'Cache Size (bits):',mem.sizeInBits(32)
   if showStats:
      print 'Total Reads:',mem.stats.num_reads
      print 'Total Writes:',mem.stats.num_writes
      print 'Total Requests:',mem.stats.num_reqs
      print 'Hit Rate:',mem.stats.hitRate()
      print 'Direct Write:',mem.stats.direct_write
      print 'Invalidations:',mem.stats.invalidations
      print 'Invalidation Sent:',mem.stats.invalidation_messages
      print 'Private Accesses:',mem.stats.private_access
      print 'Remote Accesses:',mem.stats.remote_access
      print 'Off-chip Accesses:',mem.stats.offchip_access
      print 'Protocol Writeback:',mem.stats.protocol_writeback
      print 'Replacement Writeback:',mem.stats.replacement_writeback
      print 'Total Cycle Count:',mem.stats.cycle_count
      print 'Mean Cycle Per Req.:',mem.stats.cyclePerRequest()
