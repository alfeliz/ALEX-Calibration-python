#!/usr/bin/python3
#python 3.8
#coding: UTF-8
#Version 1.00
''' IMPORTS '''
import os #File management
import numpy as np #Numerical work in Python. Yeah!!!
import csv as csv #Management opf CSV files.
import matplotlib.pyplot as plt #To plot things.
from scipy.optimize import curve_fit #Curve fitting.
from scipy.signal import find_peaks #Find the peaks of a 1D array.



'''		FUNCTIONS SECTION		'''

''' Function to reduce the number of points in a 1D numpy array, in order to make the printing times reasonable: 
channel is the numpy array, points an integer with the number of points to reduce.
It  does so by first, reshaping the original array dividing it with points in each colum. Later, this newly divided array is then averaged, to reduce the total number of points. 
From: https://stackoverflow.com/questions/26638390/decrease-array-size-by-averaging-adjacent-values-with-numpy '''
def reducir(channel, points):
	return(channel.reshape(-1,points).mean(axis=1))


'''Function to import data made with the ALEX.py program into the memory again:
It returns directly the numpy column stack.'''
def chanimport(file_name):
	if not os.path.isfile(file_name): #File does not exist
		print("File ", file_name, "does not exist or is not a valid file name.")
		tiempo = volts = []
	else:
		tiempo = []
		volts = []
		CH = []

		csv_reader = csv.reader(open(file_name, "r"), delimiter="\t", quotechar=" ")
		for row in 	csv_reader:
			CH.append(row)
		
		for i in range(0, len(CH)):
			tiempo.append(CH[i][0])
			volts.append(CH[i][1])

	#El primer objeto que devuelve es el valor del voltaje, es segundo, el del tiempo
	return volts, tiempo

'''Function to fit the I(t) channel voltage in shortcircuit. 
It is used to find the ALEX L and R parameters and 
adjusting of the Rogowsky coil. Based on the analytical discharge of a RLC circuit. '''
def func(t, t0, B, C, alpha, omega): #Exponencial decreciente con un término oscilatorio.
	return  C + B * np.exp(-alpha * (t - t0)) * np.cos(omega*(t-t0))
    

'''Function to define the initial parameters of the previous function to perform the fitting.
These parameters are based on the signal and previous experiences.'''
def generate_Initial_Parameters(tiempo, CH):
    ##################
    # t0 parameter: Time of maximum intensity on the I(t) vector
    ##################
    t0 = ( tiempo[np.argmax(CH)] ) 
     
    ##################
    #alpha0 parameter: A typical one from page 4 of logbook 2. (In logbook is for time in µs)
    ##################    
    alpha0 = 0.1e6 #typical initial value for time in seconds.
    
    ##################
    #omega0 parameter: Inverse of the period between the first two consecutive peaks of the I(t) signal
    ##################   
    peak_pos, __ = find_peaks(CH, height= np.max(CH)/2, width = 100 ) #Peaks in I(t) signal larger than half max. intensity and wider than 100 points(~100 ns).
    omega0 = float((2*np.pi) / abs( tiempo[peak_pos[0]] - tiempo[peak_pos[1]] ) )
    
    ##################
    #B0 parameter: Max. of first peak in I(t)
    ##################    
    B0 = CH[peak_pos[0]]
    
    ##################
    #C0 parameter: Mean of the I(t) values.
    ##################     
    C0 = abs(np.mean(CH) ) 
    
	#Constructing the initial parameters:
    parameterBounds = []
    parameterBounds.extend( (t0, B0, C0, alpha0, omega0) )

    return parameterBounds
 

verbose = 0 #If you want to see many parameters through the console, put this to 1.

'''		MAIN PROGRAM: Program to calibrate ALEX and check this calibration.	
It works in various phases:
1) Know the folder with all the short circuit shots electrical data is known, it looks for the RAW folder on the shot folder, 
because is there were the voltages raw channel signals employed are.
2) Then, read all the channels with THIS ORDER:
CH1	Rogowsky coil signal ( dI(t)/dt )
CH2	Resistive divider 3 signal.
CH3	Resistive divider 4 signal.
CH4 RC analog integrator signal ( I(t) )
IF THE ORDER OF THE CHANNELS CHANGE, THEY MUST BE CHANGED IN THE PROGRAM TOO.
3) Calculate the values of R and L for the whole circuit, and a value for the Rogowsky scaling of the CH1 from volts into A/s
4) Calculate the values of R and L for the ground and wire supporters. Also, check the values of resistive dividers 3 and 4 calibration or scaling.
5) Make a graph with all the fittings and adjustments, to check them visually. Its name is the shot name and is stored into the shots folder.
6) Store the data of the constants and check results into aTXT file named after the shot, also in the general shots folder.'''

