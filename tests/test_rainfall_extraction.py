"""Synthetic exactextract contracts: fractions, touched cells, NoData, no coverage."""
import tempfile
from pathlib import Path
import unittest
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from exactextract import exact_extract
from shapely.geometry import box

class ExtractionTests(unittest.TestCase):
    def test_fractional_all_intersections_and_nodata(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'rain.tif'
            with rasterio.open(path,'w',driver='GTiff',width=2,height=1,count=1,dtype='float32',
                               crs='EPSG:4326',transform=from_origin(0,1,1,1),nodata=-9999) as dst:
                dst.write(np.array([[10,30]],dtype='float32'),1)
            # One whole pixel and one quarter pixel: (10*1 + 30*.25)/1.25 = 14.
            g=gpd.GeoDataFrame(geometry=[box(0,0,1.25,1)],crs='EPSG:4326')
            q=exact_extract(str(path),g,['mean','values','coverage','count'],output='pandas')
            self.assertAlmostEqual(q.iloc[0]['mean'],14)
            self.assertEqual(len(q.iloc[0]['values']),2)
            np.testing.assert_allclose(sorted(q.iloc[0]['coverage']),[.25,1])
            with rasterio.open(path,'r+') as dst:dst.write(np.array([[10,-9999]],dtype='float32'),1)
            q=exact_extract(str(path),g,['mean','count'],output='pandas')
            self.assertAlmostEqual(q.iloc[0]['mean'],10);self.assertAlmostEqual(q.iloc[0]['count'],1)
            with rasterio.open(path,'r+') as dst:dst.write(np.array([[-9999,-9999]],dtype='float32'),1)
            q=exact_extract(str(path),g,['mean','count'],output='pandas')
            self.assertTrue(np.isnan(q.iloc[0]['mean']));self.assertEqual(q.iloc[0]['count'],0)

if __name__=='__main__':unittest.main()
