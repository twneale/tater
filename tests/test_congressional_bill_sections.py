
import json
from nose.tools import eq_

from pygments.token import Token

from tater.stuff import USBillTokenizer


def getdata(string, expected):
    return list(USBillTokenizer().tokenize(string)), expected


def test_cow():
    string = 'Section 1142(b) of title 10, United States Code'
    expected = [
        (0, Token.Division.Name, 'Section'),
        (8, Token.Division.Enum, '1142'),
        (12, Token.Punctuation.OpenParen, '('),
        (13, Token.Division.PathEnum, 'b'),
        (14, Token.Punctuation.CloseParen, ')'),
        (16, Token.Of, 'of'),
        (19, Token.Division.Name, 'title'),
        (25, Token.Division.Enum, '10'),
        (29, Token.USCode, 'United States Code'),
        ]

    eq_(*getdata(string, expected))


def test_cow1():
    string = (
        'Section 3686 of the Energy Employees '
        'Occupational Illness Compensation Program '
        'Act of 2000 (42 U.S.C. 7385s-15)')
    expected = [
        (0, Token.Division.Name, 'Section'),
        (8, Token.Division.Enum, '3686'),
        (13, Token.Punctuation.OfThe, 'of the'),
        (20, Token.PopularName,
         ('Energy Employees Occupational Illness '
          'Compensation Program Act of 2000')),
        (92, Token.Division.Title, '42'),
        (95, Token.USCode, 'U.S.C.'),
        (102, Token.Division.Enum, '7385s-15'),
        ]

    eq_(*getdata(string, expected))


def test_cow2():
    string = 'Section 41 of title 28, United States Code'
    expected = [
        (0, Token.Division.Name, 'Section'),
        (8, Token.Division.Enum, '41'),
        (11, Token.Of, 'of'),
        (14, Token.Division.Name, 'title'),
        (20, Token.Division.Enum, '28'),
        (24, Token.USCode, 'United States Code'),
        ]

    eq_(*getdata(string, expected))


def test_cow4():
    string = ('Section 611(e)(2)(C) of the Individuals with '
              'Disabilities Education Act (20 U.S.C. 1411(e)(2)(C))')
    expected = [
        (0, Token.Division.Name, 'Section'),
        (8, Token.Division.Enum, '611'),
        (11, Token.Punctuation.OpenParen, '('),
        (12, Token.Division.PathEnum, 'e'),
        (13, Token.Punctuation.CloseParen, ')'),
        (14, Token.Punctuation.OpenParen, '('),
        (15, Token.Division.PathEnum, '2'),
        (16, Token.Punctuation.CloseParen, ')'),
        (17, Token.Punctuation.OpenParen, '('),
        (18, Token.Division.PathEnum, 'C'),
        (19, Token.Punctuation.CloseParen, ')'),
        (21, Token.Punctuation.OfThe, 'of the'),
        (28, Token.PopularName, 'Individuals with Disabilities Education Act'),
        (73, Token.Division.Title, '20'),
        (76, Token.USCode, 'U.S.C.'),
        (83, Token.Division.Enum, '1411'),
        (87, Token.Punctuation.OpenParen, '('),
        (88, Token.Division.PathEnum, 'e'),
        (89, Token.Punctuation.CloseParen, ')'),
        (90, Token.Punctuation.OpenParen, '('),
        (91, Token.Division.PathEnum, '2'),
        (92, Token.Punctuation.CloseParen, ')'),
        (93, Token.Punctuation.OpenParen, '('),
        (94, Token.Division.PathEnum, 'C'),
        (95, Token.Punctuation.CloseParen, ')'),
        ]

    eq_(*getdata(string, expected))


def test_cow5():
    string = 'Section 3(a)(2) of the Securities Act of 1933 (15 U.S.C. 77c(a)(2))'
    expected = [
        (0, Token.Division.Name, 'Section'),
        (8, Token.Division.Enum, '3'),
        (9, Token.Punctuation.OpenParen, '('),
        (10, Token.Division.PathEnum, 'a'),
        (11, Token.Punctuation.CloseParen, ')'),
        (12, Token.Punctuation.OpenParen, '('),
        (13, Token.Division.PathEnum, '2'),
        (14, Token.Punctuation.CloseParen, ')'),
        (16, Token.Punctuation.OfThe, 'of the'),
        (23, Token.PopularName, 'Securities Act of 1933'),
        (47, Token.Division.Title, '15'),
        (50, Token.USCode, 'U.S.C.'),
        (57, Token.Division.Enum, '77c'),
        (60, Token.Punctuation.OpenParen, '('),
        (61, Token.Division.PathEnum, 'a'),
        (62, Token.Punctuation.CloseParen, ')'),
        (63, Token.Punctuation.OpenParen, '('),
        (64, Token.Division.PathEnum, '2'),
        (65, Token.Punctuation.CloseParen, ')'),
        ]

    eq_(*getdata(string, expected))


def test_cow3():
    string = ('Part D of title III of the Public Health '
              'Service Act (42 U.S.C. 254b et seq.)')
    expected = [
        (0, Token.Division.Name, 'Part'),
        (5, Token.Division.Enum, 'D'),
        (7, Token.Of, 'of'),
        (10, Token.Division.Name, 'title'),
        (16, Token.Division.Enum, 'III'),
        (20, Token.Punctuation.OfThe, 'of the'),
        (27, Token.PopularName, 'Public Health Service Act'),
        (54, Token.Division.Title, '42'),
        (57, Token.USCode, 'U.S.C.'),
        (64, Token.Division.Enum, '254b'),
        ]

    eq_(*getdata(string, expected))

