#!/usr/bin/env python

import numpy, sys, re, colorsys, os, time
import struct, zlib, array
import cairosvg

from common import *
from markercodes import *
from cairosvg import surface

MO_ITALY     = "italy"
MO_EUROPE    = "europe"
MO_WORLD     = "world"

def verify_keys(dic1, dic2):
  for k in dic1.keys():
    if not k in dic2.keys():
      return False
  return True

def main(argv):

  _file_input = "data_italy_test_values.dat"
#  _file_input = "data_europe_test_values.dat"
#  _file_input = "data_world_test_values.dat"
  _min    = 0
  _max    = 0

  VALUES = {}
  INVALID_VALUES = 0
  file_input = open(_file_input, 'r')
  for line in file_input:

    if line.strip() == None or line.strip() == "":
      continue
    row = line.strip().split()
    if len(row) > 2:
      # Meh, we have a val with spaces
      # Let's get the last value as val and merge the rest
      value = row.pop()
      key = " ".join(row)
      key = key.replace("'","")
    else:
      key = row[0].replace("'","")
      value = row[1]
    if value == INVALID_VALUE:
      INVALID_VALUES += 1
    VALUES[key] = float(value)
    log('info', "V[{}]={}".format(key, value))

  if len(VALUES) == len(ITALY_MARKER_CODES):
    error = not verify_keys(VALUES, ITALY_MARKER_CODES)
    MODE_OF_OPERATION = MO_ITALY
    MARKER_CODES = ITALY_MARKER_CODES
  elif len(VALUES) == len(EUROPE_MARKER_CODES):
    error = not verify_keys(VALUES, EUROPE_MARKER_CODES)
    MODE_OF_OPERATION = MO_EUROPE
    MARKER_CODES = EUROPE_MARKER_CODES
  elif len(VALUES) == len(WORLD_MARKER_CODES):
    error = not verify_keys(VALUES, WORLD_MARKER_CODES)
    MODE_OF_OPERATION = MO_WORLD
    MARKER_CODES = WORLD_MARKER_CODES
  else:
    log('info', "NO MATCH")
    error = True;
    MODE_OF_OPERATION = "none"
    MARKER_CODES = {}
  
  log('info', "[mode={}] Data file detected and parsed (invalid vals={})".format(MODE_OF_OPERATION, INVALID_VALUES))
  if error:
    log('error', "[mode={}] Either wrong data files size ({}) or keys are wrong".format(MODE_OF_OPERATION, len(VALUES)))
    sys.exit(1)

  SVG_INPUT = "input_" + MODE_OF_OPERATION + ".svg"
  SVG_OUTPUT = os.path.splitext(_file_input)[0] + ".svg"
  PNG_OUTPUT = os.path.splitext(_file_input)[0] + ".png"
  PNG_OUTPUT_LEGEND = os.path.splitext(_file_input)[0] + "_legend.png"

  GRADIENT_STEPS = 25
  L_COLOR = [255, 0, 0]
  F_COLOR = [0, 255, 0]

  if _min == None or _max == None or _min == _max:
    VALUE_MIN = min(VALUES.values())
    VALUE_MAX = max(VALUES.values())
  else:
    VALUE_MIN = _min
    VALUE_MAX = _max

  log('info', "[mode={}] SVG input:  {}".format(MODE_OF_OPERATION, SVG_INPUT))
  log('info', "[mode={}] SVG output: {}".format(MODE_OF_OPERATION, SVG_OUTPUT))
  log('info', "[mode={}] Minimum value: G[{}]={}".format(MODE_OF_OPERATION, '%.3f' % VALUE_MIN, F_COLOR))
  log('info', "[mode={}] Maximum value: G[{}]={}".format(MODE_OF_OPERATION, '%.3f' % VALUE_MAX, L_COLOR))
  log('info', "[mode={}] Gradient steps: {}".format(MODE_OF_OPERATION, GRADIENT_STEPS))

  GRADIENT = generate_G(F_COLOR, VALUE_MIN, L_COLOR, VALUE_MAX, GRADIENT_STEPS)
  CODES = generate_C(GRADIENT, VALUES)
  
  log('info', "")
  generate_S(SVG_INPUT, SVG_OUTPUT, MARKER_CODES, CODES)

  log('info', "")
  log('info', "[mode={}] SVG Output to: {}".format(MODE_OF_OPERATION, SVG_OUTPUT))

  write_png_home(PNG_OUTPUT_LEGEND, 500, 250, F_COLOR, L_COLOR)
  log('info', "[mode={}] PNG Legend Output to: {}".format(MODE_OF_OPERATION, PNG_OUTPUT_LEGEND))

  kwargs = {'dpi': float(96)}
  kwargs['write_to'] = PNG_OUTPUT
  kwargs['url'] = SVG_OUTPUT
  surface.PNGSurface.convert(**kwargs)
  log('info', "[mode={}] PNG Output to: {}".format(MODE_OF_OPERATION, PNG_OUTPUT))

  return 0

# ENTRY POINT
if __name__ == "__main__":
  sys.exit(main(sys.argv))
