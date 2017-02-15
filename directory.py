from architecture import *
from cacheprotocol import *

class DirectoryEntry:
   def __init__(self,nprocs):
      self.state = None
      self.tag = None
      self.nprocs = nprocs
      self.sharing = np.zeros(nprocs)

Uncached=0
Shared=1
Exclusive=2
class DirectoryProtocol(CacheProtocol):
   def __init__(self,arch):
      self._debug = False
      self.arch = arch
      self.stats = Statistics()
      self.entries = {} # block_id -> cache_entry

   def dump(self):
      for pid in xrange(self.arch.nprocs):
         print 'P'+str(pid)
         for cid in xrange(self.arch.num_lines):
            c = self.arch.procs[pid].lines[cid]
            if self.decodeState(c.state):
               print cid,c.tag,self.decodeState(c.state)

   def decodeState(self,state):
      if state==Uncached:
         return 'U'
      if state==Exclusive:
         return 'E'
      if state==Shared:
         return 'S'
      return None

   def sizeInBits(self,word_size):
      return ((self.arch.nprocs*self.arch.block_size*self.arch.num_lines)*(2+word_size))

   def has(self, proc_id, addr):
      block_id, _ = decompose_mem_address(addr,self.arch.block_size)
      if block_id not in self.entries.keys():
         self.entries[block_id] = DirectoryEntry(self.arch.nprocs)
      return self.entries[block_id].sharing[proc_id]!=0

   def closestProcessor(self, proc_id, block_id):
      offset = 1
      found = False
      while offset<self.arch.nprocs:
         if ((proc_id+offset)<self.arch.nprocs) and self.entries[block_id].sharing[proc_id+offset]!=0:
            found = True
            break
         if ((proc_id-offset)>=0) and self.entries[block_id].sharing[proc_id-offset]!=0:
            found = True
            break
         offset += 1
      if found:
         return offset
      return None

   def read(self, proc_id, addr):
      self.stats.num_reqs += 1
      req_cycles = 0
      block_id, _ = decompose_mem_address(addr,self.arch.block_size)
      tag, slot, _ = map_mem_address(addr,self.arch.block_size,self.arch.num_lines)
      hit = self.has(proc_id,addr)
      req_cycles += 1 #Probing local cache to match tag and check the state: 1 cycle
      if not hit:
         self.stats.num_misses += 1
         self.arch.procs[proc_id].fetch(slot,tag)
         req_cycles += 3 #One hop to the memory controller: 3 cycles
         if self.entries[block_id].state==Shared:
            self.stats.remote_access += 1
            pdist = self.closestProcessor(proc_id,block_id)
            #Directory sends message to the closest sharer
            #to forward the data and invalidate the line: 3 cycles
            req_cycles += 3
			#Probe cache at remotes processors to match tag and check the state: 1 cycle
            req_cycles += 1 #probing caches...
            req_cycles += 1 #Access cache and append data in the message: 1 cycle
            req_cycles += pdist*3 #hops from the closest processor up to the current processor
         elif self.entries[block_id].state==Uncached:
            req_cycles += 10 #Off-chip read: Memory Access latency: 10 cycles
            req_cycles += 3 #Directory sends data to the originator: 3 cycles
            self.stats.offchip_access += 1
         elif self.entries[block_id].state==Exclusive:
            self.stats.remote_access += 1
            pdist = self.closestProcessor(proc_id,block_id)
            for pid in xrange(self.arch.nprocs):
               self.arch.procs[pid].updateState(slot,tag,Shared)
            #Directory sends message to the closest sharer
            #to forward the data and invalidate the line: 3 cycles
            req_cycles += 3
			#Probe cache at remotes processors to match tag and check the state: 1 cycle
            req_cycles += 1 #probing caches...
            req_cycles += 1 #Access cache and append data in the message: 1 cycle
            req_cycles += pdist*3 #hops from the closest processor up to the current processor
         self.entries[block_id].state=Shared
         self.entries[block_id].sharing[proc_id] = 1
      else: 
         self.stats.private_access += 1
      req_cycles += 1 #Reading data from local cache: 1 cycle

      self.stats.cycle_count += req_cycles
      return (hit, req_cycles)

   def write(self, proc_id, addr):
      self.stats.num_reqs += 1
      req_cycles = 0
      block_id, _ = decompose_mem_address(addr,self.arch.block_size)
      tag, slot, _ = map_mem_address(addr,self.arch.block_size,self.arch.num_lines)
      hit = self.has(proc_id,addr)
      req_cycles += 1 #Probing local cache to match tag and check the state: 1 cycle
      if not hit:
         self.stats.num_misses += 1
         self.arch.procs[proc_id].fetch(slot,tag)
         req_cycles += 3 #One hop to the memory controller: 3 cycles
         if self.entries[block_id].state==Shared:
            self.stats.remote_access += 1
            pdist = self.closestProcessor(proc_id,block_id)
            #Directory sends message to the closest sharer
            #to forward the data and invalidate the line: 3 cycles
            req_cycles += 3
			#Probe cache at remotes processors to match tag and check the state: 1 cycle
            req_cycles += 1 #probing caches...
            for pid in xrange(self.arch.nprocs):
                  if pid!=proc_id and self.entries[block_id].sharing[pid]!=0:
                     self.entries[block_id].sharing[pid] = 0
                     self.arch.procs[pid].updateState(slot,tag,Uncached)
            req_cycles += 1 #Access cache and append data in the message: 1 cycle
            req_cycles += pdist*3 #hops from the closest processor up to the current processor
         elif self.entries[block_id].state==Uncached:
            req_cycles += 10 #Off-chip read: Memory Access latency: 10 cycles
            req_cycles += 3 #Directory sends data to the originator: 3 cycles
            self.stats.offchip_access += 1
         elif self.entries[block_id].state==Exclusive:
            self.stats.remote_access += 1
            pdist = self.closestProcessor(proc_id,block_id)
            for pid in xrange(self.arch.nprocs):
               self.arch.procs[pid].updateState(slot,tag,Shared)
            #Directory sends message to the closest sharer
            #to forward the data and invalidate the line: 3 cycles
            req_cycles += 3
            req_cycles += 1 #Access cache and append data in the message: 1 cycle
            req_cycles += pdist*3 #hops from the closest processor up to the current processor
         self.entries[block_id].state=Shared
         self.entries[block_id].sharing[proc_id] = 1
      else:
         if self.entries[block_id].state==Shared:
            if sum(self.entries[block_id].sharing)>1:
               for pid in xrange(self.arch.nprocs):
                  if pid!=proc_id and self.entries[block_id].sharing[pid]!=0:
                     self.entries[block_id].sharing[pid] = 0
                     self.arch.procs[pid].updateState(slot,tag,Uncached)
                     #if it is not at the same time, count cycles here
            req_cycles += 3 #invalidates cache (all at the same time?): 3 cycles
         self.entries[block_id].state=Exclusive
         self.arch.procs[proc_id].updateState(slot,tag,Exclusive)
         req_cycles += 3 #update cache line to exclusive?
         self.stats.private_access += 1
      req_cycles += 1 #write data to local cache: 1 cycle

      self.stats.cycle_count += req_cycles
      return hit

