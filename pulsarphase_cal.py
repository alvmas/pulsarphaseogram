
#####################
###Author: Alvaro Mas Aguilar (alvmas)
#mail: alvmas@ucm.es
#Using modules from PINT-pulsar and lstchain to calculate phases and add them to the input files.
#Modified by: Paula Molina Sanjurjo (Pau-mol)
#mail: p.molinasanjurjo@gmail.com
###################3


import pandas as pd
import csv
import os
import numpy as np
from astropy.time import Time
import pint
import astropy.units as u
from astropy.io import fits
from pint.observatory.satellite_obs import get_satellite_observatory
from lstchain.reco import dl1_to_dl2
import pint.toa as toa
import time
from lstchain.io import global_metadata, write_metadata, standard_config,srcdep_config 
from lstchain.io.io import dl2_params_src_dep_lstcam_key, write_dataframe, write_dl2_dataframe
from pint.fits_utils import read_fits_event_mjds
from pint.fermi_toas import *
from pint.scripts import *
from utils import  add_mjd,dl2time_totim, model_fromephem
import pint.models as models

__all__=['fermi_calphase','calphase']


def update_fermi(timelist,ephem,t):
    model=model_fromephem(timelist,ephem)

    #Upload TOAs and model
    m=models.get_model(model)

    #Calculate the phases
    print('Calculating barycentric time and absolute phase')
    bt=m.get_barycentric_toas(t)
    p=m.phase(t,abs_phase=True)
    
    return(bt,p)


def fermi_calphase(file,ephem,output_dir,pickle,ft2_file=None):
    
    '''
    Calculates barycentered times and pulsar phases from the DL2 dile using ephemeris. 

    Parameters:
    -----------------
    dl2file: string
    DL2 input file with the arrival times
    
    ephem: string
    Ephemeris to be used (.txt file or similar)
    
    
    output_dir:string
    Directory of the the output file
    
    pickle: boolean
    True if want to save a pickle file with the loaded TOAs
    
    
    '''
    print('Input file:'+str(file))
    #Load observatory and TOAs
    get_satellite_observatory("Fermi", ft2_file)
    tl=load_Fermi_TOAs(file,fermiobs='fermi')
    
    #Extract the timelist in mjd
    timelist=[]
    for i in range(0,len(tl)):
        timelist.append(tl[i].mjd.value)
        timelist=timelist.append(tl[i].mjd.value)

    #Create TOAs object
    t = toa.get_TOAs_list(tl)
    
    #Calculate the barycent_toas and phases in intervals of 1000 events so that ephemeris are updated
    barycent_toas=[]
    phase=[]
    k=0
    for i in range(10000,len(t),1000):
        b,p=update_fermi(timelist[k:i],ephem,t[k:i])
        barycent_toas=barycent_toas+list(b.value)
        phase=phase+list(p.frac.value)
        k=i
            
    b,p=update_fermi(timelist[k:],ephem,t[k:])
    barycent_toas=barycent_toas+list(b.value)
    phase=phase+list(p.frac.value)
               
    #Write if dir given
    hdul=fits.open(file)
    orig_cols = hdul[1].columns
    new_col1 = fits.Column(name='BARYCENTRIC_TIME', format='D',array=barycent_toas)
    new_col2 = fits.Column(name='PULSE_PHASE', format='D',array=phase)
    hdu = fits.BinTableHDU.from_columns(orig_cols + new_col1+new_col2)
            
    dir_output=output_dir+str(os.path.basename(file).replace('.fits',''))+'_pulsar.fits'
            
    print('Writing outputfile in'+str(dir_output))
    hdu.writeto(dir_output)
            
    print('Finished')


    
