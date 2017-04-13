from architecture import *
from cacheprotocol import *

Uncached=0
Shared=1
Exclusive=2
class DirectoryEntry:
   def __init__(self,nprocs):
      self.state = Uncached
      self.tag = None
      self.nprocs = nprocs
      self.sharing = np.zeros(nprocs,dtype=int)

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


   def decodeStateName(self,state):
      if state==Uncached:
         return 'Uncached'
      if state==Exclusive:
         return 'Exclusive'
      if state==Shared:
         return 'Shared'
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
      #print proc_id,self.entries[block_id].sharing,self.entries[block_id].state
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
      self.stats.num_reads += 1
      req_cycles = 0
      block_id, _ = decompose_mem_address(addr,self.arch.block_size)
      tag, slot, _ = map_mem_address(addr,self.arch.block_size,self.arch.num_lines)
      self.has(proc_id,addr)
      hit = self.arch.procs[proc_id].has(slot,tag)
      
      buff = 'Processor P'+str(proc_id)+' reads word in address '+str(addr)+', with tag '+str(tag)+' and slot '+str(slot)+'.'

      #print self.arch.procs[proc_id].has(slot,tag), self.arch.procs[proc_id].state(slot,tag), self.decodeState(self.arch.procs[proc_id].state(slot,tag))
      req_cycles += 1 #Probing local cache to match tag and check the state: 1 cycle
      if not hit or self.arch.procs[proc_id].state(slot,tag)==Uncached:
         buff += ' A cache miss occurred'
         if hit:
            buff += ' due to state '+self.decodeStateName(self.arch.procs[proc_id].lines[slot].state)+'.'
         else:
            buff += '.'
         self.stats.num_misses += 1
         if self.arch.procs[proc_id].lines[slot].state==Shared:
            replaced_block_id = compose_block_id(self.arch.procs[proc_id].lines[slot].tag,slot,self.arch.num_lines)
            self.entries[replaced_block_id].state = Uncached
            self.entries[replaced_block_id].sharing[proc_id] = 0
         elif self.arch.procs[proc_id].lines[slot].state==Exclusive:
            replaced_block_id = compose_block_id(self.arch.procs[proc_id].lines[slot].tag,slot,self.arch.num_lines)
            self.entries[replaced_block_id].state = Uncached
            self.entries[replaced_block_id].sharing[proc_id] = 0
            self.stats.replacement_writeback += 1
            buff += ' A replacement writeback was required.'
            #if self._debug:
            #   print 'Replacement Writeback'
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
            buff += ' Data transferred from remote processor in Shared state with distance '+str(pdist)+'.'
         elif self.entries[block_id].state==Uncached:
            req_cycles += 10 #Off-chip read: Memory Access latency: 10 cycles
            req_cycles += 3 #Directory sends data to the originator: 3 cycles
            self.stats.offchip_access += 1
            buff += ' Data transferred from main memory.'
         elif self.entries[block_id].state==Exclusive:
            self.stats.remote_access += 1
            self.stats.protocol_writeback += 1 #Writeback to memory due to protocol: 0 cycles (happens in background)
            #if self._debug:
            #   print 'Protocol Writeback'
            pdist = self.closestProcessor(proc_id,block_id)
            buff += ' Data transferred from remote processor in Exclusive state with distance '+str(pdist)+'.'
            for pid in xrange(self.arch.nprocs):
               if self.entries[block_id].sharing[pid]==1:
                  buff += ' A protocol writeback was required by processor P'+str(pid)+'.'
               self.arch.procs[pid].updateState(slot,tag,Shared)
            #Directory sends message to the closest sharer
            #to forward the data and invalidate the line: 3 cycles
            req_cycles += 3
			#Probe cache at remotes processors to match tag and check the state: 1 cycle
            req_cycles += 1 #probing caches...
            req_cycles += 1 #Access cache and append data in the message: 1 cycle
            req_cycles += pdist*3 #hops from the closest processor up to the current processor
         self.arch.procs[proc_id].fetch(slot,tag)
         #print self.arch.procs[proc_id].state(slot,tag)
         self.arch.procs[proc_id].updateState(slot,tag,Shared)
         #print self.arch.procs[proc_id].state(slot,tag)
         self.entries[block_id].state=Shared
         self.entries[block_id].sharing[proc_id] = 1
      #elif self.arch.procs[proc_id].state(slot,tag)==Exclusive:
      #   self.arch.procs[proc_id].updateState(slot,tag,Shared)
      #   self.entries[block_id].state=Shared
      #   self.entries[block_id].sharing[proc_id] = 1
      #   req_cycles += 3 #One hop to the memory controller: 3 cycles
      else:
         buff += ' A cache hit occurred with cache line found in state '+self.decodeStateName(self.arch.procs[proc_id].lines[slot].state)+'.'
         self.stats.private_access += 1
      req_cycles += 1 #Reading data from local cache: 1 cycle

      buff += ' ('+str(req_cycles)+' cycles taken)'
      if self._debug:
         print buff
      self.stats.cycle_count += req_cycles
      return (hit, req_cycles)

   def write(self, proc_id, addr):
      self.stats.num_reqs += 1
      self.stats.num_writes += 1
      req_cycles = 0
      block_id, _ = decompose_mem_address(addr,self.arch.block_size)
      tag, slot, _ = map_mem_address(addr,self.arch.block_size,self.arch.num_lines)
      self.has(proc_id,addr)
      hit = self.arch.procs[proc_id].has(slot,tag)
      #print self.arch.procs[proc_id].has(slot,tag), self.arch.procs[proc_id].state(slot,tag), self.decodeState(self.arch.procs[proc_id].state(slot,tag))
      req_cycles += 1 #Probing local cache to match tag and check the state: 1 cycle

      buff = 'Processor P'+str(proc_id)+' writes word in address '+str(addr)+', with tag '+str(tag)+' and slot '+str(slot)+'.'

      numInvalidations = 0
      if not hit or self.arch.procs[proc_id].state(slot,tag)==Uncached:
         buff += ' A cache miss occurred'
         if hit:
            buff += ' due to state '+self.decodeStateName(self.arch.procs[proc_id].lines[slot].state)+'.'
         else:
            buff += '.'
         self.stats.num_misses += 1	
         if self.arch.procs[proc_id].lines[slot].state==Shared:
            replaced_block_id = compose_block_id(self.arch.procs[proc_id].lines[slot].tag,slot,self.arch.num_lines)
            self.entries[replaced_block_id].state = Uncached
            self.entries[replaced_block_id].sharing[proc_id] = 0
         elif self.arch.procs[proc_id].lines[slot].state==Exclusive:
            replaced_block_id = compose_block_id(self.arch.procs[proc_id].lines[slot].tag,slot,self.arch.num_lines)
            self.entries[replaced_block_id].state = Uncached
            self.entries[replaced_block_id].sharing[proc_id] = 0
            self.stats.replacement_writeback += 1
            buff += ' A replacement writeback was required.'
            #if self._debug:
            #   print 'Replacement Writeback'
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
               self.entries[block_id].sharing[pid] = 0
               if pid!=proc_id and self.entries[block_id].sharing[pid]!=0:
                  numInvalidations += 1
                  self.entries[block_id].sharing[pid] = 0
                  self.arch.procs[pid].updateState(slot,tag,Uncached)
					 
            req_cycles += 1 #Access cache and append data in the message: 1 cycle
            req_cycles += pdist*3 #hops from the closest processor up to the current processor
            buff += ' Data transferred from remote processor in Shared state with distance '+str(pdist)+'.'
         elif self.entries[block_id].state==Uncached:
            req_cycles += 10 #Off-chip read: Memory Access latency: 10 cycles
            req_cycles += 3 #Directory sends data to the originator: 3 cycles
            self.stats.offchip_access += 1
            buff += ' Data transferred from main memory.'
         elif self.entries[block_id].state==Exclusive:
            self.stats.remote_access += 1
            pdist = self.closestProcessor(proc_id,block_id)
            #for pid in xrange(self.arch.nprocs):
            #   if self.arch.procs[pid].state(slot,tag)==Exclusive:
            #      self.stats.protocol_writeback += 1 #Writeback to memory due to protocol: 0 cycles (happens in background)
            #      if self._debug:
            #         print 'Protocol Writeback'
            #   self.arch.procs[pid].updateState(slot,tag,Uncached)
            #Directory sends message to the closest sharer
            #to forward the data and invalidate the line: 3 cycles
            req_cycles += 3
            req_cycles += 1 #probing caches...
            for pid in xrange(self.arch.nprocs):
               self.entries[block_id].sharing[pid] = 0
               if pid!=proc_id and self.entries[block_id].sharing[pid]!=0:
                  numInvalidations += 1
                  self.entries[block_id].sharing[pid] = 0
                  self.arch.procs[pid].updateState(slot,tag,Uncached)
            req_cycles += 1 #Access cache and append data in the message: 1 cycle
            req_cycles += pdist*3 #hops from the closest processor up to the current processor
            buff += ' Data transferred from remote processor in Exclusive state with distance '+str(pdist)+'.'
      else:
         buff += ' Cache line found in state '+self.decodeStateName(self.arch.procs[proc_id].lines[slot].state)+'.'
         #self.stats.private_access += 1
         #if self.entries[block_id].state==Shared:
         if self.arch.procs[proc_id].state(slot,tag)==Shared:
            self.stats.num_misses += 1
            self.stats.remote_access += 1
            req_cycles += 3 #One hop to the memory controller: 3 cycles
            if sum(self.entries[block_id].sharing)>=0:
               pdist = self.closestProcessor(proc_id,block_id)
               #Directory sends message to the closest sharer
               #to forward the data and invalidate the line: 3 cycles
               req_cycles += 3
			   #Probe cache at remotes processors to match tag and check the state: 1 cycle
               #req_cycles += 1 #probing caches...
               for pid in xrange(self.arch.nprocs):
                  self.entries[block_id].sharing[pid] = 0
                  if pid!=proc_id and self.entries[block_id].sharing[pid]!=0:
                     numInvalidations += 1
                     self.entries[block_id].sharing[pid] = 0
                     self.arch.procs[pid].updateState(slot,tag,Uncached)
               #req_cycles += 1 #Access cache and append data in the message: 1 cycle
               #req_cycles += pdist*3 #hops from the closest processor up to the current processor
         else:
            self.stats.private_access += 1
            self.stats.direct_write += 1
            buff += ' Direct write with cache line found in state '+self.decodeStateName(self.arch.procs[proc_id].lines[slot].state)+'.'

      buff += ' A total of '+str(numInvalidations)+' invalidations were required.'
      self.stats.invalidations += numInvalidations
      self.stats.invalidation_messages += (1 if numInvalidations>0 else 0)

      self.arch.procs[proc_id].fetch(slot,tag)
      self.arch.procs[proc_id].updateState(slot,tag,Exclusive)
      self.entries[block_id].sharing[proc_id] = 1
      self.entries[block_id].sharing[proc_id] = 1
      self.entries[block_id].state=Exclusive
      req_cycles += 1 #write data to local cache: 1 cycle
      self.stats.cycle_count += req_cycles
      buff += ' ('+str(req_cycles)+' cycles taken)'
      if self._debug:
         print buff
      return (hit,req_cycles)
