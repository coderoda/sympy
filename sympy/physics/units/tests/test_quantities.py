# -*- coding: utf-8 -*-

from __future__ import division

from sympy import (Abs, Add, Basic, Function, Number, Rational, S, Symbol,
    diff, exp, integrate, log, sin, sqrt, symbols)
from sympy.physics.units import (amount_of_substance, convert_to, find_unit,
    volume)
from sympy.physics.units.definitions import (amu, au, centimeter, coulomb,
    day, energy, foot, grams, hour, inch, kg, km, m, meter, mile, millimeter,
    minute, pressure, quart, s, second, speed_of_light, temperature, bit,
    byte, kibibyte, mebibyte, gibibyte, tebibyte, pebibyte, exbibyte)

from sympy.physics.units.dimensions import Dimension, charge, length, time
from sympy.physics.units.prefixes import PREFIXES, kilo
from sympy.physics.units.quantities import Quantity
from sympy.utilities.pytest import XFAIL, raises

k = PREFIXES["k"]


def test_str_repr():
    assert str(kg) == "kilogram"

def test_eq():
    # simple test
    assert 10*m == 10*m
    assert 10*m != 10*s


def test_convert_to():
    q = Quantity("q1", length, 5000)
    assert q.convert_to(m) == 5000*m

    assert speed_of_light.convert_to(m / s) == 299792458 * m / s
    # TODO: eventually support this kind of conversion:
    # assert (2*speed_of_light).convert_to(m / s) == 2 * 299792458 * m / s
    assert day.convert_to(s) == 86400*s

    # Wrong dimension to convert:
    assert q.convert_to(s) == q
    assert speed_of_light.convert_to(m) == speed_of_light


def test_Quantity_definition():
    q = Quantity("s10", time, 10, "sabbr")

    assert q.scale_factor == 10
    assert q.dimension == time
    assert q.abbrev == Symbol("sabbr")

    u = Quantity("u", length, 10, abbrev="dam")

    assert u.dimension == length
    assert u.scale_factor == 10
    assert u.abbrev == Symbol("dam")

    km = Quantity("km", length, kilo)
    assert km.scale_factor == 1000
    assert km.func(*km.args) == km
    assert km.func(*km.args).args == km.args

    v = Quantity("u", length, 5*kilo)
    assert v.dimension == length
    assert v.scale_factor == 5 * 1000

    raises(ValueError, lambda: Quantity('invalid', 'dimension', 1))
    raises(ValueError, lambda: Quantity('mismatch', length, kg))


def test_abbrev():
    u = Quantity("u", length, 1)
    assert u.name == Symbol("u")
    assert u.abbrev == Symbol("u")

    u = Quantity("u", length, 2, "om")
    assert u.name == Symbol("u")
    assert u.abbrev == Symbol("om")
    assert u.scale_factor == 2
    assert isinstance(u.scale_factor, Number)

    u = Quantity("u", length, 3*kilo, "ikm")
    assert u.abbrev == Symbol("ikm")
    assert u.scale_factor == 3000


def test_print():
    u = Quantity("unitname", length, 10, "dam")
    assert repr(u) == "unitname"
    assert str(u) == "unitname"


def test_Quantity_eq():
    u = Quantity("u", length, 10, "dam")

    v = Quantity("v1", length, 10)
    assert u != v

    v = Quantity("v2", time, 10, "ds")
    assert u != v

    v = Quantity("v3", length, 1, "dm")
    assert u != v


def test_add_sub():
    u = Quantity("u", length, 10)
    v = Quantity("v", length, 5)
    w = Quantity("w", time, 2)

    assert isinstance(u + v, Add)
    assert (u + v.convert_to(u)) == (1 + S.Half)*u
    # TODO: eventually add this:
    # assert (u + v).convert_to(u) == (1 + S.Half)*u
    assert isinstance(u - v, Add)
    assert (u - v.convert_to(u)) == S.Half*u
    # TODO: eventually add this:
    # assert (u - v).convert_to(u) == S.Half*u

def test_abs():
    v_w1 = Quantity('v_w1', length/time, meter/second)
    v_w2 = Quantity('v_w2', length/time, meter/second)
    v_w3 = Quantity('v_w3', length/time, meter/second)
    expr = v_w3 - Abs(v_w1 - v_w2)

    Dq = Dimension(Quantity.get_dimensional_expr(expr))
    assert Dimension.get_dimensional_dependencies(Dq) == {
        'length': 1,
        'time': -1,
    }
    assert meter == sqrt(meter**2)


def test_check_unit_consistency():
    u = Quantity("u", length, 10)
    v = Quantity("v", length, 5)
    w = Quantity("w", time, 2)

    def check_unit_consistency(expr):
        Quantity._collect_factor_and_dimension(expr)

    raises(ValueError, lambda: check_unit_consistency(u + w))
    raises(ValueError, lambda: check_unit_consistency(u - w))
    raises(ValueError, lambda: check_unit_consistency(u + 1))
    raises(ValueError, lambda: check_unit_consistency(u - 1))


