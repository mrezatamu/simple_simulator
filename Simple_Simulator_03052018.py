import os, subprocess, sys, random
import numpy as np
from random import randint
import math
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import time


#===============================================================================
### Set values
batch_size = 1              ### number of random simulations 
numLanes = 1     
numRamps = 0
segLength = 40000           ### feet
deltaT = 0.5
totalTime = 120             ### Total Simulation Time 
figure_number = 0
WTRatio = 1                 ### Portion of analysis period to include the waves
totalCars = 730
AWDuration = 15             ### Mean of stop duration (seconds)
S_AWDuration = 5            ### SD of stop duration (seconds)
initial_distance = 100      ### Average Vehicles' initial distance from each other
S_initial_distance = 30     ### SD of Vehicles' initial distance from each other
min_n_waves = 60            ### Minimum number of waves
max_n_waves = 100           ### Maximum number of waves
FFS = 30                    ### Fre flow speed
pixel_s = 15                 ### Pixel space width (ft) used in pixel-based time-space diagram 
pixel_t = deltaT               ### Pixel time width  (sec) used in pixel-based time-space diagram

## IDM parameters
Tgap = 0.1              ### Time gap, in seconds
aMax = 3.281            ### max acceleration, in ft/s2
b = 4.92                ### comfortable braking deceleration, in ft/s2
so = 6.56               ### jam distance, in feet
s = 0                   ### Gap, in feet
sDyn = 0                ### Desired Dynamic Distance, s*, in feet
vehLen = 20             ### Length of vehicle, in feet, typically 20 feet
aMaxII = 2.5            ### additional max acceleration
bII = 5.0               ### additional comfortable deceleration

## IDM Random parameters range
Tgap_min = 0.1          ### lower bound on Time gap, in seconds
Tgap_max = 2.0          ### upper bound on Time gap, in seconds
aMax_min = 2.50         ### lower bound on max acceleration, in ft/s2
aMax_max = 3.50         ### upper bound on max acceleration, in ft/s2
b_min = 4.00            ### lower bound on comfortable braking deceleration, in ft/s2
b_max = 8.00            ### Upper bound on comfortable braking deceleration, in ft/s2

#===============================================================================

# class car:
#     def __init__(self, i):
#         self.position = []
#         self.time = []
#         self.speed = []
#         self.acc = []
#         self.pixel = []

def rows(x_0, x_1, row_width):
    num_rows = math.ceil(x_1/row_width)-math.floor(x_0/row_width)
    row_numbers = []
    li_rows = []
    if num_rows == 1:
        row_numbers = [math.floor(x_0/row_width)]
        li_rows = [x_1-x_0]
    elif num_rows == 2:
        row_numbers = [math.floor(x_0/row_width), math.floor(x_0/row_width)+1]
        li_rows = [row_width-x_0%row_width, x_1%row_width]
    else:
        row_numbers = [i+math.floor(x_0/row_width) for i in range(num_rows)]
        li_rows = [row_width-x_0%row_width]
        for i in range(num_rows-2):
                li_rows.append(row_width)
        li_rows.append(x_1%row_width)  
    result = [row_numbers, li_rows]
    return(result)


def rows(x_0, x_1, column_width):
    n_rows = math.ceil(x_1/column_width)-math.floor(x_0/column_width)
    row_numbers = []
    li_rows = []
    if n_rows == 1:
        row_numbers = [math.floor(x_0/column_width)]
        li_rows = [x_1-x_0]
    elif n_rows == 2:
        row_numbers = [math.floor(x_0/column_width), math.floor(x_0/column_width)+1]
        li_rows = [column_width-x_0%column_width, x_1%column_width]
    else:
        row_numbers = [i+math.floor(x_0/column_width) for i in range(n_rows)]
        li_rows = [column_width-x_0%column_width]
        for i in range(n_rows-2):
                li_rows.append(column_width)
        li_rows.append(x_1%column_width)  
    result = [row_numbers, li_rows]
    return(result)



#===============================================================================
###START
 
while figure_number < batch_size:
    
    rand_name = str(str(time.strftime("%Y%m%d-%H%M%S"))+'-'+str(randint(1,1000000)))
    #=======================================================================
    ##Density and Flow blocks
    s_width=1000    ### Width in space (feet)
    t_width = 60    ### Width in time (sec.)
    n_columns = math.floor(totalTime/t_width)
    n_rows = math.floor(segLength/s_width)
    
    ##For each block in time and space, we calculate the average density and flow based on the Eddie's definition
    #sigma_ti is the matrix of summation of times that vehicles spend in each block
    #sigma_li is the matrix of summation of lemgth that vehicles spend in each block
    sigma_ti = [[0.0 for j in range(n_columns)] for i in range(n_rows)]
    sigma_ti = np.array(sigma_ti)
    sigma_li = [[0.0 for j in range(n_columns)] for i in range(n_rows)]
    sigma_li = np.array(sigma_li)
    #=======================================================================
    
    #=======================================================================
    ### Set values
    time = 0
    
    ### Random paramters and parameters of random models
