# -*- coding: utf8 -*-
from nose.tools import eq_

from core import scan


def test_multiple_sections():
    eq_(scan(u'8 U. S. C. §§1225 (a)(1), 1226a'),
        [dict(
            id='usc',
            title='8',
            secsymbol=u'\xa7',
            section='1225'),
         dict(
            id='usc',
            title='8',
            secsymbol=u'\xa7',
            section='1226a')]),


# def test_basic():
#     eq_(scan(u'8 U. S. C. §1226a'),
#         [dict(
#             id='usc',
#             title='8',
#             secsymbol=u'\xa7',
#             section='1226a')]),


# def test_space():
#     eq_(scan(u'8 U. S. C. § 1226a'),
#         [dict(
#             id='usc',
#             title='8',
#             secsymbol=u'\xa7',
#             section='1226a')]),


# def test_no_sec():
#     eq_(scan(u'8 U. S. C. 1226a'),
#         [dict(
#             id='usc',
#             title='8',
#             section='1226a')]),


# def test_acronym_short():
#     eq_(scan(u'8 USC §1226a'),
#         [dict(
#             id='usc',
#             title='8',
#             secsymbol=u'\xa7',
#             section='1226a')]),


# def test_subd():
#     eq_(scan(u'8 U. S. C. §1226a(a)(5)'),
#         [dict(
#             id='usc',
#             title='8',
#             section='1226a',
#             secsymbol=u'\xa7',
#             subdivisions=('a', '5'))]),


# def test_subd_spaces():
#     eq_(scan(u'8 U. S. C. §1226a (a) (5)'),
#         [dict(
#             id='usc',
#             title='8',
#             section='1226a',
#             secsymbol=u'\xa7',
#             subdivisions=('a', '5'))]),


# def test_edition():
#     eq_(scan(u'8 U. S. C. §1226a(a)(5) (2000 ed., Supp. I)'),
#         [dict(
#             id='usc',
#             title='8',
#             section='1226a',
#             secsymbol=u'\xa7',
#             subdivisions=('a', '5'),
#             edition='2000',
#             supplement='I')]),


# def test_edition_nosubs():
#     eq_(scan(u'8 U. S. C. §1226a (2000 ed., Supp. I)'),
#         [dict(
#             id='usc',
#             title='8',
#             section='1226a',
#             secsymbol=u'\xa7',
#             edition='2000',
#             supplement='I')]),


# def test_edition_nosubs_nystyle():
#     eq_(scan(u'8 USC 1226a (2000 ed., Supp. I)'),
#         [dict(
#             id='usc',
#             title='8',
#             section='1226a',
#             edition='2000',
#             supplement='I')]),


# def test_note():
#     eq_(scan(u'8 USC 1226a note.'),
#         [dict(
#             id='usc',
#             title='8',
#             section='1226a',
#             note=True)])


# def test_etseq():
#     eq_(scan(u'8 USC 1226a et seq.'),
#         [dict(
#             id='usc',
#             title='8',
#             section='1226a',
#             etseq=True)])


