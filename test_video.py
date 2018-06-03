import subprocess
import math
def xx(filename):
    duration = subprocess.check_output(['ffprobe', '-i', filename, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=%s' % ("p=0")])
    print(duration)
    return math.ceil(float(duration))    

length = xx('/home/pi/yustplayit_assets/519f82588c8e275bd38e6318e8b478ff177a88a3.mp4')
print('Lengh: %f', length)