###
#ALEX known calibration constants for the Rogowsky coil and the resistive dividers:
###
#Krog = 18 081 000 000.00 (Like that is easier to read, but it cannot be read by python.
Krog = 18.081e9
DI03 = 5535
DI04 = 3465

vol_nom = 0.0 #Value of the nominal voltage, necessary to calibrate the Rogowsky.

###
#Find the folders with shots folders by askinf the user. 
#IT MUST BE IN THE SAME FOLDER IF YOU DO NOT PROVIDE A ROUTE.
###
#Folder with calibration shots:
folder_name = input("Please, give the folder with the calibration shots: ")
#folder_name ="Calibración ALEX" #For testing purposes. Really, uncomment previous line

'''Take the directory were this script is an show me the folders:
	dirnames is the list of folders within folder_name.
	Make whatever you want with them.'''
for dirpath, dirnames, dirarchivos in os.walk(  os.path.join( os.path.dirname(os.path.abspath(__file__)), folder_name )  ):
	break #Only once, the main folders structure...


''' Come on! Each folder inside folder_name is a calibration ALEX shot that has a RAW folder within.'''
for directorio in dirnames:
	print("\nDisparo/directorio: ", directorio,"\n\n")
	file_route = os.path.join( os.path.dirname(os.path.abspath(__file__)), folder_name, directorio ) #Luke, I am the shot folder in an acceptable by python file route. Kchshh!
	
	for dirpath, dirnames, dirarchivos in os.walk( file_route ): #En cada directorio de disparo, ¿qué directorios y archivos hay?
		shot_data_file = [s for s in dirarchivos if ".html" in s] #The file with the shot data, volatge, electrical carachteristics, calbe organization, etc. is in HTML format and now stored in a list.
		
		if len(shot_data_file) ==1: #We have the data file!!!:
			with open( os.path.join(file_route, shot_data_file[0]) ) as f: #Just to read, do not "fuchiques" into the file.
				for line in f: #Look for the HTML file lines, concretely for the one with the nominal voltage info written as "~ V_nom - V_capacitors".
					if "Material" in line: #This line has the main info on the shot, including the nominal voltage.
						pos1 = line.rfind("</b>") #Position of the last "</b>" string, just before the numbers.
						pos2 = line.find("Volts</p>") #Position of the "Vol..." string, just after the numbers.
						#Take the string between these two positions, and splitted by the minus("-") between them. So the 2 voltages are found...
						dato = line[pos1+4:pos2].strip()[1:].split("-")  #Because of the "~" symbol, I choose to remove the first character.
						vol_nom = float(dato[0]) #It is a number, not a list...

 
		for directorios in dirnames: #Para cada directorio, coge el de datos RAW, que acaba con "_RAW" siempre:
			if directorios[-4:]=="_RAW":
				raw_folder = os.path.join(file_route,directorios)
				CH1, tiempo = chanimport( os.path.join(raw_folder, "LECROY_CH1.csv")  )#Channel names are constant and always equal.
				CH2 = chanimport( os.path.join(raw_folder, "LECROY_CH2.csv") )[0] #To take only the voltag, not the time signal, which is the second part of the returning np.array.
				CH3 = chanimport( os.path.join(raw_folder, "LECROY_CH3.csv") )[0] 
				CH4 = chanimport( os.path.join(raw_folder, "LECROY_CH4.csv") )[0] 

				CH1 = np.array(CH1, dtype='float') #To ensure the internal consistency of the types it is necessary to force the type.
				CH2 = np.array(CH2, dtype='float')
				CH3 = np.array(CH3, dtype='float')
				CH4 = np.array(CH4, dtype='float')
				tiempo = np.array(tiempo, dtype='float')


				'''Use of the I(t) signal to find the parameters of ALEX and adjust the Rogowsky coil.
				First, it adjust the channel to an appropiate function. Then, from these parameters, the values of L, R and Krog can be calculated.'''
				#########################################
				#Fitting part:
				#########################################
				#Initial parameters:
				parametros_iniciales = generate_Initial_Parameters(tiempo, CH1)

				#Fitting only from the maximum in the channel. 
				#Otherwise, amplitudes will be low because of the null values of the experimental channel before the discharge is on:
				# pcov is the estimated covariance of the parameters and used to estimate their error (1 standard deviation)
				# With a check just for the cases that does not converge...(NONE in the tests, but...)
				try:
					parametros, pcov = curve_fit(func, tiempo[np.argmax(CH1):], CH1[np.argmax(CH1):], parametros_iniciales, maxfev=20000)
					errores_parametros = np.sqrt(np.diag(pcov))
				except RuntimeError:
					print("The algorithm did not converge. Initial values of the parameters are considered for this shot.\n")
					parametros = parametros_iniciales
					errores_parametros = parametros_iniciales
				
				#Parameters of the function in a human readable form:
				t0, B, C, alpha, omega = parametros[0], parametros[1], parametros[2], parametros[3], parametros[4]

				#########################################
				# Parameters L and R of the ALEX circuit:
				#########################################
				# L of the circuit (2.2e-6 is the total capacitance (1.1µF*2) ):
				Lcir = 1 / ( 2.2e-6 * (omega**2 + alpha**2) ) #In Henrios
				# R of the circuit:
				Rcir = 2 * alpha * Lcir #In Ohms

				#########################################
				# Rogowsky calibration (pages 2-7 Logbook of diverse projects 02)
				#########################################
				Krog = vol_nom / (Lcir * func(tiempo[np.argmax(CH1)], *parametros) )

				#########################################
				# Circuit calibration of support and ground:
				# (pages 2-7 Logbook of diverse projects 02)
				#########################################
				''' Equation (1):
				Fitting of CH3 as function of CH1 and CH4:
				 CH3 = a CH1  + b CH4, that will be transformed into:
				 CH3 = B * C, with
				 B a matrix with CH1 and CH4 as columns, and 
				 C the column vector with the parameters (a, b) '''
				# Construction of the matrix:
				B = np.vstack([CH1, CH4]).T # .T to traspose the resulting array.

				# Solving the linear equation:
				a, b = np.linalg.lstsq(B, CH3, rcond=None)[0] #Just store the parameters a and b, and do not store anything more.

				''' Equation (2):
				Fitting of CH2 as function of CH1 and CH4:
				 CH2 = c CH1  + d CH4, that will be transformed into:
				 CH2 = B * C2, with
				 B a matrix with CH1 and CH4 as columns, and 
				 C2 the column vector with the parameters (c, d) '''

				# Solving the linear equation: (Matrix is made previously)
				c, d = np.linalg.lstsq(B, CH2, rcond=None)[0] 

				''' Equation (3):
				Fitting of CH2 as function of CH1, CH3 and CH4:
				 CH2 = e CH1  + f CH3 + g CH4, that will be transformed into:
				 CH2 = B2 * C3, with
				 B2 a matrix with CH1, CH3 and CH4 as columns, and 
				 C3 the column vector with the parameters (e, f, g) '''

				#Making the matrix:
				B2 = np.vstack([CH1, CH3, CH4]).T # .T to traspose the resulting array.

				# Solving the linear equation: (Matrix is made previously)
				e, f, g = abs(np.linalg.lstsq(B2, CH2, rcond=None)[0] )

				''' Equation (4):
				Fitting of CH4 as integral  of CH1:
				CH4 = h * Integral(CH1) '''

				h = np.polyfit( CH4,   np.cumsum(CH1) - np.poly1d(np.polyfit(tiempo, np.cumsum(CH1), 1))(tiempo) , 1 )[0] 
				'''What is in the upper line?:
				np.polyfit( CH4,   np.cumsum(CH1) - np.poly1d(np.polyfit(tiempo, h2, 1))(tiempo) , 1 )[0]
				Por partes, que dijo Jack el destripador:
				np.polyfit(   CH4, np.cum..., 1)[0] Ajusta aun polinomio lineal los arrays CH4 y np.cum, recogiendo sólo los parñametros ([0])...
				np.cumsum(CH1) - np.poly1d(np.polyfit(tiempo, np.cumsum(CH1), 1))(tiempo) Usa como integral la suma
				acumulativa MENOS el ajuste lineal de la integral, para quitar los errores de suma en la integral. '''

				###
				#Calculating the ALEX ground and support parts R and L:
				###
				Lt = ( a*DI04) / Krog
				
				Krc = Krog / h

				Rt = (b*DI04)/Krc

				Lsop = (DI03*c)/Krog - Lt

				Rsop = (DI03*d)/Krc - Rt

				if verbose ==1:
					print("Lcir: ", Lcir)
					print("Rcir: ", Rcir)
					print("Krog: ",Krog)
					print("Eq(1) parameters (a, b):  ", a,  b, "\n")
					print("Eq(2) parameters (c, d) : ",  c,  d, "\n")
					print("Eq(3) parameters (e, f, g): ",  e,  f, g)
					print("Eq(4) parameters:", h,  "\n")
					print("Ltierra: ", Lt,"\n")
					print("Krc: ", Krc,"\n")
					print("Rtierra: ", Rt,"\n")
					print("Lsop: ", Lsop,"\n")
					print("Rsop: ", Rsop,"\n")
					print("Comprobando:\n")
					print("DI03 y DI04: ", e,  (DI04/DI03) )
					print("Lsop: ", Lsop,  (f*DI03)/Krog )
					print("Rsop: ", Rsop,  (g*DI03)/Krc )
				
				
				###
				# Saving a graph with adjustments:
				###
				points = 50
				ti = reducir(tiempo, points)

				#Making the reduced in points version for plotting:
				ch1_red = reducir(CH1, points)
				ch3_red = reducir(CH3, points)
				ch3_adj = a*ch1_red + b*reducir(CH4, points)

				ch2_red = reducir(CH2,points)
				ch2_adj = c*ch1_red + d*reducir(CH4, points)

				ch2_sec_adj = e*ch1_red + f*ch3_red + g*reducir(CH4, points)

				#Plot making:
				comprueba, ejes = plt.subplots(4)
				comprueba.suptitle("ALEX calibration with "+directorio[0:-5])
				ejes[0].plot(ti, ch3_red, "r", ti, ch3_adj)
				ejes[1].plot(ti, ch2_red, "b", ti, ch2_adj)
				ejes[2].plot(ti, ch2_red, "g", ti, ch2_sec_adj)
				ejes[3].plot(ti, ch1_red, "*k", ti, func(ti, *parametros))

				for ax in ejes.flat:
					ax.set(xlabel="Seconds", ylabel="Volts")

				comprueba.legend(["CH3 (DIV04)", "CH3 adjusted with CH1(I_dot) and CH4(I)", "CH2 (DIV03)", "CH2 adjusted with CH1 and CH4", "CH2", "CH2 sec. adjusted with CH1, CH3 and CH4", "CH1", "CH1 fitted with parameters"], loc = "upper left", bbox_to_anchor=(1.5, 0.75))
				
				#Making the file route to save data:
				archivo_datos = str(os.path.join( os.path.dirname(os.path.abspath(__file__)), folder_name,directorio[0:-5]))
				comprueba.savefig(archivo_datos+"-graf.png", bbox_inches='tight')
				

				###
				# Saving a text file with the data:
				###

				save_file = open(archivo_datos+"-data.txt", "w")
				
				save_file.write("Obtained data from "+directorio[0:-5]+"\n\n")

				print("Parameters of circuit fitting:\n", file=save_file)
				print("a: {0:6.4f}\n b: {1:6.4f}\n c: {2:6.4f}\n d: {3:6.4f}\n e: {4:6.4f}\n f: {5:6.4f}\n".format(a,b,c,d,e,f), file=save_file)
				
				print("Value of constant for the Rogowsky: \n", file=save_file )
				print("Krog: {0:8.3e}\n".format(Krog), file=save_file)
				print("\nValue of constant for the integrator:\n", file=save_file)
				print("Krc: {0:8.3e}".format(Krc), file=save_file)
								
				print("\nCircuit parameters:\n", file=save_file)
				print("L total (nHr): {0:10.2f}\n R total (mOhm):  {1:6.2f}\n".format(Lcir*1e9, Rcir*1e3), file=save_file)
				print("L tierra (nHr): {0:10.2f}\n R tierra (mOhm):  {1:6.2n}\n L soporte (nHr): {2:10.3f}\n R soporte (mOhm):{3:6.1f}\n".format(Lt*1e9 ,Rt*1e3, Lsop*1e9, Rsop*1e3), file=save_file)

				save_file.write("\nTest results:\n")
				print("Ratio between DI03 y DI04(numeric, known): {0:6.4f}, {1:6.4f}\n".format(e,  DI04/DI03 ), file=save_file)
				print("Lsop values(one calc, other calc., ratio): {0:5.4e}, {1:5.4e}: {2:3.2f}\n".format(Lsop,  (f*DI03)/Krog , Lsop/((f*DI03)/Krog) ), file=save_file)
				print("Rsop:values(one calc, other calc., ratio):{0:5.4e}, {1:5.4e}:  {2:3.2f}\n".format(Rsop,  (g*DI03)/Krc,  Rsop / ( (g*DI03)/Krc ) ), file=save_file)
				
				save_file.close()

	#break #To perform tests on just one folder
	
#And tha...tha...that's all folks!
	
	


