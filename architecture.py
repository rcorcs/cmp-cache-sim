import numpy as np

def decompose_mem_address(addr, block_size):
   nbits = int(np.log2(block_size))
   mask = 2**nbits - 1
   word_id = addr & mask
   block_id = addr >> nbits
   return (block_id, word_id)

def map_mem_address(addr,block_size,num_lines):
   block_id, word_id = decompose_mem_address(addr,block_size)
   nbits = int(np.log2(num_lines))
   mask = 2**nbits - 1
   slot = block_id & mask
   tag = block_id >> nbits
   return (tag, slot, word_id)

class CacheLine:
   def __init__(self,block_size):
      #self.words = np.zeros(2**block_size)
      self.tag = None
      self.state = None

class Cache:
   def __init__(self,block_size,num_lines):
      self.block_size = block_size
      self.num_lines = num_lines
      self.lines = []
      for _ in xrange(num_lines):
         self.lines.append(CacheLine(block_size))

   def has(self,slot,tag):
      return self.lines[slot].tag==tag

   def fetch(self, slot, tag):
      self.lines[slot].tag = tag
      self.lines[slot].state = None

   def updateState(self,slot,tag,state):
      hit = self.has(slot,tag)
      if hit:
         self.lines[slot].state=state
      return hit
   
   def state(self,slot,tag):
      hit = self.has(slot,tag)
      if hit:
         return self.lines[slot].state
      return None

class Architecture:
   def __init__(self,nprocs,block_size,num_lines):
      self.nprocs = nprocs
      self.procs = []
      self.block_size = block_size
      self.num_lines = num_lines
      for _ in xrange(nprocs):
         self.procs.append(Cache(block_size,num_lines))

