from mcpi.minecraft import Minecraft
import time, numpy as np, random, math

#From an x and z coordinate, as well as information about the randomly generated wave function, this spits out a height.
def calcheight(xval, zval, wavecoeff, periodcoeff, numterms, diagnums, phaseshifts):
    output = 70 #Base y value height so stuff doesn't sink into void
    for waveind in range(numterms):
        for diagind in range(diagnums):
            output += wavecoeff[waveind] * np.sin(periodcoeff[waveind] * ((diagind / diagnums) * math.floor(zval) + ((diagnums - diagind) / diagnums) * math.floor(xval)) + phaseshifts[diagind + diagnums * waveind])
    return output

#Partial derivative of the height with respect to x
def calcxderiv(xval, zval, wavecoeff, periodcoeff, numterms, diagnums, phaseshifts):
    xderiv = 0
    for waveind in range(numterms):
        for diagind in range(diagnums):
            xderiv += wavecoeff[waveind] * periodcoeff[waveind] * ((diagnums - diagind) / diagnums) * np.cos(periodcoeff[waveind] * ((diagind / diagnums) * zval + ((diagnums - diagind) / diagnums) * xval) + phaseshifts[diagind + diagnums * waveind])
    return xderiv

#Partial derivative of the height with respect to z
def calczderiv(xval, zval, wavecoeff, periodcoeff, numterms, diagnums, phaseshifts):
    zderiv = 0
    for waveind in range(numterms):
        for diagind in range(diagnums):
            zderiv += wavecoeff[waveind] * periodcoeff[waveind] * (diagind / diagnums) * np.cos(periodcoeff[waveind] * ((diagind / diagnums) * zval + ((diagnums - diagind) / diagnums) * xval) + phaseshifts[diagind + diagnums * waveind])
    return zderiv

#In the beginning of the river creation phaze to test when you're standing on a block, returns coordinates of that block
def sensestanding():
    foundblock = 0
    while foundblock == 0:
        x, y, z = mc.player.getPos()
        blockunder = mc.getBlock(x, y - 1, z)
        if blockunder != 0:
            return x, y - 1, z
        time.sleep(0.05)

#In the river creation phase, takes an x and z coordinate, places blocks in a small grid around that.
def setcluster(centerx, centerz, blockid, wavecoeff, periodcoeff, numterms, diagnums, phaseshifts):

    for xdif in range(-1, 3):     #Increase these size of these two ranges to increase the width of the river
        for zdif in range(-1, 3):
            xval = centerx + xdif
            zval = centerz + zdif

            yval = calcheight(xval, zval - 1 , wavecoeff, periodcoeff, numterms, diagnums, phaseshifts)
            yval = calcheight(xval, zval , wavecoeff, periodcoeff, numterms, diagnums, phaseshifts)
            mc.setBlock(xval, yval - 1, zval, blockid)
            mc.setBlock(xval, yval, zval, blockid)

#Decides what to make a block once the height id determined.
def getblockid(height):
    blockidcutoffs = [(2, 72),(1, 110),(80, 300)] #(Id: Height) pairs, where the id is what block it is, and the height is approximately where you want the transition to be
    height += random.uniform(-3, 3) #Creates a smooth block transition, increase this range to increase the scattering of blocks.
    for pair in blockidcutoffs:
        if height < pair[1]:
            return pair[0]



if __name__ == "__main__":

    mc = Minecraft.create()
    random.seed(1)

    #Wave Function Generation Process
    numterms = 6 #Number of terms in the function in any direction, increase this number to increase noise, decrease this number to increase smoothness.
    maxwaveheight = 13 #Amplitude of the largest wave, increase to increase how extreme the wave is over all.
    minfrequencycoeff = 0.008 #A variable to control the frequency of the largest wave, decrease this value to stretch out the land horizontally.

    #Generates coefficients for the wave based on the variables above
    wavecoeff = []
    periodcoeff = []
    for x in range(numterms):
        wavecoeff.append(maxwaveheight / 2 ** (x))
        periodcoeff.append(minfrequencycoeff * 2 ** (x))

    #Dictates how many different directions wave travel in. A value of 2 will have waves going in only the x and z direction.
    #A value of 3 will have a single diagonal wave as well.
    diagnums = 10

    #Randomizes the phase shift of every wave so there are not obvious convergence points
    phaseshifts = [random.random() * np.pi * 2 for x in range(numterms * diagnums)]

    #Dictates whether the program will be building terrain or building a river for that terrain
    #Swap to "terrain" for terrain generation, and "river" for river generation.
    #Do not change the seed in between doing these, otherwise the function will be different.
    #Advised to run the program first with this as terrain to create terrain, then with
    #river to create a river on that terrain.
    progfunc = "river"

    #Terrain Generation Process
    if progfunc == "terrain":
        mc.postToChat("Beginning terrain generation...")
        cornerpos1 = (-50, 1, -50)       #Dictates the dimensions of the terrain to be generated
        cornerpos2 = (50, 100, 50) #Boxes larger than 300 x 300 have a good chance of crashing the server, probably depends on cpu
        mc.setBlocks(cornerpos1[0], cornerpos1[1], cornerpos1[2], cornerpos2[0], cornerpos2[1], cornerpos2[2], 0) #Clears the area you want to be working with with air beforehand.
        for xval in range(cornerpos1[0], cornerpos2[0] + 1):
            for zval in range(cornerpos1[2], cornerpos2[2] + 1):
                yval = calcheight(xval, zval, wavecoeff, periodcoeff, numterms, diagnums, phaseshifts)
                blockid = getblockid(yval)
                mc.setBlocks(xval, 1, zval, xval, yval, zval, blockid)

    #River Generation Process
    if progfunc == "river":
        mc.postToChat("Step on a block to begin your river")
        xval, yval, zval = sensestanding()

        rate = 0.5 #How fast the river flows, if this number is too high, you may overshoot a basin.

        minfound = 0
        while minfound == 0:
            xderiv = calcxderiv(xval, zval, wavecoeff, periodcoeff, numterms, diagnums, phaseshifts)
            xval -= xderiv * rate
            zderiv = calczderiv(xval, zval, wavecoeff, periodcoeff, numterms, diagnums, phaseshifts)
            zval -= zderiv * rate
            derivmagnitude = (xderiv ** 2 + zderiv ** 2) ** 0.5

            setcluster(xval, zval, 8, wavecoeff, periodcoeff, numterms, diagnums, phaseshifts)

            if derivmagnitude < 0.001:
                minfound = 1
                mc.postToChat("Found Basin")

        #Brute force bottom layer basin filler with water, not necessary for river generation
        ymin = calcheight(xval, zval, wavecoeff, periodcoeff, numterms, diagnums, phaseshifts) + 1
        for xdif in range(-10, 10, 2):
            for zdif in range(-10, 10, 2):
                yval = calcheight(xval + xdif, zval + zdif, wavecoeff, periodcoeff, numterms, diagnums, phaseshifts) + 1
                blockid = mc.getBlock(xval + xdif, ymin, zval + zdif)
                if blockid == 0 or blockid == 8 or blockid == 9:
                    mc.setBlock(xval + xdif, yval, zval+zdif, 8)