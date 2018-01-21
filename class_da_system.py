import numpy as np
import scipy as sp
from class_state_vector import state_vector
from class_obs_data import obs_data
import numpy.matlib
import pickle

class da_system:

  def __init__(self,x0=[],yo=[],t0=0,dt=0,alpha=0.5,state_vector=[],obs_data=[],acyc_step=10):
    self.xdim = np.size(x0)
    self.ydim = np.size(yo)
    self.edim = 1
    self.x0 = x0
    self.t0 = t0
    self.dt = dt
    self.X0 = x0
    self.t = t0
    self.acyc_step = acyc_step
    self.dtau = dt*acyc_step
    self.fcst_step = acyc_step
    self.fcst_dt = dt
    self.maxit = 0
    self.B = np.matrix(np.identity(self.xdim))
    self.R = np.matrix(np.identity(self.ydim))
    self.H = np.matrix(np.identity(self.xdim))
    self.Ht = (self.H).transpose()
    self.alpha = alpha
    self.SqrtB = []
    self.state_vector = state_vector
    self.obs_data = obs_data

  def __str__(self):
    print('xdim = ', self.xdim)
    print('ydim = ', self.ydim)
    print('x0 = ', self.x0)
    print('t0 = ', self.t0)
    print('dt = ', self.dt)
    print('t  = ', self.t)
    print('acyc_step = ', self.acyc_step)
    print('dtau = ', self.dtau)
    print('fcst_step = ', self.fcst_step)
    print('fcst_dt  = ', self.fcst_dt)
    print('B = ')
    print(self.B)
    print('R = ')
    print(self.R)
    print('H = ')
    print(self.H)
    print('state_vector = ')
    print(self.state_vector)
    print('obs_data = ')
    print(obs_data)
    return 'type::da_system'

  def setMethod(self,method):
    self.method = method

  def getMethod(self):
    return self.method

  def setStateVector(self,sv):
    self.state_vector = sv

  def setObsData(self,obs):
    self.obs_data = obs

  def getStateVector(self):
    return self.state_vector

  def getObsData(self):
    return self.obs_data

  def update(self,B=[0],R=[0],H=[0],t=[0],x0=[0]):
    # Update the state of the DA system for a new cycle
    self.B = B
    self.R = R
    self.H = H
    self.Ht = H.Transpose()
    self.t = t
    self.x0 = x0

  def getB(self):
    return self.B

  def setB(self,B):
    self.B = np.matrix(B)
    nr,nc = np.shape(B)
    self.xdim = nr
    self.SqrtB = sp.linalg.sqrtm(self.B)

  def setSqrtB(self,X):
    self.SqrtB = np.matrix(X)
    self.B = self.SqrtB*self.SqrtB.T
    nr,nc = np.shape(X)
    self.xdim = nr
    self.edim = nc

  def getR(self):
    return self.R

  def setR(self,R):
    self.R = np.matrix(R)
#   nr,nc = np.shape(R)
#   self.ydim = nr
    self.Rinv = np.linalg.inv(R)

  def getH(self):
    return self.H

  def setH(self,H):
    self.H = np.matrix(H)
    self.Ht = np.transpose(self.H)
#   nr,nc = np.shape(H)

    # Verify that H is ydim x xdim
#   if (nr != self.ydim):
#     error('H must be ydim x xdim, but instead H is %d x %d'%(nr,nc))
#   if (nc != self.xdim):
#     error('H must be ydim x xdim, but instead H is %d x %d'%(nr,nc))

  def reduceYdim(self,yp):
#   print('reduceYdim:')
#   print('yp = ', yp)
    self.ydim = len(yp)
    self.setH(self.H[yp,:])
    self.setR(self.R[yp,yp])

  def compute_analysis(self,xb,yo,params=[0]):
    # (params needed for 4D-Var)
    method = self.method
    if method == 'skip':
      xa = xb 
      KH = np.identity(self.xdim)
    elif method == 'nudging':
      xa,KH = self.nudging(xb,yo)
    elif method == 'OI':
      xa,KH = self.OI(xb,yo)
    elif method == '3DVar' or method == '3D-Var':
      xa,KH = self._3DVar(xb,yo) 
    elif method == 'ETKF' or method == 'EnKF':
      xa,KH = self.ETKF(xb,yo)
    elif method == 'PF':
      xa,KH = self.PF(xb,yo)
    elif method == 'Hybrid':
      xa,KH = self.HybridGain(xb,yo) 