#     FFS = random.choice([30, 45, 60])            ### mph
    waves = randint(min_n_waves, max_n_waves)      ### Number of cars simulating waves
    w_dec = random.uniform(-2.5, -1.5)             ###Intensity of decelaration for shockwaves (ft/s2)
    
    ### Note 1: All cars will start traveling at v = FFS mph
    ### Note 2: Car 1 will start at location x = 0 feet
    ### Note 3: Car 2 will start at some distance behind that e.g. x = -100 feet
    ### 

    ##IDM Random Parameters:
    vo = FFS                 ### desired speed, in mph
    listTgap = list([0] * totalCars)
    listaMax = list([0] * totalCars)
    listb = list([0] * totalCars)
    for i in range(totalCars):
      listTgap[i] = random.uniform(Tgap_min, Tgap_max) 
      listaMax[i] = random.uniform(aMax_min, aMax_max)
      listb[i] = random.uniform(b_min, b_max)
    #=======================================================================

    #=======================================================================
    ## Initialization
    ## Selecting the cars that will cause a shockwave and time of the shockwaves
    WCars = []  ##List of the index number of the cars causing the shockwave
    StopTimes = list([0] * totalCars) ## Time periods that the cars stop 
    CWP = math.floor(totalCars/waves)
    TWP = math.floor(WTRatio*totalTime/waves)
    WPList = []
    TPList = []

    for i in range(waves):
        WPList.append([i*CWP+1, (i+1)*CWP])

    for i in range(waves):
        rand_car = randint(WPList[i][0], WPList[i][1])
        WCars.append(rand_car)
        rand_time = randint(2, totalTime)
        stop_duration = abs(np.random.normal(AWDuration, S_AWDuration))
        StopTimes[rand_car] = [rand_time, rand_time + stop_duration]
    
#     print("WCars: ")
#     print(WCars)
#     print(" ")
#     print("StopTimes: ")
#     print(StopTimes)
#     print(" ")
    
    ### Save data lists
    results = [[] for i in range(totalCars)]
#     car_results = [ car(i) for i in range(totalCars)]
    ###
    
    ## Second, create a list of their initial positions...
    
    listPos = list([0] * totalCars)
    listDet = list([1] * totalCars)

    for i, item in enumerate(listPos):
        if i == 0:
            listPos[i] = segLength
        else:
            listPos[i] = listPos[i-1] - max((np.random.normal(initial_distance, S_initial_distance)), 100)
#     print("Position of vehicles (feet): ")
#     print(listPos)
#     print(" ")

    ## If they are all traveling at 80 mph, 
    ## then will travel 294 feet every 2.5 secs
    ## or 117 feet every second. 
    
    ## ...and their initial speeds
    
    listSpeed = list([FFS] * totalCars)
    # print("Speed of vehicles (mph)")
    # print (listSpeed)
    # print (" ")
    
    listAccel = list([0] * totalCars)
    # print("Acceleration of vehicles (fps)")
    # print (listAccel)
    # print (" ")
    
    #=======================================================================
    
    t_s_mat_row = round(segLength/pixel_s)
    t_s_mat_col = round(totalTime/pixel_t)
    time_space_matrix = np.array([[100 for j in range(t_s_mat_col)] for i in range(t_s_mat_row)])
    
    x_0 = 0
    x_1 = 0
    while time < totalTime:
#         print("============================")
#         print("Time is: ", time)

        if time != 0:
            column = math.floor((time-deltaT)/t_width)
        else:
            column = 0
        
        for i in range(totalCars):
            
            x_0 = listPos[i]
# # #             i_p_old = -1
# # #             if round(listPos[i]/pixel_s) in range(t_s_mat_row):
# # #                 i_p_old = int(t_s_mat_row - round(listPos[i]/pixel_s))
            
            listSpeed[i] = listSpeed[i] + (listAccel[i] * deltaT * 0.6818182)
            if listSpeed[i] < 0:
                listSpeed[i] = 0
        
            if time == 0:
                listPos[i] = listPos[i]
            else:
                listPos[i] = listPos[i] + (listSpeed[i] * deltaT * 1.47) + (0.5 * listAccel[i] * pow(deltaT,2))
            
            #Updating the sigma time and sigma length 
            x_1 = listPos[i]
            delta_xi = rows(x_0,x_1,s_width)

            for j in range(len(delta_xi[0])):
                if delta_xi[0][j] in range(n_rows):
                    sigma_li[delta_xi[0][j]][column] = sigma_li[delta_xi[0][j]][column] + delta_xi[1][j]
                    sigma_ti[delta_xi[0][j]][column] = sigma_ti[delta_xi[0][j]][column] + deltaT
            
            #===================================================================            
            #Updating the time_space_matrix:
            i_p = t_s_mat_row - int(round(listPos[i]/pixel_s))
            j_p = int(round(time/pixel_t))
            if i_p in range(t_s_mat_row) and j_p in range(t_s_mat_col):
                time_space_matrix[i_p][j_p] = 0
