import netCDF4
from datetime import datetime, timedelta
import numpy as np
import sys

def conc(ifs,o):
    for (dn, dim) in ifs[0].dimensions.items():
        #print(dn,dim)
        o.createDimension(dn,len(dim) if not dim.isunlimited() else None)
    for (vn, ivar) in ifs[0].variables.items():
        #print(vn,ivar)
        ovar = o.createVariable(vn, ivar.datatype, ivar.dimensions)
        ovar.setncatts({an: ivar.getncattr(an) for an in ivar.ncattrs()})
        if vn in ("lat","lon"):
            ovar[:] = ivar[:]
        elif vn == "time":
            ovar = np.array([0])
            stime = datetime(*list(int(i[-1]) if len(i) == 2 and i[0] == 0 else int(i) for i in ivar.units.split()[2].split("-")))
            for ifx in ifs[1:]:
                timex = datetime(*list(int(i[-1]) if len(i) == 2 and i[0] == 0 else int(i) for i in ifx.variables[vn].units.split()[2].split("-")))
                ovar = np.append(ovar,(timex-stime).total_seconds()/3600)
                print(ovar)
                print((timex-stime).total_seconds()/3600)
        else:
            ivars = ivar[:]
            for ifx in ifs[1:]:
                #print(22222,ivars,ivars.shape,type(ivars))
                ivars = np.ma.concatenate((ivars,ifx.variables[vn][:]))
            ovar[:] = ivars[:]
            

if __name__ == "__main__":
    ifns = sys.argv[1:-1]
    ofn = sys.argv[-1]

    ifs = [netCDF4.Dataset(i,'r') for i in ifns]
    of = netCDF4.Dataset(ofn,"w",format="NETCDF4")
    
    conc(ifs,of)

    for i in ifs:
        i.close()
    of.close()