#   elif method == '4DVar' or method == '4D-Var':
#     xa,KH = self._4DVar(xb,yo)
#   elif method == '4DEnVar':
#     xa,KH = self._4DEnVar(xb,yo)
#   elif method == '4DETKF':
#     xa,KH = self._4DETKF(xb,yo) 
    else:
      print('compute_analysis:: Unrecognized DA method.')
      raise SystemExit
    return xa,KH

  def initEns(self,x0,mu=0,sigma=0.1,edim=4):
    xdim = len(x0)
    x0 = np.matrix(x0).flatten().T
    mu = np.matrix(mu).flatten().T
    Xrand = np.random.normal(0,sigma,(xdim,edim))
    Xrand = np.matrix(Xrand)
#   print('Xrand = ')
#   print(Xrand)
    # Remove mean to make sure it is properly centered at 0
    # (add bias if included)
    rand_mean = np.mean(Xrand,axis=1) + mu
#   print('rand_mean = ')
#   print(rand_mean)
    rmat = np.matlib.repmat(rand_mean,1,edim)
    Xrand = Xrand - rmat
#   print('xrand = ')
#   print(xrand)
    # add perturbations to x0
    rmat = np.matlib.repmat(x0, 1, edim)
#   print('rmat = ')
#   print(rmat)
    X0 = np.matrix(rmat + Xrand)
    return X0

# def init4D(self):
#   xdim = size(self.x0)

# def init4DEns(self):
#   xdim = size(self.x0)

#---------------------------------------------------------------------------------------------------
  def nudging(self,xb,yo):
#---------------------------------------------------------------------------------------------------
# Use observations at predefined points to drive the model system to the observed nature system

    xb = np.matrix(xb).flatten().T
    yo = np.matrix(yo).flatten().T

    const = np.diagonal(self.B)

    xa = xb + const*(yo - xb) 

    C = np.diag(const)
    Hl = self.H
    Ht = self.Ht
    KH = Ht*C*Hl

    return xa.A1,KH
        
#---------------------------------------------------------------------------------------------------
  def OI(self,xb,yo):
#---------------------------------------------------------------------------------------------------
    xb = np.matrix(xb).flatten().T
    yo = np.matrix(yo).flatten().T

    # Use explicit expression to solve for the analysis
#   print(self)
    Hl = self.H
    Ht = self.Ht
    B = self.B
    R = self.R

#   print('H = ')
#   print(Hl)

#   print('R = ')
#   print(R)

    # Should be dimensioned: xdim * xdim
    K = B*Ht*np.linalg.inv(Hl*B*Ht + R)
    KH = K*Hl

#   print('KH = ')
#   print(KH)

    Hxb = Hl*xb
    xa = xb + K*(yo - Hxb)

    return xa.A1, KH


#---------------------------------------------------------------------------------------------------
  def _3DVar(self,xb,yo):
#---------------------------------------------------------------------------------------------------
# Use minimization algorithm to solve for the analysis

    # make inputs column vectors
    xb = np.matrix(xb).flatten().T
    yo = np.matrix(yo).flatten().T

    # Set parameters
    xdim = self.xdim
    Hl = self.H
    Ht = self.Ht
    B = self.B
    R = self.R
    Rinv = np.linalg.inv(R)

    # 'preconditioning with B'
    I = np.identity(xdim)
    BHt = B*Ht
    BHtRinv = BHt*Rinv
    A = I + BHtRinv*Hl
    b1 = xb + BHtRinv*yo

    # Use minimization algorithm to minimize cost function:
    xa,ierr = sp.sparse.linalg.cg(A,b1,x0=xb,tol=1e-05,maxiter=1000) 
