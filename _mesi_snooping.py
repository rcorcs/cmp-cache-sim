from enum import Enum

from architecture import *
from cacheprotocol import *

class MESIStates(Enum):
   Invalid=0
   Shared=1
   Exclusive=2
   Modified=3

class MESIProtocol(CacheProtocol):
   def __init__(self,arch):
      self._debug = False
      self.arch = arch
      self.stats = Statistics()

   def dump(self):
      for pid in xrange(self.arch.nprocs):
         print 'P'+str(pid)
         for cid in xrange(self.arch.num_lines):
            c = self.arch.procs[pid].lines[cid]
            if self.decodeState(c.state):
               print cid,c.tag,self.decodeState(c.state)

   def decodeState(self,state):
      if state==MESIStates.Modified:
         return 'M'
      if state==MESIStates.Exclusive:
         return 'E'
      if state==MESIStates.Invalid:
         return 'I'
      if state==MESIStates.Shared:
         return 'S'
      return None

   def sizeInBits(self,word_size):
      return ((self.arch.nprocs*self.arch.block_size*self.arch.num_lines)*(2+word_size))

   def read(self, proc_id, addr):
      self.stats.num_reqs += 1
      req_cycles = 0
      tag, slot, word_id = map_mem_address(addr,self.arch.block_size,self.arch.num_lines)
      hit = self.arch.procs[proc_id].has(slot,tag)
      req_cycles += 1 #Probing local cache to match tag and check the state: 1 cycle
      if not hit:
         self.stats.num_misses += 1
         if self.arch.procs[proc_id].lines[slot].state==MESIStates.Modified:
            self.stats.replacement_writeback += 1
      if not hit or self.arch.procs[proc_id].state(slot,tag)==MESIStates.Invalid:
         procs = []
         terminated = False
         isShared = False
         #Snooping: clockwise probing in ring-network
         pid = (proc_id+1)%self.arch.nprocs
         while pid!=proc_id:
            req_cycles += 3 #Send message clockwise one hop: 3 cycles
            if not terminated:
               req_cycles += 1 #Probe cache to match tag and check the state: 1 cycle
            if self.arch.procs[pid].has(slot,tag):
               req_cycles += 1 #Append data in the message: 1 cycle (terminating action)
               terminated = True #(terminating action)
               if self.arch.procs[pid].state(slot,tag)==MESIStates.Modified:
                  self.stats.protocol_writeback += 1 #Writeback to memory due to protocol: 0 cycles (happens in background)
               if self._debug:
                  procs.append(pid)
            if self.arch.procs[pid].state(slot,tag) in [MESIStates.Modified,MESIStates.Exclusive]:
               isShared = isShared or self.arch.procs[pid].updateState(slot,tag,MESIStates.Shared)
            pid = (pid+1)%self.arch.nprocs
         req_cycles += 3 #Send message clockwise one hop: 3 cycles (final hop, closing network ring)
         if isShared:
            if self._debug:
               print '[P'+str(proc_id)+' R '+str(addr)+'] Read miss: cache line shared by '+str([ 'P'+str(pid) for pid in procs ])+' (remote cache access)'
            self.stats.remote_access += 1
            self.arch.procs[proc_id].fetch(slot,tag)
            self.arch.procs[proc_id].updateState(slot,tag,MESIStates.Shared)
         else:
            if self._debug:
               print '[P'+str(proc_id)+' R '+str(addr)+'] Read miss: exclusive cache line (off-chip memory access)'
            req_cycles += 3 #One hop to the memory controller: 3 cycles
            req_cycles += 10 #Off-chip read: Memory Access latency 10
            self.stats.offchip_access += 1
            self.arch.procs[proc_id].fetch(slot,tag)
            self.arch.procs[proc_id].updateState(slot,tag,MESIStates.Exclusive)
      else: 
         self.stats.private_access += 1
         if self._debug:
            print '[P'+str(proc_id)+' R '+str(addr)+'] Read hit (private cache access)'
      req_cycles += 1 #Reading data from local cache: 1 cycle

      self.stats.cycle_count += req_cycles
      return (hit,req_cycles)

   def write(self, proc_id, addr):
      self.stats.num_reqs += 1
      req_cycles = 0
      req_cycles += 1 #Probing local cache to match tag and check the state: 1 cycle
      tag, slot, word_id = map_mem_address(addr,self.arch.block_size,self.arch.num_lines)
      hit = self.arch.procs[proc_id].has(slot,tag)
      if not hit:
         self.stats.num_misses += 1
         if self.arch.procs[proc_id].lines[slot].state==MESIStates.Modified:
            self.stats.replacement_writeback += 1
      if not hit or self.arch.procs[proc_id].state(slot,tag)==MESIStates.Invalid:
         numInvalidations = 0
         procs = []
         dataAppened = False
         #Snooping: clockwise probing in ring-network
         pid = (proc_id+1)%self.arch.nprocs
         while pid!=proc_id:
            req_cycles += 3 #Send message clockwise one hop: 3 cycles
            req_cycles += 1 #Probe cache to match tag and check the state: 1 cycle
            #print 'here'
            if self._debug and self.arch.procs[pid].has(slot,tag):
               procs.append(pid)
            if self.arch.procs[pid].has(slot,tag):
               if not dataAppened:
                  #print 'HERE'
                  req_cycles += 1 #Append data in the message: 1 cycle (non-terminating action)
                  dataAppened += True
               if self.arch.procs[pid].state(slot,tag)==MESIStates.Modified:
                  self.stats.protocol_writeback += 1 #Writeback to memory due to protocol: 0 cycles (happens in background)
            numInvalidations +=  (1 if self.arch.procs[pid].updateState(slot,tag,MESIStates.Invalid) else 0)
            pid = (pid+1)%self.arch.nprocs
         req_cycles += 3 #Send message clockwise one hop: 3 cycles (final hop, closing network ring)
         if numInvalidations > 0:
            if self._debug:
               print '[P'+str(proc_id)+' W '+str(addr)+'] Upgrade: cache line shared by '+str([ 'P'+str(pid) for pid in procs ])
            self.stats.invalidations += 1
         else:
            if self._debug:
               print '[P'+str(proc_id)+' W '+str(addr)+'] Write miss: (off-chip memory access)'
            req_cycles += 10 #Off-chip read: Memory Access latency 10
            self.stats.offchip_access += 1
         self.arch.procs[proc_id].fetch(slot,tag)
         self.arch.procs[proc_id].updateState(slot,tag,MESIStates.Modified)
      elif self.arch.procs[proc_id].state(slot,tag)==MESIStates.Shared:
         numInvalidations = 0
         procs = []
         #Snooping: clockwise probing in ring-network
         pid = (proc_id+1)%self.arch.nprocs
         while pid!=proc_id:
            req_cycles += 3 #Send message clockwise one hop: 3 cycles
            req_cycles += 1 #Probe cache to match tag and check the state: 1 cycle
            if self._debug and self.arch.procs[pid].has(slot,tag):
               procs.append(pid)
            numInvalidations +=  (1 if self.arch.procs[pid].updateState(slot,tag,MESIStates.Invalid) else 0)
            pid = (pid+1)%self.arch.nprocs
         req_cycles += 3 #Send message clockwise one hop: 3 cycles (final hop, closing network ring)
         if numInvalidations > 0:
            if self._debug:
               print '[P'+str(proc_id)+' W '+str(addr)+'] Upgrade: cache line shared by '+str([ 'P'+str(pid) for pid in procs ])
            self.stats.invalidations += 1
         self.arch.procs[proc_id].updateState(slot,tag,MESIStates.Modified)
      elif self.arch.procs[proc_id].state(slot,tag)==MESIStates.Exclusive:
         if self._debug:
            print '[P'+str(proc_id)+' W '+str(addr)+'] Exclusive cache line'
         self.arch.procs[proc_id].updateState(slot,tag,MESIStates.Modified)
      req_cycles += 1 #Write data to the local cache: 1 cycle

      self.stats.cycle_count += req_cycles
      return (hit,req_cycles)

