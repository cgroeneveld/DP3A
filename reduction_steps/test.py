import phase_cal as pc

gs = pc.PhaseCalibrator(0,'/data1/groeneveld/LB_295_single/SB430.avg.ms/', '/data1/groeneveld/autodeploy/LB1/testrun1/', '../')
gs.initialize()
gs.execute()