#   xa,ierr = sp.sparse.linalg.bicgstab(A,b1,x0=np.zeros_like(b1),tol=1e-05,maxiter=1000)
#   try: gmres, 

    # Compute KH:
    HBHtPlusR_inv = np.linalg.inv(Hl*BHt + R)
    KH = BHt*HBHtPlusR_inv*Hl

    return xa, KH


#---------------------------------------------------------------------------------------------------
  def ETKF(self,Xb,yo):
#---------------------------------------------------------------------------------------------------
# Use ensemble of states to estimate background error covariance

    # Make sure inputs are matrix and column vector types
    Xb = np.matrix(Xb)
    yo = np.matrix(yo).flatten().T

    # Get system dimensions
    nr,nc = np.shape(Xb)
    xdim = nr  # == self.xdim
    edim = nc
    ydim = len(yo)

    # Apply observation operator to forecast ensemble
    Hl = self.H
    Yb = np.matrix(np.zeros([ydim,edim]))
    for i in range(edim):
      Yb[:,i] = Hl*Xb[:,i]
    
    # Convert ensemble members to perturbations
    xm = np.mean(Xb,axis=1)
    Xb = Xb - np.matlib.repmat(xm, 1, edim)
    ym = np.mean(Yb,axis=1)
    Yb = Yb - np.matlib.repmat(ym, 1, edim)

    # Compute R^{-1}
    R = self.R
    Rinv = np.linalg.inv(R)

    # Compute the weights
    Ybt = Yb.T
    C = Ybt*Rinv

    I = np.identity(edim)
    rho = 1.0
    eigArg = (edim-1)*I/rho + C*Yb
    lamda,P = np.linalg.eigh(eigArg)
    Linv = np.diag(1.0/lamda)
    PLinv = P*Linv
    Pt = P.T
    Pa = PLinv*Pt

    Linvsqrt = np.diag(1/np.sqrt(lamda))
    PLinvsqrt = P*Linvsqrt
    Wa = np.sqrt(edim-1) * PLinvsqrt*Pt

    d = yo - ym
    wm = Pa*(C*d)
    Wa = Wa + np.matlib.repmat(wm, 1, edim)

    # Add the same mean vector wm to each column
    Xa = Xb*Wa + np.matlib.repmat(xm, 1, edim)

    # Compute KH:
    IpYbtRinvYb = ((edim-1)/rho)*I + Ybt*Rinv*Yb
    IpYbtRinvYb_inv = IpYbtRinvYb.I
    K = Xb*IpYbtRinvYb_inv*Ybt*Rinv
    KH = K*Hl
    
    return Xa, KH


#---------------------------------------------------------------------------------------------------
# def _4DVar(self,xb_4d,yo_4d):
#---------------------------------------------------------------------------------------------------
# Use minimization over a time window to solve for the analysis
#   
#   xb_4d = np.matrix(np.atleast_2d(xb_4d))
#   yo_4d = np.matrix(np.atleast_2d(yo_4d))
#   nr,nc = np.shape(xb_4d)     ! columns are state vectors at consecutive timesteps
#   xdim = nr
#   tdim = nc
#   B = self.B
#   R_4d = self.R               ! may need list of R matrices if observations are non-uniform over time
#   H_4d = self.H               ! may need list of H matrices if observations are non-uniform over time
#   M_4d = self.M               ! input list of TLMs for each timestep


#---------------------------------------------------------------------------------------------------
# def _4DEnVar(self,Xb_4d,yo_4d):
#---------------------------------------------------------------------------------------------------
# Use ensemble of states over a time window to estimate temporal correlations


#---------------------------------------------------------------------------------------------------
# def _4DETKF(self,Xb_4d,yo_4d):
#---------------------------------------------------------------------------------------------------
# Use ensemble of states over a time window to estimate temporal correlations


#---------------------------------------------------------------------------------------------------
  def PF(self,Xb,yo):
