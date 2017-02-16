from enum import Enum

from architecture import *
from cacheprotocol import *

class MSIStates(Enum):
   Invalid=0
   Shared=1
   Modified=2

class MSIProtocol(CacheProtocol):
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
      if state==MSIStates.Modified:
         return 'M'
      if state==MSIStates.Shared:
         return 'S'
      if state==MSIStates.Invalid:
         return 'I'
      return None

   def sizeInBits(self,word_size):
      return ((self.arch.nprocs*self.arch.block_size*self.arch.num_lines)*(2+word_size))

   def read(self, proc_id, addr):
      self.stats.num_reqs += 1
      self.stats.num_reads += 1
      req_cycles = 0
      tag, slot, word_id = map_mem_address(addr,self.arch.block_size,self.arch.num_lines)
      
      #for pid in xrange(self.arch.nprocs):
      #   print 'P'+str(pid),self.decodeState(self.arch.procs[pid].state(slot,tag))

      hit = self.arch.procs[proc_id].has(slot,tag)
      req_cycles += 1 #Probing local cache to match tag and check the state: 1 cycle
      if not hit or self.arch.procs[proc_id].state(slot,tag)==MSIStates.Invalid:
         self.stats.num_misses += 1
         if self.arch.procs[proc_id].lines[slot].state==MSIStates.Modified:
            self.stats.replacement_writeback += 1
            if self._debug:
               print 'Replacement Writeback'
         procs = []
         terminated = False
         isShared = False
         #Snooping: clockwise probing in ring-network
         pid = (proc_id+1)%self.arch.nprocs
         while pid!=proc_id:
            req_cycles += 3 #Send message clockwise one hop: 3 cycles
            if not terminated:
               req_cycles += 1 #Probe cache to match tag and check the state: 1 cycle
               if self.arch.procs[pid].has(slot,tag) and self.arch.procs[pid].state(slot,tag)!=MSIStates.Invalid:
                  req_cycles += 1 #Append data in the message: 1 cycle (terminating action)
                  terminated = True #(terminating action)
            if self.arch.procs[pid].has(slot,tag):
               if self.arch.procs[pid].state(slot,tag)==MSIStates.Modified:
                  self.stats.protocol_writeback += 1 #Writeback to memory due to protocol: 0 cycles (happens in background)
                  if self._debug:
                     print 'Protocol Writeback'
               if self._debug:
                  procs.append(pid)
               if self.arch.procs[pid].state(slot,tag) in [MSIStates.Modified,MSIStates.Shared]:
                  self.arch.procs[pid].updateState(slot,tag,MSIStates.Shared)
                  isShared = True
            pid = (pid+1)%self.arch.nprocs
         req_cycles += 3 #Send message clockwise one hop: 3 cycles (final hop, closing network ring)
         if isShared:
            if self._debug:
               print '[P'+str(proc_id)+' R '+str(addr)+'] Read miss: cache line shared by '+str([ 'P'+str(pid) for pid in procs ])+' (remote cache access)'
            self.stats.remote_access += 1
            self.arch.procs[proc_id].fetch(slot,tag)
            self.arch.procs[proc_id].updateState(slot,tag,MSIStates.Shared)
         else:
            if self._debug:
               print '[P'+str(proc_id)+' R '+str(addr)+'] Read miss: off-chip memory access'
            req_cycles += 3 #One hop to the memory controller: 3 cycles
            req_cycles += 10 #Off-chip read: Memory Access latency 10
            req_cycles += 3 #One hop back from the memory controller: 3 cycles
            self.stats.offchip_access += 1
            self.arch.procs[proc_id].fetch(slot,tag)
            self.arch.procs[proc_id].updateState(slot,tag,MSIStates.Shared)
      else: 
         self.stats.private_access += 1
         if self._debug:
            print '[P'+str(proc_id)+' R '+str(addr)+'] Read hit (private cache access)'
      req_cycles += 1 #Reading data from local cache: 1 cycle

      self.stats.cycle_count += req_cycles
      return (hit,req_cycles)

   def write(self, proc_id, addr):
      self.stats.num_reqs += 1
      self.stats.num_writes += 1
      numInvalidations = 0
      numInvalidationsSent = 0
      req_cycles = 0
      req_cycles += 1 #Probing local cache to match tag and check the state: 1 cycle
      tag, slot, word_id = map_mem_address(addr,self.arch.block_size,self.arch.num_lines)

      #for pid in xrange(self.arch.nprocs):
      #      print 'P'+str(pid),self.decodeState(self.arch.procs[pid].state(slot,tag))

      hit = self.arch.procs[proc_id].has(slot,tag)
      if not hit or self.arch.procs[proc_id].state(slot,tag)==MSIStates.Invalid:
         self.stats.num_misses += 1
         if self.arch.procs[proc_id].lines[slot].state==MSIStates.Modified:
            self.stats.replacement_writeback += 1
            if self._debug:
               print 'Replacement Writeback'
         self.arch.procs[proc_id].fetch(slot,tag)
         procs = []
         terminated = False
         dataAppened = False
         #Snooping: clockwise probing in ring-network
         pid = (proc_id+1)%self.arch.nprocs
         while pid!=proc_id:
            req_cycles += 3 #Send message clockwise one hop: 3 cycles
            if not terminated:
               numInvalidationsSent += 1
               req_cycles += 1 #Probe cache to match tag and check the state: 1 cycle
            #print 'here'
            if self._debug and self.arch.procs[pid].has(slot,tag):
               procs.append(pid)
            if self.arch.procs[pid].has(slot,tag):
               if not dataAppened:
                  req_cycles += 1 #Append data in the message: 1 cycle (non-terminating action)
                  dataAppened += True
               if self.arch.procs[pid].state(slot,tag)==MSIStates.Modified:
                  terminated = True
                  #self.stats.protocol_writeback += 1 #Writeback to memory due to protocol: 0 cycles (happens in background)
                  #if self._debug:
                  #   print 'Protocol Writeback'
               if self.arch.procs[pid].state(slot,tag) in [MSIStates.Modified,MSIStates.Shared]:
                  self.arch.procs[pid].updateState(slot,tag,MSIStates.Invalid)
                  numInvalidations += 1
            pid = (pid+1)%self.arch.nprocs
         req_cycles += 3 #Send message clockwise one hop: 3 cycles (final hop, closing network ring)
         if numInvalidations > 0:
            self.stats.remote_access += 1
            if self._debug:
               print '[P'+str(proc_id)+' W '+str(addr)+'] Upgrade: cache line shared by '+str([ 'P'+str(pid) for pid in procs ])
         else:
            if self._debug:
               print '[P'+str(proc_id)+' W '+str(addr)+'] Write miss: (off-chip memory access)'
            req_cycles += 3 #One hop to the memory controller: 3 cycles
            req_cycles += 10 #Off-chip read: Memory Access latency 10
            req_cycles += 3 #One hop back from the memory controller: 3 cycles
            self.stats.offchip_access += 1
         self.arch.procs[proc_id].updateState(slot,tag,MSIStates.Modified)
      elif self.arch.procs[proc_id].state(slot,tag)==MSIStates.Shared:
         self.stats.num_misses += 1
         self.stats.remote_access += 1
         procs = []
         #Snooping: clockwise probing in ring-network
         pid = (proc_id+1)%self.arch.nprocs
         while pid!=proc_id:
            req_cycles += 3 #Send message clockwise one hop: 3 cycles
            req_cycles += 1 #Probe cache to match tag and check the state: 1 cycle
            if self._debug and self.arch.procs[pid].has(slot,tag):
               procs.append(pid)
            #if self.arch.procs[pid].state(slot,tag) in [MSIStates.Modified,MSIStates.Shared,MSIStates.Invalid]:
            if self.arch.procs[pid].state(slot,tag) in [MSIStates.Modified,MSIStates.Shared]:
               numInvalidations += 1
               self.arch.procs[pid].updateState(slot,tag,MSIStates.Invalid)
            numInvalidationsSent += 1
            #numInvalidations +=  (1 if self.arch.procs[pid].updateState(slot,tag,MSIStates.Invalid) else 0)
            pid = (pid+1)%self.arch.nprocs
         req_cycles += 3 #Send message clockwise one hop: 3 cycles (final hop, closing network ring)
         if numInvalidations > 0:
            if self._debug:
               print '[P'+str(proc_id)+' W '+str(addr)+'] Upgrade: cache line shared by '+str([ 'P'+str(pid) for pid in procs ])
         self.arch.procs[proc_id].updateState(slot,tag,MSIStates.Modified)
      elif self.arch.procs[proc_id].state(slot,tag) in [MSIStates.Modified]:
         self.stats.private_access += 1
         self.stats.direct_write += 1
         if self._debug:
            print '[P'+str(proc_id)+' W '+str(addr)+'] Cache line already-modified in state'
      req_cycles += 1 #Write data to the local cache: 1 cycle

      self.stats.invalidations += numInvalidations
      self.stats.invalidation_messages += numInvalidationsSent
      if self._debug:
         print 'Invalidations ['+str(numInvalidationsSent)+','+str(numInvalidations)+']'
      self.stats.cycle_count += req_cycles
      return (hit,req_cycles)

