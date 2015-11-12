import math
import csv as csv

def calc_apparent_temp(temp, rh, wind):

	if temp is None or rh is None or wind is None:
		return None

	vapPress = (float(rh) / 100.0) * 6.105 * math.exp(17.27 * temp / (237.7 + temp))

	return temp + (0.33 * vapPress) - (0.7 * wind) - 4.0

def main():

	csvFileObj = csv.writer(open(('train.csv'), 'wb'))

	for i in range(0, 40):
		for j in range(20, 100):
			for k in range(0, 7):
				appTemp = calc_apparent_temp(i, j, k)
				if appTemp > 35.0:
					label = 5
				elif appTemp > 26.0:
					label = 4
				elif appTemp > 20.0:
					label = 3
				elif appTemp > 15:
					label = 2
				elif appTemp > 5:
					label = 1
				else:
					label = 0

				csvFileObj.writerow([float(i), float(j), float(k), label])

if __name__ == "__main__":
	main()

