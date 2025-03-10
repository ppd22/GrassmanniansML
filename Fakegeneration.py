'''SSYT fake data generation - to run on the hpc (bottleneck is the data loading and checking against loaded data - so not worth parallelising)'''
'''
Run the cells sequentially, or the first 3 together on a hpc.
Cell 1 ==> import necessary libraries, then import and reformat the dataset to model fake data for.
Cell 2 ==> generate the fake data (fitting the same distribution as the real data), ensuring the SSYT condition is met, and there are no repeats of real data or within the fake data.
Cell 3 ==> save the fake data to an output file.
Cell 4 ==> checking system to ensure the SSYT condition holds.
'''
### Cell 1 ###
#Import libraries
import numpy as np
from ast import literal_eval as LE

#Set params
G_choice = 0        #...select the indices of the filepath to import data from (i.e. choose the data to import): {0,1,2} = {Gr(3,12)r6, Gr(4,10)r6, Gr(4,12)r4}
fake_size = 10000   #...select how many fake SSYTs to make
resample_freq = 6   #...choose how frequently to resample entries ~ 1/resample_size (note only updates the middle)

#Import data
Datafiles = ['../FinalData/SmallRank6ModulesGr312.txt','../FinalData/SmallRank6ModulesGr410.txt','../FinalData/SmallRank4ModulesGr412.txt']
prefixes = [f[-7:-4] for f in Datafiles]
n, k, max_r = int(prefixes[G_choice][0]), int(prefixes[G_choice][1:]), int(Datafiles[G_choice][-17]) #...entries of Gr(n,k) & rank --> number of rows, max entry, and max number of columns respectively

Data = []
with open(Datafiles[G_choice],'r') as file:
    for line in file.readlines():
        Data.append(LE(line))
print('Dataset sizes: '+str(len(Data)))
del(file,line)

#Extract data info
max_height = max(map(len,Data)) 
max_width  = max(map(len,[tab[0] for tab in Data])) #...all tableaux rows the same length so can just consider first row

#Pad data (all datasets to the same size)
for tab_idx in range(len(Data)):
    tab = np.array(Data[tab_idx])
    new_tab = np.zeros((max_height,max_width),dtype=int)
    new_tab[:len(tab),:len(tab[0])] = tab
    Data[tab_idx] = new_tab
Data = np.array(Data)
del(tab_idx,tab,new_tab)

#%% ### Cell 2 ###
#Generate the fake data
Fake = []

while len(Fake) < fake_size:
    r=np.random.choice(range(1,max_r+1)) #...randomly select the rank of the SSYT (i.e. number of columns)
    trial = np.sort(np.random.choice(range(1,k+1),n*r)).reshape(n,r) #..start with a sorted array st the condition of \geq to the right automatically satisfied
    skip = False #...boolean to check for uncorrectable SSYT (skip where they occur and generate a new one)
        
    #Check & mutate the SSYT
    if r > 1:        
        #Loop through the entries and check < below, and randomly resample some
        for i in range(1,n-1): #...dont need to check first or last row
            #First column
            if not trial[i-1,0] < trial[i,0] < trial[i+1,0]: 
                if min(trial[i+1][0],trial[i][1]+1)-trial[i-1,0] < 2: #...skip those wthout enough gap to update
                    skip = True
                    continue
                trial[i,0] = np.random.randint(trial[i-1][0]+1,min(trial[i+1][0],trial[i][1]+1))
            elif np.random.randint(resample_freq) == 0: #...randomly resample
                trial[i,0] = np.random.randint(trial[i-1][0]+1,min(trial[i+1][0],trial[i][1]+1))
            
            #Middle columns
            for j in range(1,r-1): 
                if not trial[i-1,j] < trial[i,j] < trial[i+1,j]: 
                    if min(trial[i+1][j],trial[i][j+1]+1)-max(trial[i-1][j]+1,trial[i][j-1]) < 2: #...skip those wthout enough gap to update
                        skip = True
                        continue
                    trial[i,j] = np.random.randint(max(trial[i-1][j]+1,trial[i][j-1]),min(trial[i+1][j],trial[i][j+1]+1))
                elif np.random.randint(resample_freq) == 0: #...randomly resample 
                    trial[i,j] = np.random.randint(max(trial[i-1][j]+1,trial[i][j-1]),min(trial[i+1][j],trial[i][j+1]+1))
            
            #Last column
            if not trial[i-1,-1] < trial[i,-1] < trial[i+1,-1]: 
                if trial[i+1,-1]-max(trial[i-1][-1]+1,trial[i][-2]) < 2: #...skip those wthout enough gap to update
                    skip = True
                    continue
                trial[i,-1] = np.random.randint(max(trial[i-1][-1]+1,trial[i][-2]),trial[i+1][-1])
            elif np.random.randint(resample_freq) == 0: #...randomly resample
                trial[i,-1] = np.random.randint(max(trial[i-1][-1]+1,trial[i][-2]),trial[i+1][-1])
        
    #Special case when there is only 1 column (rank 1)
    else: 
        for i in range(1,n-1): #don't need to check first or last row
            if not trial[i-1,0] < trial[i,0] < trial[i+1,0]: 
                if trial[i+1,0]-trial[i-1,0] < 2: #...skip those wthout enough gap to update
                    skip = True
                    continue
                trial[i,0] = np.random.randint(trial[i-1][0]+1,trial[i+1][0])
            elif np.random.randint(resample_freq) == 0: #...randomly resample 
                trial[i,0] = np.random.randint(trial[i-1][0]+1,trial[i+1][0])
        
    #Skip if uncorrectable
    if skip: continue

    #Pad the trial SSYT
    new_tab = np.zeros((4,6),dtype=int) #...hard code to standard form, otherwise: np.zeros((max_height,max_width),dtype=int)
    new_tab[:len(trial),:len(trial[0])] = trial
    trial = np.array(new_tab)
        
    #Check not in the real data
    for tab in Data:
        if np.array_equal(trial,tab): 
            skip = True
            break
    if skip: continue
    #print('Data pass')
    #Check not already generated
    for tab in Fake:
        if np.array_equal(trial,tab): 
            skip = True
            break
    if skip: continue
    #print('New pass\n\n##############\n')
    
    #All tests passed, so add to the list
    Fake.append(trial)
    print('Progress...',len(Fake))
    
    #Save data at regular intervals
    if len(Fake)%500==0:
        with open('./Fake'+str(prefixes[G_choice])+'_'+str(fake_size)+'.txt','w') as file:
            file.write(str(Fake))
        del(file)
            
del(i,j,r,tab,new_tab,trial)


#%% ### Cell 3 ###
#Save the fake data
with open('./Fake'+str(prefixes[G_choice])+'_'+str(fake_size)+'.txt','w') as file:
    file.write(str(Fake))
del(file)    

#%% ### Cell 4 ###
#Check fake data for generation errors
Fake = np.array(Fake,dtype=int)
error_r, error_c = [], []
for tab in Fake:
    #Check the vertical condition (always <)
    for r in range(1,len(tab)-1):
        for c in range(len(tab[0])):
            if tab[r][c] != 0 and tab[r+1][c] != 0:
                if not tab[r+1][c] > tab[r][c] > tab[r-1][c]:
                    error_r.append(tab)
    #Check the horizontal condition (always <=) --> never a problem here
    for r in range(len(tab)):
        for c in range(1,len(tab[0])-1):
            if tab[r][c] != 0 and tab[r][c+1] != 0:
                if not tab[r][c-1] <= tab[r][c] <= tab[r][c+1]:
                    error_c.append(tab)
print('Errors:',len(error_r),len(error_c))
