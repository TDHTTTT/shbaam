import fiona
import shapely.geometry
import shapely.prepared
import sys
import pprint
import rtree
from netCDF4 import Dataset

def newSHP(nf,sf):
    lonum,lanum = len(nf.variables['lon']),len(nf.variables['lat'])
    lons,lats = nf.variables['lon'],nf.variables['lat']
    schx={'geometry': 'Point', 'properties': {'lon': 'int:4', 'lat': 'int:4'}}
    with fiona.open('tmpxx.shp','w',driver=sf.driver,crs=sf.crs.copy(),schema=schx) as tmpx:
        for lonx in range(lonum):
            nlon = lons[lonx]
            if nlon > 180:
                nlon -= 360
            for latx in range(lanum):
                nlat = lats[latx]
                tmprop = {'lon':lonx,'lat':latx}
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
                ilons.append(sfpfea['properties']['lon'])
                ilats.append(sfpfea['properties']['lat'])
                tot += 1
    return tot, ilons, ilats


if __name__ == "__main__":
    ifns = sys.argv[1:]
    nf = Dataset(ifns[0],'r')
    sf = fiona.open(ifns[1],'r')
    newSHP(nf,sf)
    tmpx = fiona.open('tmpxx.shp','r')
    index = newIndex(tmpx)
    tot, ilons, ilats = findInter(sf,index,tmpx)
    print(tot,ilons,ilats)
