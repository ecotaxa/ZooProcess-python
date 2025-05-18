import pytest

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


def test_latitude_correction_45_3():
    correctedValue = latlng_correction(45.3)
    assert correctedValue == 45.50


def test_latitude_correction_10_3():
    correctedValue = latlng_correction(10.3)
    assert correctedValue == 10.50


def test_latitude_correction_10_3030():
    correctedValue = latlng_correction(10.3030)
    assert correctedValue == 10.5050


def test_latitude_correction_10_30000():
    correctedValue = latlng_correction(10.30000)
    assert correctedValue == 10.50000


def test_latitude_correction_from_apero():
    # meta
    # apero2023_pp_wp2_001_st01_d ;pourquoipas ;apero          ;        1 ;20230610-1303 ;48.27162   ;22.30036   ; 4107 ;nan    ;nan      ;    1 ;      3 ;wp2     ;    200 ;  99999 ; 200 ;   0 ;20.2875   ;nan            ;     1 ;       2 ;     1111 ;ape000000659 ;  48.27162   ;   22.30039   ;          17 ;               0 ;       99999 ;      99999 ;        0.5 ;     1
    # tsv
    # apero2023_pp_wp2_001...(2715 characters truncated, it's impossible to view or edit this line)

    # 48.27162   ;22.30036 -> 48.4527    	-22.500600000000002
    correctedValue = latlng_correction(48.27162)
    assert correctedValue == 48.4527
    correctedValue = latlng_correction(22.30036)
    assert correctedValue == 22.50060

    # 48.27162   ;   22.30039 -> 48.4527        	-22.50065
    correctedValue = latlng_correction(48.27162)
    assert correctedValue == 48.4527
    correctedValue = latlng_correction(22.30039)
    assert correctedValue == 22.50065