from numpy import *

head = "Theta [deg.]  Phi   [deg.]  Abs(E   )[V/m   ]   Abs(Cross)[V/m   ]  Phase(Cross)[deg.]  Abs(Copol)[V/m   ]  Phase(Copol)[deg.]  Ax.Ratio[      ]"
sep = "------------------------------------------------------------------------------------------------------------------------------------------------------"

with open('farfields/custom.txt', 'w') as f:
    f.write(head)
    f.write("\n")
    f.write(sep)
    f.write("\n")

    for phi in range(360):
        for theta in range(181):
            theta = str(theta)
            phi = str(phi)
            e = str(1)
            #xp = str(0)
            xp = str(0)
            pxp = str(0)
            co = str(1 / cos(float(theta) * pi / 180 / 2) ** 2)
            #co = str(1)
            pco = str(180)

            f.write(theta + "          " + phi + "          " + e + "          " + xp + "          " + pxp + "          " + co + "          " + pco)
            f.write('\n')