def test_mul_div():
    u = Quantity("u", length, 10)

    assert 1 / u == u**(-1)
    assert u / 1 == u

    v1 = u / Quantity("t", time, 2)
    v2 = Quantity("v", length / time, 5)

    # Pow only supports structural equality:
    assert v1 != v2
    assert v1 == v2.convert_to(v1)

    # TODO: decide whether to allow such expression in the future
    # (requires somehow manipulating the core).
    # assert u / Quantity('l2', length, 2) == 5

    assert u * 1 == u

    ut1 = u * Quantity("t", time, 2)
    ut2 = Quantity("ut", length*time, 20)

    # Mul only supports structural equality:
    assert ut1 != ut2
    assert ut1 == ut2.convert_to(ut1)

    # Mul only supports structural equality:
    assert u * Quantity("lp1", length**-1, 2) != 20

    assert u**0 == 1
    assert u**1 == u
    # TODO: Pow only support structural equality:
    assert u ** 2 != Quantity("u2", length ** 2, 100)
    assert u ** -1 != Quantity("u3", length ** -1, 0.1)

    assert u ** 2 == Quantity("u2", length ** 2, 100).convert_to(u)
    assert u ** -1 == Quantity("u3", length ** -1, S.One/10).convert_to(u)


def test_units():
    assert convert_to((5*m/s * day) / km, 1) == 432
    assert convert_to(foot / meter, meter) == Rational('0.3048')
    # amu is a pure mass so mass/mass gives a number, not an amount (mol)
    # TODO: need better simplification routine:
    assert str(convert_to(grams/amu, grams).n(2)) == '6.0e+23'

    # Light from the sun needs about 8.3 minutes to reach earth
    t = (1*au / speed_of_light) / minute
    # TODO: need a better way to simplify expressions containing units:
    t = convert_to(convert_to(t, meter / minute), meter)
    assert t == 49865956897/5995849160

    # TODO: fix this, it should give `m` without `Abs`
    assert sqrt(m**2) == Abs(m)
    assert (sqrt(m))**2 == m

    t = Symbol('t')
    assert integrate(t*m/s, (t, 1*s, 5*s)) == 12*m*s
    assert (t * m/s).integrate((t, 1*s, 5*s)) == 12*m*s


def test_issue_quart():
    assert convert_to(4 * quart / inch ** 3, meter) == 231
    assert convert_to(4 * quart / inch ** 3, millimeter) == 231


def test_issue_5565():
    raises(ValueError, lambda: m < s)
    assert (m < km).is_Relational


def test_find_unit():
    assert find_unit('coulomb') == ['coulomb', 'coulombs', 'coulomb_constant']
    assert find_unit(coulomb) == ['C', 'coulomb', 'coulombs']
    assert find_unit(charge) == ['C', 'coulomb', 'coulombs']
    assert find_unit(inch) == [
        'm', 'au', 'cm', 'dm', 'ft', 'km', 'ly', 'mi', 'mm', 'nm', 'pm', 'um',
        'yd', 'nmi', 'feet', 'foot', 'inch', 'mile', 'yard', 'meter', 'miles',
        'yards', 'inches', 'meters', 'micron', 'microns', 'decimeter',
        'kilometer', 'lightyear', 'nanometer', 'picometer', 'centimeter',
        'decimeters', 'kilometers', 'lightyears', 'micrometer', 'millimeter',
        'nanometers', 'picometers', 'centimeters', 'micrometers',
        'millimeters', 'nautical_mile', 'planck_length', 'nautical_miles', 'astronomical_unit',
        'astronomical_units']
    assert find_unit(inch**-1) == ['D', 'dioptre', 'optical_power']
    assert find_unit(length**-1) == ['D', 'dioptre', 'optical_power']
    assert find_unit(inch ** 3) == [
        'l', 'cl', 'dl', 'ml', 'liter', 'quart', 'liters', 'quarts',
        'deciliter', 'centiliter', 'deciliters', 'milliliter',
        'centiliters', 'milliliters']
    assert find_unit('voltage') == ['V', 'v', 'volt', 'volts']


def test_Quantity_derivative():
    x = symbols("x")
    assert diff(x*meter, x) == meter
    assert diff(x**3*meter**2, x) == 3*x**2*meter**2
    assert diff(meter, meter) == 1
    assert diff(meter**2, meter) == 2*meter


