import numpy, sys, re, colorsys, os, time
import struct, zlib, array

from markercodes import *

VERSION = 'v1.0'

LF = "\n"

LOG_LEVELS = {
  'critical'     :       1,
  'error'        :       2,
  'warning'      :       3,
  'info'         :       4,
  'debug'        :       5
}

CONF = {
  'LOG_LEVEL' : 'debug',
}


INVALID_VALUE = -1

'''
  GENERATE GRADIENT

  The following function generates a dictionary where each
    key: the numeric value betwen F_VAL and L_VAL, aka the raw valye
    value: the RGB color as calculated w.r.t. gradient between F and L_COLOR
  GRADIENT_STEP is simply the resolution of the gradient.
'''
def generate_G(F_COLOR, F_VAL, L_COLOR, L_VAL, GRADIENT_STEPS):
  gradient_values = []
  gradient_raw_pixels = generate_gradient(F_COLOR, L_COLOR, GRADIENT_STEPS)
  for index in range(GRADIENT_STEPS):
    ri = index * 3
    gradient_values.append([  gradient_raw_pixels[ri+0],
                              gradient_raw_pixels[ri+1],
                              gradient_raw_pixels[ri+2]])
  gradient_keys = numpy.linspace( float(F_VAL), 
                                  float(L_VAL), 
                                  GRADIENT_STEPS)
  GRADIENT = dict(zip(gradient_keys, gradient_values))
  return GRADIENT

'''
  GENERATE CODES - Starting from values get the RGB HEX codes

  This is abit more difficult
  Basically we have the VALUES (to be replaced). We calculate the closest key 
  (hence the actual numeric value of which we previously calculated the gradient 
  color) and we use it to get the color from GRADIENT. The rest is trivial/
  However, if VALUES[k] is -1, then the actual data is not available.
'''
def generate_C(GRADIENT, VALUES):
  log('info', "")
  CODES = {}
  for k in sorted(VALUES.keys()):
    region = k.ljust(12)
    value = '%.3f' % VALUES[k]
    if VALUES[k] != INVALID_VALUE:
      key = min(GRADIENT.keys(), key=lambda x:abs(x-VALUES[k]))
      rgbcolor = GRADIENT[key]
      hexcolor = rgb_to_hex(tuple(rgbcolor))
    else:
      key = INVALID_VALUE
      rgbcolor = [100, 100, 100]
      hexcolor = rgb_to_hex(tuple(rgbcolor))
    log("info", "[genC] Key: {} Value: {}\tG[{}]=RGB[{}]={}".format(region, 
      value, '%.3f' % key, ",".join('%3d' % x for x in rgbcolor), hexcolor))
    CODES[k] = hexcolor[1:]
  return CODES

def timestamp():
  now = time.time()
  localtime = time.localtime(now)
  return time.strftime('%m%d_%H%M%S', localtime)

def log(level, line, isFormatted=1):
  global LF, LOG_LEVELS, CONF
  if level not in LOG_LEVELS:
    level = 'error'   
  if LOG_LEVELS[level] <= LOG_LEVELS[CONF['LOG_LEVEL']]:
    if isFormatted:
      line = '[%s] %s%s' % (level, line, LF)
    else:
      line = '%s%s' % (line, LF)
    sys.stderr.write(line)

def find_nearest(array,value):
  idx = (abs(array-value)).argmin()
  return idx

def hex_to_rgb(value):
  value = value.lstrip('#')
  lv = len(value)
  return tuple(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))

def rgb_to_hex(rgb):
  return '#%02x%02x%02x' % rgb

def generate_S(input_filename, output_filename, marker_codes, new_codes):
  log('info', "")

  # Pregenerate REs (performance yay)
  reg_expressions = dict()
  marker_verifier = dict()
  for k in marker_codes.keys(): 
    if marker_codes[k] != "-1":
      reg_expressions[marker_codes[k]] = re.compile("#" + marker_codes[k], re.IGNORECASE)
      marker_verifier[marker_codes[k]] = False

  inputfile = open(input_filename, 'r')
  outputfile = open(output_filename, 'w')
  count = 0
  for line in inputfile:
    for k in marker_codes.keys():
      if marker_codes[k] != "-1":
        reg = reg_expressions[marker_codes[k]]
        newline = reg.sub("#" + new_codes[k], line)
        if newline != line:
          marker_verifier[marker_codes[k]] = True
          line = newline
          count += 1
    outputfile.write(line + LF) 
  outputfile.close()
  
  if count != len(new_codes.keys()):
    log('info', '[genS] Possible Error - count: {} len(new_codes.keys()): {}'.format(count,len(new_codes.keys())))
    fatal_error = False
    for k in sorted(marker_verifier.keys()):
      if marker_verifier[k] == False:
        log('info', '[genS] Fatal Error: marker {} not found'.format(k))
        fatal_error = True
    if fatal_error:
      sys.exit(1)
    else:
      log('info', '[genS] No error. Just multiple matches')

  return output_filename

def output_chunk(out, chunk_type, data):
  out.write(struct.pack("!I", len(data)))
  out.write(chunk_type)
  out.write(data)
  checksum = zlib.crc32(data, zlib.crc32(chunk_type))
  out.write(struct.pack("!i", checksum))

def generate_gradient(f_color, l_color, number_of_shades):
  h_f, s_f, v_f = colorsys.rgb_to_hsv(f_color[0]/255., f_color[1]/255., f_color[2]/255.)
  h_l, s_l, v_l = colorsys.rgb_to_hsv(l_color[0]/255., l_color[1]/255., l_color[2]/255.)
  h_new_interval = numpy.linspace(h_f, h_l, number_of_shades)
  s_new_interval = numpy.linspace(s_f, s_l, number_of_shades)
  v_new_interval = numpy.linspace(v_f, v_l, number_of_shades)
  response = []
  for x in range(number_of_shades):
    r, g, b = colorsys.hsv_to_rgb(h_new_interval[x], s_new_interval[x], v_new_interval[x])
    r, g, b = int(r*255), int(g*255), int(b*255)
    response.extend([r, g, b])
  return response

def get_data(width, height, f_color, l_color):
  compressor = zlib.compressobj()
  data = array.array("B")
  for y in range(height):
    data.append(0)
    line_of_data = generate_gradient(f_color, l_color, width)
    data.extend(line_of_data)
  compressed = compressor.compress(data.tostring())
  flushed = compressor.flush()
  return compressed + flushed

def write_png_home(filename, width, height, f_color, l_color):
  out = open(filename, "wb")
  out.write(struct.pack("8B", 137, 80, 78, 71, 13, 10, 26, 10))
  output_chunk(out, "IHDR", struct.pack("!2I5B", width, height, 8, 2, 0, 0, 0))

  data = get_data(width, height, f_color, l_color)

  output_chunk(out, "IDAT", data)
  output_chunk(out, "IEND", "")
  out.close()