def calphase(file,ephem,output_dir,pickle=False):
    '''
    Calculates barycentered times and pulsar phases from the DL2 dile using ephemeris. 

    Parameters:
    -----------------
    dl2file: string
    DL2 input file with the arrival times
    
    ephem: string
    Ephemeris to be used (.txt file or similar)
    
    
    output_dir:string
    Directory of the the output file
    
    pickle: boolean
    True if want to save a pickle file with the loaded TOAs
    
    Returns:
    --------
    Returns same DL2 with two additional columns: 'mjd_barycenter_time' and 'pulsar_phase'
    The name of this new file is dl2.....run_number_ON_Crab_pulsar.h5
    
    '''

    dl2_params_lstcam_key='dl2/event/telescope/parameters/LST_LSTCam'

    #Read the file
    print('Input file:'+str(file))
    df_i=pd.read_hdf(file,key=dl2_params_lstcam_key,float_precision=20)
    add_mjd(df_i)

    try:     
        df_i_src=pd.read_hdf(file,key=dl2_params_src_dep_lstcam_key,float_precision=20)
        src_dep=True
    except:
        src_dep=False

    
    #Create the .tim file
    timelist=df_i.mjd_time.tolist()     
    timname=str(os.path.basename(file).replace('.h5',''))+'.tim'
    parname=str(os.path.basename(file).replace('.h5',''))+'.par'
    barycent_toas=get_phase_list(timname,timelist,ephem,parname,pickle)
    phase=phase
    os.remove(str(os.getcwd())+'/'+parname)         
    #Write if dir given
    if output_dir is not None:
        print('Generating new columns in DL2 DataFrame')
        df_i['mjd_barycenter_time']=barycent_toas
        df_i['pulsar_phase']=phase
        output_file=output_dir+str(os.path.basename(file).replace('.h5',''))+'_pulsar.h5'
        print('Writing outputfile in'+str(output_file))
        
        metadata = global_metadata()
        write_metadata(metadata, output_file)
        
        if src_dep==False:
            write_dl2_dataframe(df_i, output_file, meta=metadata)

        else:
            write_dl2_dataframe(df_i, output_file,meta=metadata)
            write_dataframe(df_i_src, output_file, dl2_params_src_dep_lstcam_key,meta=metadata)
            
        print('Finished')
 
    else:
        ('Finished. Not output directory given so the output is not saved')
        
        
