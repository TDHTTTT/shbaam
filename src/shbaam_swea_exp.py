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

def newSHP(nf,sf,lons,lats):
    lonum,lanum = len(lons),len(lats)
    schx={'geometry': 'Point', 'properties': {'lonx': 'int:4', 'latx': 'int:4','nlon':'float','nlat':'float'}}
    with fiona.open('tmpxx.shp','w',driver=sf.driver,crs=sf.crs.copy(),schema=schx) as tmpx:
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

def findInter(sf,index,tmpx):
    tot = 0
    ilons, ilats = [], []
    for fea in sf:
        sfshy = shapely.geometry.shape(fea['geometry'])
        sfpre = shapely.prepared.prep(sfshy)
        for sfid in [int(x) for x in list(index.intersection(sfshy.bounds))]:
            sfpfea = tmpx[sfid]
            sfpshy = shapely.geometry.shape(sfpfea['geometry'])
            if sfpre.contains(sfpshy):
                ilons.append((sfpfea['properties']['lonx'],sfpfea['properties']['nlon']))
                ilats.append((sfpfea['properties']['latx'],sfpfea['properties']['nlat']))
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

def outCSV(times,ptimes):
    with open('tmpx.csv' , 'w') as cf:
        cw = csv.writer(cf,dialect='excel')
        for t in range(len(times)):
            cw.writerow([ptimes[t],sweas[t]])

if __name__ == "__main__":
    ifns = sys.argv[1:]
    nf = Dataset(ifns[0],'r')
    lons,lats,times = nf.variables['lon'],nf.variables['lat'],nf.variables['time']
    swes = nf.variables['SWE']
    print('s',swes.shape)
    sf = fiona.open(ifns[1],'r')
    newSHP(nf,sf,lons,lats)
    tmpx = fiona.open('tmpxx.shp','r')
    index = newIndex(tmpx)
    tot, ilons, ilats = findInter(sf,index,tmpx)
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
    outCSV(times,ptimes)

    nf.close()
    sf.close()