#---------------------------------------------------------------------------------------------------
# Use an ensemble of states to estimate a multidimensional probability distribution

    # Make sure inputs are matrix and column vector types
    Xb = np.matrix(Xb)
    yo = np.matrix(yo).flatten().T

    nr,nc = np.shape(Xb)
    xdim = nr
    edim = nc
    ydim = len(yo)
    Hl = self.H
    R = self.R
    Rinv = np.linalg.inv(R)

    # Mintail as machine epsilon
    mintail = np.finfo(float).eps
  
    # Convert background to observation space
    Yb = np.matrix(np.zeros([ydim,edim]))
    for k in range(edim):
      Yb[:,k] = Hl*Xb[:,k]

    # Compute the weights
    # Use a Gaussin for the observation likelihood
    likelihood = np.zeros(edim)
    for k in range(edim):
      likelihood[k] = np.exp(-0.5* (yo-Yb[:,k]).T * Rinv * (yo-Yb[:,k]) )
    likelihood = likelihood + mintail

    # Normalize the weights
    weights = likelihood/np.sum(likelihood)

    # form cumulative distribution
    weight = np.cumsum(weights)

    # Calculate effective sample size
    Neff = 1/np.sum(np.square(weights))

    # Resample the particles with replacement
    addit=1.0/edim
    stt=addit*np.random.rand(1)
    selection_points=np.arange( stt , stt + edim*addit , addit) # Check to make sure ported correctly from matlab

#   print('addit = ', addit)
#   print('stt = ', stt)
#   print('selection_points = ')
#   print(selection_points)

    #(set up comb)
    Xa = np.matrix(np.zeros_like(Xb))
    resampling_index = np.zeros(edim)
    j=1; 
    for i in range(edim):
      while selection_points[i] >= weight[j]:
        j=j+1
      resampling_index[i]=j
      Xa[:,i] = Xb[:,j]

    # Apply inflation
    if (Neff < edim/2):
      # Apply additive inflation (remove sample mean)
      const=1.0
      rmat=np.rand.randn(xdim,edim) * np.matlib.repmat(np.std(Xa,axis=1),1,edim) * const;
      Xa = Xa + rmat - np.matlib.repmat(np.mean(rmat,axis=1),1,edim);

    KH = [0] # dummy output

    return Xa, KH

#---------------------------------------------------------------------------------------------------
  def HybridGain(self,Xb,yo):
#---------------------------------------------------------------------------------------------------
# Use a hybrid method to compute the analysis

    # Make sure inputs are matrix and column vector types
    Xb = np.matrix(Xb)
    yo = np.matrix(yo).flatten().T

    # Get parameters
    alpha = self.alpha
    nr,nc = np.shape(Xb)
    xdim = nr
    edim = nc
    ydim = len(yo)

    # Compute ETKF analysis
    Xa_ETKF, KH_ETKF = self.ETKF(Xb,yo)
    print('Xa_ETKF = ')
    print(Xa_ETKF)

    # Compute 3DVar analysis
    xa_ETKF = np.mean(Xa_ETKF,axis=1)
    print('xa_ETKF = ')
    print(xa_ETKF)
    xa_3DVar, KH_3DVar = self._3DVar(xa_ETKF,yo)
    print('xa_3DVar = ')
    print(xa_3DVar)

    xa_ETKF = np.matrix(xa_ETKF).flatten().T
    xa_3DVar = np.matrix(xa_3DVar).flatten().T

    # Recover ensemble perturbations
    Xa_ETKF = Xa_ETKF - np.matlib.repmat(xa_ETKF,1,edim)

    # Form hybrid combination to update the mean state
    xa_hybrid = (1-alpha)*xa_ETKF + alpha*xa_3DVar
    Xa = Xa_ETKF + np.matlib.repmat(xa_hybrid,1,edim)

    print('xa_hybrid = ')
    print(xa_hybrid)

    KH = (1-alpha)*KH_ETKF + alpha*KH_3DVar

    return Xa, KH 


#---------------------------------------------------------------------------------------------------
  def save(self,outfile):
#---------------------------------------------------------------------------------------------------
    with open(outfile,'wb') as output:
      pickle.dump(self,output,pickle.HIGHEST_PROTOCOL)

#---------------------------------------------------------------------------------------------------
  def load(self,infile):
#---------------------------------------------------------------------------------------------------
    with open(infile,'rb') as input:
      das = pickle.load(input)
    return das