def calphase_interpolated(file,ephem,output_dir,pickle=False,custom_config=None):
    '''
    Calculates barycentered times and pulsar phases from the DL2 dile using ephemeris. 

    Parameters:
    -----------------
    dl2file: string
    DL2 input file with the arrival times
    
    ephem: string
    Ephemeris to be used (.txt file or similar)
    
    
    output_dir:string
    Directory of the the output file
    
    pickle: boolean
    True if want to save a pickle file with the loaded TOAs
    
    Returns:
    --------
    Returns same DL2 with two additional columns: 'mjd_barycenter_time' and 'pulsar_phase'
    The name of this new file is dl2.....run_number_ON_Crab_pulsar.h5
    
    '''

    dl2_params_lstcam_key='dl2/event/telescope/parameters/LST_LSTCam'

    #Read the file
    print('Input file:'+str(file))
    df_i=pd.read_hdf(file,key=dl2_params_lstcam_key,float_precision=20)
    add_mjd(df_i)

    try:
        df_i_src=pd.read_hdf(file,key=dl2_params_src_dep_lstcam_key,float_precision=20)
        src_dep=True
        print('Using source-dependent analysis files')
    except:
        src_dep=False    
    
    #Create the .tim file
    timelist=df_i.mjd_time.tolist()   

    
    #Extraxting reference values of times for interpolation
    timelist_n=timelist[0::1000]
    if timelist_n[-1]!=timelist[-1]:
        timelist_n.append(timelist[-1])

    timname=str(os.path.basename(file).replace('.h5',''))+'.tim'
    parname=str(os.path.basename(file).replace('.h5',''))+'.par'
    
    #Time in seconds:
    timelist_s = np.array(timelist)*86400
    timelist_ns = np.array(timelist_n)*86400    
    
    #Calculate the barycent times and phases for reference
    barycent_toas_sample,phase_sample=get_phase_list(timname,timelist_n,ephem,parname,pickle)
    os.remove(str(os.getcwd())+'/'+parname)
    
    #Time of barycent_toas in seconds:
    btime_sample_sec = np.array(barycent_toas_sample)*86400  
  
    
    #Getting the period:
    colnames=['PSR', 'RAJ1','RAJ2','RAJ3', 'DECJ1','DECJ2','DECJ3', 'START', 'FINISH', 't0geo', 'F0', 'F1', 'F2', 'RMS','Observatory', 'EPHEM', 'PSR2']
    Ephem = pd.read_csv('Efemerides.txt', delimiter='\s+',names=colnames,header=None)
    Period = 1/Ephem['F0']
    P = np.mean(Period)
    
    #Number of complete cicles(N):    
    phase_sam = np.array(phase_sample.frac) + 0.5
    N=(1/P)*(np.diff(btime_sample_sec)-P*(1+np.diff(phase_sam)))    
    N=np.round(N)
    
    #For having the same dimensions:
    N = np.append([0], N)
   
    #The cumulative sum of N:
    sN=np.cumsum(N)
    
    #Sum of phases:
    sp = np.cumsum(phase_sam)
    #Sum of complementary phases shifted by 1:
    spc= np.append([0], np.cumsum(1-phase_sam)[:-1])
    
    #Adding sN + sp+ spc:
    phase_s = sp+sN+spc
    
    #Interpolate to all values of times:    
    barycent_toas = interpolate_btoas(timelist,timelist_n,barycent_toas_sample)
    barycent_toas_sec = np.array(barycent_toas)*86400
    phase=interpolate_phase(barycent_toas_sec,btime_sample_sec,phase_s)
    phase = phase%1
    phase = phase - 0.5

    #Write if dir given
    if output_dir is not None:
        print('Generating new columns in DL2 DataFrame')
        df_i['mjd_barycenter_time']=barycent_toas
        df_i['pulsar_phase']=phase
        
        output_file=output_dir+str(os.path.basename(file).replace('.h5',''))+'_pulsar.h5'
        print('Writing outputfile in'+str(output_file))

        metadata = global_metadata()
        write_metadata(metadata, output_file)
        
        if src_dep==False:
            if custom_config==None:
                config=standard_config
            else:
                config=custom_config
            write_dl2_dataframe(df_i, output_file, config=config, meta=metadata)

        else:
            if custom_config==None:
                config=srcdep_config
            else:
                config=custom_config
            write_dl2_dataframe(df_i, output_file,config=config,meta=metadata)
            write_dataframe(df_i_src, output_file, dl2_params_src_dep_lstcam_key,meta=metadata)

        print('Finished')

    else:
        ('Finished. Not output directory given so the output is not saved')

def interpolate_phase(timelist,time_sample,phase_s):
    from scipy.interpolate import interp1d

    print('Interpolating phase...')
    interp_function_phase=interp1d(time_sample, phase_s)
    
    phase=interp_function_phase(timelist)

    return(phase)

def interpolate_btoas(timelist,time_sample,barycent_toas_sample):
    from scipy.interpolate import interp1d

    print('Interpolating btoas...')
    interp_function_mjd = interp1d(time_sample, barycent_toas_sample)
    barycent_toas=interp_function_mjd(timelist)

    return(barycent_toas)    

def get_phase_list(timname,timelist,ephem,parname,pickle=False):
    print('Creating tim file')
    dl2time_totim(timelist,name=timname)
    print('creating TOA list')

    t= toa.get_TOAs(timname, usepickle=pickle)
    #Create model from ephemeris
    model=model_fromephem(timelist,ephem,parname)

    #Upload TOAs and model
    m=models.get_model(model)

    #Calculate the phases
    print('Calculating barycentric time and absolute phase')
    barycent_toas=m.get_barycentric_toas(t)
    phase=m.phase(t,abs_phase=True)
    
    os.remove(str(os.getcwd())+'/'+timname)
    
    return(barycent_toas,phase)
