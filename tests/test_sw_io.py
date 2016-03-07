import nose.tools as nt
import swtools
import numpy as np 
import datetime as dt
import unittest
import spacepy
import os
import warnings

import swtools.ops 
import swtools.aux 
import swtools.sph 
import swtools.ops 
import swtools.sw_io


swtools.debug_info(-1)#as error will be generated when testing 
#if errors work, stdout logging is suppressed

warnings.simplefilter("ignore")


class test_CDF(unittest.TestCase):
    
    def setUp(self):
        from spacepy import pycdf
        #generate two fake CDF swarm product files
        self.N = 60
        self.atol = 1e-5

        np.random.seed(1)

        self.timestamp = [dt.datetime(2000, 10, 1, 1, val) for val in range(self.N)]
        self.radius = np.random.random_sample(len(self.timestamp))
        self.n = np.random.random_sample(len(self.timestamp))

        self.fn1='SW_OPER_EFIA_PL_1B_20150716T000000_20150716T235959_0402_MDR_EFI_PL.cdf'
        self.fn2='SW_OPER_EFIB_PL_1B_20150718T000000_20150716T235959_0403_MDR_EFI_PL.cdf'
        self.rname='radius'
        self.nname='n'
        self.tname='Timestamp'
        self.r_u = 'm'
        self.n_u = '1/m^-3'
        self.t_u = ''
        for i,fn in enumerate([self.fn1,self.fn2]):
            cdf = pycdf.CDF(fn,'')
            cdf[self.tname] = self.timestamp
            cdf[self.rname] = self.radius
            cdf[self.nname] = self.n + i 

            cdf[self.rname].attrs['UNITS'] = self.r_u
            cdf[self.nname].attrs['UNITS'] = self.n_u
            cdf[self.tname].attrs['UNITS'] = self.t_u
            cdf.close()

    def tearDown(self):
        for fn in [self.fn1,self.fn2]:
            os.remove(fn)


    def test_getCDFparams(self):
        p1 = swtools.getCDFparams(self.fn1,'n','Timestamp')
        n = p1[0]
        t = p1[1]
        assert isinstance(n,swtools.Parameter)
        assert len(n.values) == self.N, 'unexpected number of values: {}!={}'\
            .format(len(n.values),self.N)
        
        assert abs(n[ 0] - 0.10233443) < self.atol, '{} != {}'\
            .format(n[0],0.10233443)
        
        assert abs(n[-1] - 0.12427096) < self.atol, '{} != {}'\
            .format(n[-1],0.12427096)
        
        assert n.name == self.nname,'{} != {}'.format(n.name,self.nname)
        assert n.unit == self.n_u,'{} != {}'.format(n.unit,self.n_u)
        tmp = n.values*2

        p2 = swtools.getCDFparams('.','n',sat='B')
        assert abs(p2[0]-n[0]-1) < self.atol,'{} != {}'\
            .format(p2[0],n[0]+1)

        pass

    def test_getCDFlist(self):
        flist1 = swtools.getCDFlist('.')
        
        assert os.path.abspath(self.fn1) in flist1
        assert os.path.abspath(self.fn2) in flist1
        
        flist2 = swtools.getCDFlist(start_t='2015-07-18',end_t='2015-09-18')
        assert len(flist2) == 1,"len: {}".format(len(flist2))

        flist3 = swtools.getCDFlist(start_t='20150716',duration=2)
        assert flist3 == flist1,"{}!={}".format(flist3,flist1)
        pass

    def test_extract_parameter(self):
        #implicitly tested in test_getCDFparams
        pass

    def test_concatenate_values(self):
        a1 = np.hstack((self.n,self.n))
        a2 = swtools.concatenate_values(self.n,self.n)

        a4 = swtools.concatenate_values(np.vstack((self.n,self.n)),
            np.vstack((self.n,self.n)),axis=0)
        a3 = swtools.concatenate_values(np.vstack((self.n,self.n)),
            np.vstack((self.n,self.n)),axis=1)
        
        np.testing.assert_allclose(a1,a2,atol=self.atol)
        
        assert a2.shape == (self.N*2,),"{} != {}".format(a3.shape,(self.N*2,))
        assert a3.shape == (2,self.N*2),"{} != {}".format(a3.shape,(2,self.N*2))
        assert a4.shape == (4,self.N),"{} != {}".format(a4.shape,(4,self.N))
        
        pass

