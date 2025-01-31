import unittest
# from unittest.mock import Mock, patch

# from main import latitude_correction, longitude_correction

def latlng_correction1(value):
    try:
        val = float(value)
        degrees = int(val)
        minutes = (val - degrees) * 60
        minutes = int(minutes/6*10)
        return degrees + minutes/100
    except ValueError:
        return value

def latlng_correction2(value):
    try:
        val = float(value)
        degrees = int(val)
        decimal = (val - degrees) * 100
        decimal = int(decimal/3*5)
        return degrees + decimal/100
    except ValueError:
        return value

def latlng_correction3(value):
    try:
        val = float(value)
        degrees = int(val)
        decimal = (val - degrees) * 10
        decimal = round(decimal/3*5)
        return degrees + decimal/10
    except ValueError:
        return value

def latlng_correction4(value):
    try:
        val = float(value)
        degrees = int(val)
        decimal = (val - degrees) * 100
        decimal = round(decimal/30*50, 4)
        return degrees + decimal/100
    except ValueError:
        return value

def latlng_correction5(value):
    try:
        val = float(value)
        degrees = int(val)
        minutes = (val - degrees)
        return degrees + (minutes * 100) / 60
    except ValueError:
        return value

def latlng_correction(value):
    try:
        val = float(value)
        degrees = int(val)
        minutes = (val - degrees)
        return round(degrees + (minutes * 100) / 60, 5)
    except ValueError:
        return value

def latlng_correctionold(value):
    try:
        val = float(value)
        degrees = int(val)
        print("degrees: ", degrees)
        minutes = (val - degrees) * 60
        # minutes = int((val - degrees) * 60)
        print("minutes: ", minutes)
        # seconds = int((minutes - int(minutes)) * 60)
        seconds = (minutes - int(minutes)) * 60
        print("seconds: ", seconds)
        minutes = int(minutes/6*10)
        print("minutes: ", minutes)
        seconds = int(seconds/6*10)
        print("seconds: ", seconds)
        print("total: ", degrees + minutes / 60 + seconds / 3600)
        return degrees + minutes / 100 + seconds / 1000
        # return float(value)
    except ValueError:
        return value
    
class Test_tools(unittest.TestCase):

    def test_latitude_correction_45_3(self):

        correctedValue = latlng_correction(45.3)
        
        self.assertEqual(correctedValue,45.50)


    def test_latitude_correction_10_3(self):

        correctedValue = latlng_correction(10.3)
        
        self.assertEqual(correctedValue,10.50)

    def test_latitude_correction_10_3030(self):

        correctedValue = latlng_correction(10.3030)
        
        self.assertEqual(correctedValue,10.5050)


    def test_latitude_correction_10_30000(self):

        correctedValue = latlng_correction(10.30000)
        
        self.assertEqual(correctedValue,10.50000)


    def test_latitude_correction_from_apero(self):

        # meta
        # apero2023_pp_wp2_001_st01_d ;pourquoipas ;apero          ;        1 ;20230610-1303 ;48.27162   ;22.30036   ; 4107 ;nan    ;nan      ;    1 ;      3 ;wp2     ;    200 ;  99999 ; 200 ;   0 ;20.2875   ;nan            ;     1 ;       2 ;     1111 ;ape000000659 ;  48.27162   ;   22.30039   ;          17 ;               0 ;       99999 ;      99999 ;        0.5 ;     1
        # tsv
        # apero2023_pp_wp2_001_st01_d_d1_1_1.jpg   	0        	apero2023_pp_wp2_001_st01_d_d1_1_1   	http://www.zooscan.obs-vlfr.fr// 	48.4527    	-22.500600000000002 	20230610    	13:03:00.000 	0                	200              	48.4527        	-22.50065      	263906      	187.32      	27.751        	191         	95         	255        	420.78   	406.34   	427       	413.31    	6910.61       	11153     	90        	1059         	826           	746.2        	450.3        	141.8        	0.069        	1173.2       	49435719      	188           	-0.23       	0.152       	0.65         	11393         	90            	262202          	1.167          	10417           	18.652       	169             	187             	203             	0           	0           	53         	37         	0          	0                  	0               	0                	0             	0             	0             	4.501            	4.516            	5                 	5                 	3766             	574731          	28.898       	3.614         	1          	579.6684874071367  	1.6577777777777778 	160          	-0.7331022530329291  	9.219544457292887  	14.947683109118087  	17.5               	13.496553884828568  	2.2907622206488076  	5.891730605285592  	9.264075067024129  	0.06898649465598765  	0.018004931060834325  	zooprocess_apero2023_pp_wp2_001_st01_d 	20230919     	17:55:00.000 	8.03_picheral_cnrs           	2400                   	nan                 	0                  	20230914_0917_background_large_manual.tif 	8.13_2022/10/17_picheral_cnrs 	243                        	0.0106                         	0.3                          	100                          	include                   	0.0745                    	zooprocess_pid_to_ecotaxa_8.20_2024/01/19 	d1_apero2023_pp_wp2_001_st01_d 	1000         	999999       	1            	motoda         	hydroptic_v1 	9.7.67       	hugo_berrenger 	zooscan     	20230914      	10:44:00.000  	4           	3            	2            	3                   	3            	1         	30120     	48728     	6354        	1021        	manual                	no             	757         	63237       	1.8             	1.15          	54989.1            	zooscan_sn002  	no               	apero2023_pp_wp2_001_st01_d 	hugo_berrenger       	pourquoipas 	apero          	1                	4107               	nan                       	nan              	1             	3               	wp2             	200             	99999           	200         	0           	20.2875        	nan            	1                 	2               	1111             	ape000000659   	17              	0                 	99999               	99999              	0.5                	1             	nan                          	nan


        # 48.27162   ;22.30036 -> 48.4527    	-22.500600000000002
        correctedValue = latlng_correction(48.27162 )
        self.assertEqual(correctedValue, 48.4527)
        correctedValue = latlng_correction(22.30036 )
        self.assertEqual(correctedValue, 22.50060)

        # 48.27162   ;   22.30039 -> 48.4527        	-22.50065
        correctedValue = latlng_correction(48.27162 )
        self.assertEqual(correctedValue, 48.4527)
        correctedValue = latlng_correction(22.30039)
        self.assertEqual(correctedValue,22.50065 )