# # #             ## approximately connecting the points:
# # #             if i_p_old > 0 and j_p-1 > 0:
# # #                 delta = i_p_old - i_p
# # #                 if delta > 1:
# # #                     i_n = i_p_old - 1
# # #                     while i_n >= i_p_old - delta/2:
# # #                         time_space_matrix[i_n][(j_p-1)] = 0
# # #                         i_n -= 1
# # #                     while i_n >= i_p:
# # #                         time_space_matrix[i_n][j_p] = 0
# # #                         mreza.append([i_n, j_p])
# # #                         i_n -= 1
            #===================================================================

            if listDet[i] == 1:
                sDyn = so + max(0, (listTgap[i] * listSpeed[i] * 1.47) + (((listSpeed[i] * 1.47) * (1.47 * (listSpeed[i] - listSpeed[i-1])))/ (2 * np.sqrt(listaMax[i] * listb[i])))) 
    
                if i in WCars:
                    if time >= StopTimes[i][0] and time <= StopTimes[i][1]:
                        listAccel[i] = w_dec
                        if listSpeed[i] <= 0:
                            listAccel[i] = 0
                    else:
                        listAccel[i] = listaMax[i] * (1 - pow((listSpeed[i]/vo),4) - pow(sDyn/(listPos[i-1] - listPos[i] - vehLen),2))
                else:
                    listAccel[i] = listaMax[i] * (1 - pow((listSpeed[i]/vo),4) - pow(sDyn/(listPos[i-1] - listPos[i] - vehLen),2))
    
            results[i].append([time, listSpeed[i], listPos[i], listAccel[i]])
#             car_results[i].position.append(listPos[i])
#             car_results[i].speed.append(listSpeed[i])
#             car_results[i].acc.append(listAccel[i])
#             car_results[i].time.append(time)

        time = time + deltaT
        
#========================================================================================================
    ## Estimating the densities and flow for each block:
    Density = sigma_ti/(s_width*t_width/5280)
    Flow = sigma_li/(s_width*t_width/3600)
    np.savetxt('./Density_'+str(figure_number)+rand_name, Density)
    np.savetxt('./Flow_'+str(figure_number)+rand_name, Flow)
#========================================================================================================

#     plt.imshow(time_space_matrix)
#     plt.savefig('./Trajectory_'+str(figure_number)+rand_name+'.png', bbox_inches='tight', pad_inches = 0)

#     im = Imaage.fromarray(time_space_matrix)
#     im.save('./Trajectory_'+str(figure_number)+rand_name+'.png')
#     im.show()
    
    plt.gray()
    plt.imshow(time_space_matrix)
    plt.savefig('./Trajectory_'+str(figure_number)+rand_name+'.png')



#========================================================================================================
    ## Plotting the trajectories:
    fig = plt.figure()
    results = np.array(results)
    print (np.shape(results))
     
    for i, vehicle in enumerate(results):
        time = []
        location = []
        time = [i[0] for i in vehicle]
        location = [i[2]/100 for i in vehicle]
        if (listDet[i] == 1): ##IDM
#             plt.plot(time, location, linewidth=0.3, linestyle="-", c='maroon')
            plt.plot(time, location, linewidth=0.3)
       
#     for i in range(totalCars):
#         plt.plot(car_results[i].time, car_results[i].position, linewidth=0.3)
 
    plt.ylim(0, segLength/100)
    plt.xlim(0, totalTime)
    plt.axis('off')
#     plt.xticks(fontsize=16)
#     plt.yticks(fontsize=16)
#     plt.ylabel(r'$Location (100 ft)$', fontsize=20)
#     plt.xlabel(r'$Time (s)$', fontsize=20)
     
    fig.set_size_inches(18, 8)
    fig.tight_layout()
    plt.savefig('./Trajectory_2_'+str(figure_number)+rand_name+'.jpeg', bbox_inches='tight', pad_inches = 0)
    plt.close()
     
#==========================================================================================================
    IDM_param = np.array([listTgap, listaMax, listb])
    np.savetxt('./IDM_par_'+str(figure_number)+rand_name, IDM_param)
    


# #     IDM_out = open('IDM_par_'+str(figure_number)+'.txt', 'w')
# #     IDM_out.write('listTgap: '+'\n')
# #     IDM_out.write(str(listTgap)+'\n')
# #     IDM_out.write('listaMax: '+'\n')
# #     IDM_out.write(str(listaMax)+'\n')
# #     IDM_out.write('listb: '+'\n')
# #     IDM_out.write(str(listb))    
# #     IDM_out.close()
    
#     result_out = open('result_'+str(figure_number)+'.txt', 'w')
#     result_out.write('[time, listSpeed[i], listPos[i], listAccel[i]]'+'\n')
#     for i in range(totalCars):
#         result_out.write('Car: '+str(i)+'\n')
#         for j in range(len(results)):
#             result_out.write(str(results[j][i])+'\n')
#     result_out.close()
    
    figure_number = figure_number + 1
    

