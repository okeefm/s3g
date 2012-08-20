import json
from profile import *
from errors import *

class GcodeAssembler(object):

  def __init__(self, machine_profile):
    self.machine_profile = machine_profile
    self.start_order = [
        'begin_print',
        'homing',
        'start_position',
        'heat_platform',
        'heat_tools',
        'anchor',
        ]
    self.end_order = [
        'end_position',
        'cool_platform',
        'cool_tools',
        'end_print',
        ]
    self.recipes = Profile('recipes')
    
  def assemble_recipe(self,
      material='PLA',
      tool_0=True,
      tool_1=False,
      begin_print='replicator_begin',
      homing='replicator_homing',
      start_position='replicator_start_position',
      heat_platform='heat_platform',
      anchor='replicator_anchor',
      end_position='replicator_end_position',
      cool_platform='cool_platform',
      end_print='replicator_end',
      ):
    start_template = {
      'begin_print' : begin_print,
      'homing' : homing,
      'start_position' : start_position,
      'heat_platform' : heat_platform,
      'anchor' : anchor,
      }
    end_template = {
      'end_position' : end_position,
      'cool_platform' : cool_platform,
      'end_print' : end_print
      }
    variables = {}
    return_values = [start_template, end_template, variables]
    #Check for dualstrusion
    if tool_0 and tool_1:
      dual_values = self.get_recipe_routines_and_variables('dualstrusion')
      for return_val, dual_val in zip(return_values, dual_values):
        return_val.update(dual_val)
    elif tool_0:
      return_values[0]['heat_tools'] = 'heat_0'
      return_values[1]['cool_tools'] = 'cool_0'
    elif tool_1:
      return_values[0]['heat_tools'] = 'heat_1'
      return_values[1]['cool_tools'] = 'cool_1'
    #Add material values to the return template values
    material_values = self.get_recipe_routines_and_variables(material)
    for return_val, mat_val in zip(return_values, material_values):
      return_val.update(mat_val)
    return return_values

  def assemble_start_sequence(self, recipe):
    order = self.start_order
    template_name = 'print_start_sequence'
    gcodes = self.assemble_sequence_from_recipe(recipe, template_name, order)
    return gcodes

  def assemble_end_sequence(self, recipe):
    order = self.end_order
    template_name = 'print_end_sequence'
    gcodes = self.assemble_sequence_from_recipe(recipe, template_name, order)
    return gcodes
    
  def assemble_sequence_from_recipe(self, recipe, template_name, order):
    gcodes = []
    template = self.machine_profile.values[template_name]
    for routine in order:
      gcodes.extend(template[routine][recipe[routine]])
    return gcodes

  def get_recipe_routines_and_variables(self, material):
    if not material in self.recipes.values:
      raise RecipeNotFoundError
    values = self.recipes.values[material]
    start_routines = values['print_start_sequence']
    end_routines = values['print_end_sequence']
    variables = values['variables']
    return start_routines, end_routines, variables
