from modern.utils import convert_ddm_to_decimal_degrees


def test_latitude_correction_45_3():
    corrected_value = convert_ddm_to_decimal_degrees(45.3)
    assert corrected_value == 45.50


def test_latitude_correction_10_3():
    corrected_value = convert_ddm_to_decimal_degrees(10.3)
    assert corrected_value == 10.50


def test_latitude_correction_10_3030():
    corrected_value = convert_ddm_to_decimal_degrees(10.3030)
    assert corrected_value == 10.5050


def test_latitude_correction_10_30000():
    corrected_value = convert_ddm_to_decimal_degrees(10.30000)
    assert corrected_value == 10.50000


def test_latitude_correction_from_apero():
    # meta
    # apero2023_pp_wp2_001_st01_d ;pourquoipas ;apero          ;        1 ;20230610-1303 ;48.27162   ;22.30036   ; 4107 ;nan    ;nan      ;    1 ;      3 ;wp2     ;    200 ;  99999 ; 200 ;   0 ;20.2875   ;nan            ;     1 ;       2 ;     1111 ;ape000000659 ;  48.27162   ;   22.30039   ;          17 ;               0 ;       99999 ;      99999 ;        0.5 ;     1
    # tsv
    # apero2023_pp_wp2_001...(2715 characters truncated, it's impossible to view or edit this line)

    # 48.27162   ;22.30036 -> 48.4527    	-22.500600000000002
    corrected_value = convert_ddm_to_decimal_degrees(48.27162)
    assert corrected_value == 48.4527
    corrected_value = convert_ddm_to_decimal_degrees(22.30036)
    assert corrected_value == 22.50060

    # 48.27162   ;   22.30039 -> 48.4527        	-22.50065
    corrected_value = convert_ddm_to_decimal_degrees(48.27162)
    assert corrected_value == 48.4527
    corrected_value = convert_ddm_to_decimal_degrees(22.30039)
    assert corrected_value == 22.50065