def test_read_sp3():
    atol = 1e-5
    p1 = swtools.read_sp3('sample_kin.txt',doctype=1,SI_units=False)
    p2 = swtools.read_sp3('sample_rd.txt',doctype=2)

    assert abs(p1[0][0] - 5031.197333) < atol,"{} != {}"\
        .format(p1[0][0],5031.197333)
    assert len(p1) == 5,"{} != 5".format(len(p1))
    assert p1[3][0].month == 11 

    assert len(p2) == 9,"{} != 9".format(len(p2))
    assert abs(p2[0][0] - 5031.1973021*1000) < atol
    assert abs(p2[3][0] - 33366.6869662/10 ) < atol
    assert int(round(p2[7][1].second)) == 11 
    
    pass

def test_info_from_filename():
    fn1='SW_OPER_EFIA_PL_1B_20150716T000000_20150716T235959_0402_MDR_EFI_PL.cdf'
    fn2='SW_OPER_EFIB_PL_1B_20150718T000000_20150716T235959_0403_MDR_EFI_PL.cdf'
    assert swtools.sw_io._info_from_filename(fn1,'mission') == "SW"
    assert swtools.sw_io._info_from_filename(fn1,'version') == "0402"
    t01 = dt.datetime(2015,7,16,0,0,0)
    assert swtools.sw_io._info_from_filename(fn1,'t0') == t01
    assert swtools.sw_io._info_from_filename(fn1,'product') == \
        'EFIA_PL_1B'+'_MDR_EFI_PL'
    
    d2 = swtools.sw_io._info_from_filename(fn2)
    for k in d2.keys():
        assert k in ['t0','t1','mission','oper','version','product','version'],k
    pass

def test_filter_filelist():
    fl = ['SW_OPER_EFIA_PL_1B_20150716T000000_20150716T235959_0402_MDR_EFI_PL.cdf',
          'SW_OPER_EFIB_PL_1B_20150716T000000_20150716T235959_0402_MDR_EFI_PL.cdf',
          'SW_OPER_EFIA_PL_1B_20160716T000000_20160716T235959_0402_MDR_EFI_PL.cdf',
          'SW_OPER_EEFATMS_2F_20151101T234509_20151102T230946_0101.DBL',
          'SW_OPER_EEFBTMS_2F_20151101T234509_20151102T230946_0101.DBL',
          'SW_OPER_EEFATMS_2F_20161101T234509_20161102T230946_0101.DBL']
    fl2 = [i for i in fl]
    fl3 = [i for i in fl]
    filt1 = {'sat':'B','param0':'EEF'}
    filt2 = {'sat':'A','period':swtools.aux._set_period(end_t='20150717',duration=5)}
    swtools.sw_io._filter_filelist(fl,**filt1)
    swtools.sw_io._filter_filelist(fl2,**filt2)
    assert fl  == [fl3[4]],"FL:\n'{}'\n".format('\n'.join(fl))
    assert fl2 == [fl3[0]],"FL:\n'{}'\n".format('\n'.join(fl2))
    pass

def test_read_EFI():
    atol = 1e-5
    pEFI = swtools.read_EFI_prov_txt('prel_efi.txt')

    assert abs(pEFI['latitude'][0] - 6.797) < atol

    pEFIn = swtools.read_EFI_prov_txt('prel_efi.txt','n')
    assert abs(pEFIn[0] - 163151) < atol,pEFIn[0]
    pass

def test_Parameter():
    v,u,n = [1,2,3],'myunit','myname'
    p = swtools.Parameter([1,2,3],'myunit','myname')

    assert p.name == n
    assert p.unit == u
    assert p.values == v
    assert p[0] == p.values[0]
    assert p() == p.values
    pass


if __name__ == '__main__':
  import nose
  
  nose.main()
  