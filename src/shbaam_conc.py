#!/usr/bin/env python3
import netCDF4
from datetime import datetime, timedelta
import numpy as np
import sys

def copy(ifs,o):
    res = []
    for (dn, dim) in ifs[0].dimensions.items():
        o.createDimension(dn,len(dim) if not dim.isunlimited() else None)

    for (vn, ivar) in ifs[0].variables.items():
        ovar = o.createVariable(vn, ivar.datatype, ivar.dimensions)
        ovar.setncatts({an: ivar.getncattr(an) for an in ivar.ncattrs()})
        if vn not in ("SWE","Canint"):
            ovar[:] = ivar[:]
        else:
            res.append(ovar)
    return res
            
def conc_time(ifs,o):
    for (vn, ovar) in o.variables.items():
        if vn == "time":
            stime = datetime(*list(int(i[-1]) if len(i) == 2 and i[0] == 0 else int(i) for i in ovar.units.split()[2].split("-")))
            for ifx in ifs[1:]:
                timex = datetime(*list(int(i[-1]) if len(i) == 2 and i[0] == 0 else int(i) for i in ifx.variables[vn].units.split()[2].split("-")))
                ovar[:] = np.append(ovar[:],(timex-stime).total_seconds()/3600)
                 
def conc_vars(ifs,o):
    for (vn, ovar) in o.variables.items():
        if vn in ("SWE", "Canint"):
            for i in range(len(ifs)):
                ifx = ifs[i]
                ovar[i] = ifx.variables[vn][:] 
            

def check(o):
    #np.set_printoptions(threshold=np.nan)
    for (vn, ovar) in o.variables.items():
        print(ovar,ovar[:],ovar[:].shape)

if __name__ == "__main__":
    ifns = sys.argv[1:-1]
    ofn = sys.argv[-1]

    ifs = [netCDF4.Dataset(i,'r') for i in ifns]
    of = netCDF4.Dataset(ofn,"w",format="NETCDF4")
    
    copy(ifs,of)
    conc_time(ifs,of)
    conc_vars(ifs,of)
    check(of)

    for i in ifs:
        i.close()
    of.close()