data = '''

Pub. L. 109-295, title VI, Sec. 671, Oct. 4, 2006, 120 Stat. 1433 (6 U.S.C. 571 et seq.)

8 U. S. C. §1226a(a)(5) (2000 ed., Supp. I)
8 U. S. C. §1226a (2000 ed., Supp. I)
28 U. S. C. §§2243, 2246
28 U. S. C. §§2243(a)(5), 2246

31 CFR §595.204 (2003)
50 U. S. C. §811 et seq. (1970 ed.)
50 U. S. C. §811 et seq
10 U. S. C. §956(5)
was required by 18 U. S. C. §4001(a)--which provides that
28 U. S. C. §2241
26 U. S. C. §275(c) (1940 ed.)
26 U. S. C. §§61(a)(3), 1012
(Jones Act, 46 USC Appendix § 688)
(50 USC Appendix § 525)

§6501(e)(1)(A)(i)
Compare 26 U. S. C. §§22, 111 (1940 ed.) with §§61(a)(3), 1001(a) (2000 ed.)
filed." 26 U. S. C. §6501(a) (2000 ed.). The 3-year period is extended to 6 years, however, when a taxpayer "omits from gross income an amount properly includible therein which is in excess of 25 percent of the amount of gross income stated in the return." §6501(e)(1)(A) (e
See, e.g., 18 U. S. C. §2339A (material support for various terrorist acts); §2339B (material support to a foreign terrorist organization); §2332a (use of a weapon of mass destruction, including conspiracy and attempt); §2332b(a)(1) (acts of terrorism "transcending national boundaries," including threats, conspiracy, and attempt); 18 U. S. C. A. §2339C (Supp. 2004) (financing of certain terrorist acts); see also 18 U. S. C. §3142(e) (pretrial detention).

Homeland Security Act of 2002 (6 USC § 101 et seq., as added by Pub L 107-296, 116 US Stat 2135)
Title VII of the Civil Rights Act of 1964 (42 USC, ch 21, § 2000e et seq.)
Section 208 of the Social Security Act (42 USC § 408)
Jones Act (46 USC Appendix § 688)
Habeas Corpus Act of 1679, 31 Car. 2, c. 2

115 Stat. 272
Act of Mar. 3, 1863, 12 Stat. 755, §§1, 2

26 CFR §301.6501(e)-1 (2011)
§301.6501(e)-1(a)(1)(iii)
    The Government's argument about subsection (e)(2)'s use of the word
28 U.S.C. 1254 (1), 2101 (e)
(Homeland Security Act of 2002, 6 USC § 101 et seq., as added by Pub L 107-296, 116 US Stat 2135)
(Social Security Act § 208 [42 USC § 408])
(Pub L 105-298, 112 US Stat 2827 [105th Cong, 2d Sess, Oct. 27, 1998] [termed the "Sonny Bono Copyright Term Extension Act"], amending 17 USC § 301 [c])
(Pub L 106-74, tit V, § 531, 113 US Stat 1109, amending Multifamily Assisted Housing Reform and Affordability Act of 1997 § 524 [codified at 42 USC § 1437f Note])
(Act of May 31, 1790 § 1 [1st Cong, 2d Sess, ch 15], 1 US Stat 124, reprinted in Lib of Cong, Copyright Enactments, 1ending Multifamily Assisted Housing Reform and Affordability 783-1900, at 30-32)
50 USC Appendix § 525
(57 Fed Reg 48451 [1992], codified at 15 CFR 1150.1 et seq.)
(74 Fed Reg [No. 120] 30106 [2009])
(HR Rep 730, 95th Cong, 2d Sess, at 25, reprinted in 1978 US Code Cong & Admin News, at 9130, 9134)
(HR Rep No. 103-392, 103rd Cong, 1st Sess, reprinted in 1993 WL 484758) [Note: leave but don't add]
(S Rep 86-658, 86th Cong, 1st Sess, reprinted in 1959 US Code Cong & Admin News, at 2548)
(151 Cong Rec H3052-01 [May 5, 2005])
(Rep of Senate Judiciary Commn, at 4, S Rep 103-361, 103rd Cong, 2d Sess, reprinted in 1994 US Code Cong & Admin News, at 3259, 3260)
(7 CFR [Agriculture])
(7 CFR subtit A)
(7 CFR part 8)
(42 CFR ch IV)
(7 CFR 8.6)
(7 CFR 8.6 [a] [1])
(7 CFR 8.6, 8.7-8.9)
(7 CFR 8.6 [2000])
(Fed Rules Civ Pro rule 4 [b])
(Fed Rules Crim Pro rule 8 [a])
(Fed Rules Evid rule 804 [b] [5])
(Fed Rules Bankr Pro rule 9007)
(Fed Rules App Pro rule 10)
(US Const, art III, § 3)
(US Const, art I, § 8 [3])
(US Const, 14th Amend, § 1)
(US Const 14th, 15th Amends)
(US Const Fourteenth Amend)
(US Const Amend XIV)
Art. III, §3, cl. 1
Amdt. 5
(1821 NY Const, art I, § 1)
(US Const, art VI, cl 2)
'''.decode('utf8')


def main():
    scan(u'8 U. S. C. §1226a')
    import pprint
    from core import Scanner
    scanner = Scanner()
    for line in filter(None, data.splitlines()):
        print line
        pprint.pprint(list(scanner(line)))
        # import pdb;pdb.set_trace()

sec = "§"

if __name__ == '__main__':
    main()