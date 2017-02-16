class Statistics:
   def __init__(self):
      self.num_reqs = 0
      self.num_reads = 0
      self.num_writes = 0
      self.num_misses = 0
      self.invalidations = 0
      self.invalidation_messages = 0
      self.private_access = 0
      self.remote_access = 0
      self.offchip_access = 0
      self.protocol_writeback = 0
      self.replacement_writeback = 0
      self.cycle_count = 0
      self.direct_write = 0

   def missRate(self):
      return (float(self.num_misses)/float(self.num_reqs))

   def hitRate(self):
      return (1.0-self.missRate())

   def cyclePerRequest(self):
      return float(self.cycle_count)/float(self.num_reqs)

class CacheProtocol:
   def decodeState(self,state):
      pass
   def read(self, proc_id, addr):
      pass
   def write(self, proc_id, addr):
      pass
   def dump(self):
      pass

