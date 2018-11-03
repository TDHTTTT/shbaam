#!/usr/bin/env python3
import fiona
import shapely.geometry
import shapely.prepared
import sys
import pprint
import rtree
from netCDF4 import Dataset
import math
import numpy as np
import datetime
import csv
import shbaam_conc

def newSHP(inx,isx,lons,lats,osn):
    lonum,lanum = len(lons),len(lats)
    schx={'geometry': 'Point', 'properties': {'lonx': 'int:4', 'latx': 'int:4','nlon':'float','nlat':'float'}}
    with fiona.open(osn,'w',driver=isx.driver,crs=isx.crs.copy(),schema=schx) as tmpx:
        for lonx in range(lonum):
            nlon = lons[lonx]
            if nlon > 180:
                print(nlon)
                #nlon -= 360
            for latx in range(lanum):
                nlat = lats[latx]
                tmprop = {'lonx':lonx,'latx':latx, 'nlon':nlon,'nlat':nlat}
                tmpgeo = shapely.geometry.mapping(shapely.geometry.Point((nlon,nlat)))
                tmpx.write({'properties':tmprop,'geometry':tmpgeo})

def newIndex(tmpx):
    index = rtree.index.Index()
    for fea in tmpx:
        tmpfid = int(fea['id'])
        tmpshy = shapely.geometry.shape(fea['geometry'])
        index.insert(tmpfid,tmpshy.bounds)
    return index

def findInter(isx,index,tmpx):
    tot = 0
    ilons, ilats = [], []
    for fea in isx:
        isxshy = shapely.geometry.shape(fea['geometry'])
        isxpre = shapely.prepared.prep(isxshy)
        for isxid in [int(x) for x in list(index.intersection(isxshy.bounds))]:
            isxpfea = tmpx[isxid]
            isxpshy = shapely.geometry.shape(isxpfea['geometry'])
            if isxpre.contains(isxpshy):
                ilons.append((isxpfea['properties']['lonx'],isxpfea['properties']['nlon']))
                ilats.append((isxpfea['properties']['latx'],isxpfea['properties']['nlat']))
                tot += 1
    return tot, ilons, ilats

def getMean(tot,ilons,ilats,times,swes):
    avgs = [0] * tot
    for i in range(tot):
        lonx, latx = ilons[i][0], ilats[i][0]
        for t in range(len(times)):
            #print(t,lonx,latx)
            #print(swes[t,latx,lonx])
            avgs[i] = avgs[i] + swes[t,latx,lonx]
    avgs = [x/len(times) for x in avgs]
    return avgs

def getSQM(tot,ilons,ilats,lons,lats):
    sqms = [0] * tot
    lonstp = abs(lons[1] - lons[0])
    latstp = abs(lats[1] - lats[0])
    for i in range(tot):
        nlat = ilats[i][1]
        sqms[i] = 6371000*math.radians(latstp)*6371000*math.radians(lonstp)*math.cos(math.radians(nlat))
    return sqms

def getSWEA(tot,ilons,ilats,times,avgs,sqms,swes):
    sweas = []
    for t in range(len(times)):
        swea = 0
        for i in range(tot):
            lonx,latx = ilons[i][0],ilats[i][0]
            avgx = avgs[i]
            sqmx = sqms[i]
            sweax = (swes[t,latx,lonx])/100 - avgx * sqmx
            swea += sweax
        sweas.append(100*swea/sum(sqms))
    return sweas

def getPtimes(times):
    start = datetime.datetime.strptime('2002-04-01T00:00:00', '%Y-%m-%dT%H:%M:%S')
    print(start)
    ptimes = []
    for t in range(len(times)):
        dt = datetime.timedelta(hours=times[t])
        print(dt)
        ptimex = (start+dt).strftime('%m%d%y')
        ptimes.append(ptimex)
    return ptimes

def outCSV(times,ptimes,ocx):
    with open(ocx , 'w') as cf:
        cw = csv.writer(cf,dialect='excel')
        for t in range(len(times)):
            cw.writerow([ptimes[t],sweas[t]])

def outNC(tot,ilons,ilats,avgs,swes,onx):
    swe, canint = shbaam_conc.copy([inx],onx)
    print(swe,canint)
    dt=datetime.datetime.utcnow()
    dt=dt.replace(microsecond=0)
    #Current UTC time without the microseconds
    #vsn=subprocess.Popen('bash ../version.sh', stdout=subprocess.PIPE,shell=True).communicate()
    #vsn=vsn[0]
    #vsn=vsn.rstrip()
    #Version of SHBAAM

    onx.Conventions='CF-1.6'
    onx.title=''
    onx.institution=''
    #h.source='SHBAAM: '+vsn+', GRACE: '+os.path.basename(shb_grc_ncf) +', Scale factors: '+os.path.basename(shb_fct_ncf)
    onx.history='date created: '+dt.isoformat()+'+00:00'
    onx.references='https://github.com/c-h-david/shbaam/'
    onx.comment=''
    onx.featureType='timeSeries' 

    for i in range(tot):
        lonx,latx = ilons[i][0],ilats[i][0]
        avgx = avgs[i]
        for t in range(len(times)):
            swe[t,latx,lonx] = swes[t,latx,lonx] - avgx

if __name__ == "__main__":
    ifns = sys.argv[1:]
    inx = Dataset(ifns[0],'r')
    isx = fiona.open(ifns[1],'r')
    osn = ifns[2]
    ocx = ifns[3]
    onx = Dataset(ifns[4],'w',format='NETCDF4')

    lons,lats,times = inx.variables['lon'],inx.variables['lat'],inx.variables['time']
    swes = inx.variables['SWE']
    print('s',swes.shape)
    newSHP(inx,isx,lons,lats,osn)
    osx = fiona.open(osn,'r')
    index = newIndex(osx)
    tot, ilons, ilats = findInter(isx,index,osx)
    print("Total # of cells:",tot,"Longitudes:",ilons,"Latitudes:",ilats)
    avgs = getMean(tot,ilons,ilats,times,swes)
    print(avgs)
    sqms = getSQM(tot,ilons,ilats,lons,lats)
    print(sqms)
    sweas = getSWEA(tot,ilons,ilats,times,avgs,sqms,swes)
    print(sweas)

    print('- Average of time series: '+str(np.average(sweas)))
    print('- Maximum of time series: '+str(np.max(sweas)))
    print('- Minimum of time series: '+str(np.min(sweas)))

    ptimes = getPtimes(times)
    print(ptimes)
    outCSV(times,ptimes,ocx)
    outNC(tot,ilons,ilats,avgs,swes,onx)

    inx.close()
    isx.close()
    osx.close()
    onx.close()
