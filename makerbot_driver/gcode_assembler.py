import json

class GcodeAssembler(object):

  def __init__(self, 
      material='PLA',
      dualstrusion='False',
      begin_print='replicator_begin',
      homing='replicator_homing',
      start_position='replicator_start_position',
      anchor='replicator_anchor',
      end_position='replicator_end_position',
      end_print='replicator_end',
      )
