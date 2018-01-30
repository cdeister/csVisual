# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 20:28:05 2018

@author: alexandermore
"""

# Define Stuff and Import Dependencies

from math import pi

# We will use luer BDs, but these seemed close.
# http://www.restek.com/norm-ject-specs

# define common syringes and rods.
syr_3ml={'lenInMM':65.1,'diamInMM':9.65}
syr_10ml={'lenInMM':85.3,'diamInMM':15.9}
syr_50ml={'lenInMM':120.3,'diamInMM':29.2}

# standard T8 3d printer rod is 8 mm per turn.
rod_std={'threadStarts':4,'pitchInMM':2}
rod_fine={'threadStarts':1,'pitchInMM':2}

stepsPerRev=256  # TNC2130 does 256 native.
motorCoils=8
# Pick a syringe and rod, calculate its resolution.
# This is the standard rod example.

# ---- Edit these.

syrToUse=syr_10ml
rodToUse=rod_std


# ------- Don't Edit.
threadStarts=rodToUse['threadStarts']
mmPerTurn=rodToUse['pitchInMM']
heightInMM=syrToUse['lenInMM']
diamInMM=syrToUse['diamInMM']


radiusInMM=diamInMM/2
cVolume=heightInMM*pi*radiusInMM*radiusInMM

#new calculation by Ian

mmPerRev = 8 # lead is the same as mm per revolution, and is the same as pitch*start
mmPerStep = mmPerRev/stepsPerRev
numSteps = heightInMM/mmPerStep

volPerStepInUL = cVolume/numSteps

#leadsPerLength=(threadStarts*mmPerTurn)/heightInMM   # 4 starts, 2 mm per turn. Lead is distance traveled per turn.
#volPerLeadInUL=leadsPerLength*pi*radiusInMM*radiusInMM
#volPerStepInUL=((leadsPerLength/(stepsPerRev/motorCoils))*pi*radiusInMM*radiusInMM)

print ('{:0.2f} ul per step'.format(volPerStepInUL))