def test_sum_of_incompatible_quantities():
    raises(ValueError, lambda: meter + 1)
    raises(ValueError, lambda: meter + second)
    raises(ValueError, lambda: 2 * meter + second)
    raises(ValueError, lambda: 2 * meter + 3 * second)
    raises(ValueError, lambda: 1 / second + 1 / meter)
    raises(ValueError, lambda: 2 * meter*(mile + centimeter) + km)

    expr = 2 * (mile + centimeter)/second + km/hour
    assert expr in Basic._constructor_postprocessor_mapping
    for i in expr.args:
        assert i in Basic._constructor_postprocessor_mapping


def test_quantity_dimension_not_registered():
    d = Dimension("someDimension")
    raises(ValueError, lambda: Quantity("q", d, 1))
    raises(ValueError, lambda: Quantity("q", d/length, 1))


def test_quantity_postprocessing():
    q1 = Quantity('q1', length*pressure**2*temperature/time)
    q2 = Quantity('q2', energy*pressure*temperature/(length**2*time))
    assert q1 + q2
    q = q1 + q2
    Dq = Dimension(Quantity.get_dimensional_expr(q))
    assert Dimension.get_dimensional_dependencies(Dq) == {
        'length': -1,
        'mass': 2,
        'temperature': 1,
        'time': -5,
    }


def test_factor_and_dimension():
    assert (3000, Dimension(1)) == Quantity._collect_factor_and_dimension(3000)
    assert (1001, length) == Quantity._collect_factor_and_dimension(meter + km)
    assert (2, length/time) == Quantity._collect_factor_and_dimension(
        meter/second + 36*km/(10*hour))

    x, y = symbols('x y')
    assert (x + y/100, length) == Quantity._collect_factor_and_dimension(
        x*m + y*centimeter)

    cH = Quantity('cH', amount_of_substance/volume)
    pH = -log(cH)

    assert (1, volume/amount_of_substance) == Quantity._collect_factor_and_dimension(
        exp(pH))

    v_w1 = Quantity('v_w1', length/time, S(3)/2*meter/second)
    v_w2 = Quantity('v_w2', length/time, 2*meter/second)
    expr = Abs(v_w1/2 - v_w2)
    assert (S(5)/4, length/time) == \
        Quantity._collect_factor_and_dimension(expr)

    expr = S(5)/2*second/meter*v_w1 - 3000
    assert (-(2996 + S(1)/4), Dimension(1)) == \
        Quantity._collect_factor_and_dimension(expr)

    expr = v_w1**(v_w2/v_w1)
    assert ((S(3)/2)**(S(4)/3), (length/time)**(S(4)/3)) == \
        Quantity._collect_factor_and_dimension(expr)


@XFAIL
def test_factor_and_dimension_with_Abs():
    v_w1 = Quantity('v_w1', length/time, S(3)/2*meter/second)
    expr = v_w1 - Abs(v_w1)
    assert (0, length/time) == Quantity._collect_factor_and_dimension(expr)


def test_dimensional_expr_of_derivative():
    l = Quantity('l', length, 36 * km)
    t = Quantity('t', time, hour)
    t1 = Quantity('t1', time, second)
    x = Symbol('x')
    y = Symbol('y')
    f = Function('f')
    dfdx = f(x, y).diff(x, y)
    dl_dt = dfdx.subs({f(x, y): l, x: t, y: t1})
    assert Quantity.get_dimensional_expr(dl_dt) ==\
        Quantity.get_dimensional_expr(l / t / t1) ==\
        Symbol("length")/Symbol("time")**2
    assert Quantity._collect_factor_and_dimension(dl_dt) ==\
        Quantity._collect_factor_and_dimension(l / t / t1) ==\
        (10, length/time**2)


def test_get_dimensional_expr_with_function():
    v_w1 = Quantity('v_w1', length / time, meter / second)
    assert Quantity.get_dimensional_expr(sin(v_w1)) == \
        sin(Quantity.get_dimensional_expr(v_w1))


def test_get_dimensional_expr_with_function_1():
    v_w1 = Quantity('v_w1', length / time, meter / second)
    v_w2 = Quantity('v_w2', length / time, meter / second)
    assert Quantity.get_dimensional_expr(sin(v_w1/v_w2)) == 1


def test_binary_information():
    assert convert_to(kibibyte, byte) == 1024*byte
    assert convert_to(mebibyte, byte) == 1024**2*byte
    assert convert_to(gibibyte, byte) == 1024**3*byte
    assert convert_to(tebibyte, byte) == 1024**4*byte
    assert convert_to(pebibyte, byte) == 1024**5*byte
    assert convert_to(exbibyte, byte) == 1024**6*byte

    assert kibibyte.convert_to(bit) == 8*1024*bit
    assert byte.convert_to(bit) == 8*bit

    a = 10*kibibyte*hour

    assert convert_to(a, byte) == 10240*byte*hour
    assert convert_to(a, minute) == 600*kibibyte*minute
    assert convert_to(a, [byte, minute]) == 614400*byte*minute
