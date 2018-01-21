# Tutorial: "A tour of Data Assimilation methods"
# Model: Lorenz-63
# DA Methods: Nudging, 3D-Var, 4D-Var, Particle Filter, EnKF, Hybrid
import numpy as np
from class_lorenz63 import lorenz63
from class_state_vector import state_vector
from class_obs_data import obs_data
from class_da_system import da_system
from copy import deepcopy

#-----------------------------------------------------------------------
# Read the da system object
#-----------------------------------------------------------------------
name = 'x_analysis'
infile = name+'_init.pkl'
das = da_system()
das = das.load(infile)

print(das)

#-----------------------------------------------------------------------
# Get the nature run trajectory
#-----------------------------------------------------------------------
sv = das.getStateVector()
x_nature = sv.getTrajectory()

#-----------------------------------------------------------------------
# Get the L63 observations via the obs_data object
#-----------------------------------------------------------------------
obs = das.getObsData()
y_obs = obs.getVal()
y_pts = obs.getPos()
y_err = obs.getErr()
print('y_obs = ')
print(y_obs[0,:])
print('y_pts = ')
print(y_pts[0,:])

#-----------------------------------------------------------------------
# Initialize the timesteps
#-----------------------------------------------------------------------
t_nature = sv.getTimes()
acyc_step = das.acyc_step  # (how frequently to perform an analysis)
dtau = das.dtau
dt = das.dt
fcst_step= das.fcst_step
fcst_dt = das.fcst_dt
maxit = das.maxit
xdim = das.xdim
ydim = das.ydim

#-----------------------------------------------------------------------
# Initialize the model
#-----------------------------------------------------------------------
l63 = lorenz63()

#-----------------------------------------------------------------------
# Choose DA method:
#-----------------------------------------------------------------------

method = das.getMethod()  # (use default)

#-----------
# Test basic functionality
#-----------
#method='skip'

#-----------
# 3D methods
#-----------
# Nudging
#method='nudging'
# OI
#method='OI'
# 3D-Var
#method='3DVar'

#das.setMethod(method)

#-----------------------------------------------------------------------
# Conduct data assimilation process
#-----------------------------------------------------------------------
#
xa = sv.x0
xa_history = np.zeros_like(x_nature)
KH_history = []
for i in range(0,maxit-acyc_step,acyc_step):
 
  #----------------------------------------------
  # Run forecast model for this analysis cycle:
  #----------------------------------------------
  t = np.arange(t_nature[i],t_nature[i+acyc_step]+dt,dt)
# print('t = ', t)
# print('t_nature[i+acyc_step] = ', t_nature[i+acyc_step])

  # Run the model
  xf_4d =  l63.run(xa,t) 
  # Get last timestep of the forecast
  xf = xf_4d[-1,:] 

  #----------------------------------------------
  # Get the observations for this analysis cycle
  #----------------------------------------------
  yo = y_obs[i+acyc_step,:]
  yp = y_pts[i+acyc_step,:]

# if (len(yp) < xdim): 
#   das.reduceYdim(yp)
 
  #----------------------------------------------
  # Compute analysis
  #----------------------------------------------
  xa, KH = das.compute_analysis(xf,yo)
# print('xa = ')
# print(xa)
# print('KH = ')
# print(KH)

  # Archive the analysis
  xa_history[i+acyc_step,:] = xa
  # Fill in the missing timesteps with the forecast from the previous analysis IC's
  xa_history[i:i+acyc_step,:] = xf_4d[0:acyc_step,:]

# print('xa_history[i:i+acyc_step+1,:] = ', xa_history[i:i+acyc_step+1,:])

  # Archive the KH matrix
  KH_history.append(deepcopy(KH))
 
#--------------------------------------------------------------------------------
# Fill in unobserved dimensions (for plotting)
#--------------------------------------------------------------------------------
#fillValue=0.0
#obs.fillDim(fillValue)
#das.setObsData(obs)

sv.setTrajectory(xa_history)
sv.setName(name)
das.setStateVector(sv)

outfile=name+'_'+method+'.pkl'
das.save(outfile)

print(das)