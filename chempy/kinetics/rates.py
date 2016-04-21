# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)

import math
from .expr import Expr


class RateExpr(Expr):

    kw = ('rxn', 'ref')


class MassAction(RateExpr):
    """ Arguments: k """
    def __call__(self, variables, args=None, backend=math):
        prod = self.arg(variables, args, 0)
        for k, v in self.rxn.reac.items():
            prod *= variables[k]**v
        return prod


class ArrheniusMassAction(MassAction):
    """ Arguments: A, Ea_over_R """
    parameter_keys = ('temperature',)

    def __call__(self, variables, args=None, backend=math):
        A, Ea_over_R = self.all_args(variables, args)
        k = A*backend.exp(-Ea_over_R/variables['temperature'])
        return super(ArrheniusMassAction, self).__call__(
            variables, (k,), backend=backend)


class Radiolytic(RateExpr):
    """ Arguments: yield [amount/volume] """

    parameter_keys = ('doserate', 'density')

    def __call__(self, variables, args=None, backend=math):
        g = self.arg(variables, args, 0)
        return g*variables['doserate']*variables['density']


def law_of_mass_action_rates(conc, rsys, variables=None):
    """ Returns a generator of reaction rate expressions

    Rates from the law of mass action (:attr:`Reaction.inact_reac` ignored)
    from a :class:`ReactionSystem`.

    Parameters
    ----------
    conc : array_like
        concentrations (floats or symbolic objects)
    rsys : ReactionSystem instance
        See :class:`ReactionSystem`
    variables : dict (optional)
        to override parameters in the rate expressions of the reactions

    Examples
    --------
    >>> from chempy import ReactionSystem, Reaction
    >>> line, keys = 'H2O -> H+ + OH- ; 1e-4', 'H2O H+ OH-'
    >>> rsys = ReactionSystem([Reaction.from_string(line, keys)], keys)
    >>> next(law_of_mass_action_rates([55.4, 1e-7, 1e-7], rsys))
    0.00554

    """
    for idx_r, rxn in enumerate(rsys.rxns):
        if isinstance(rxn.param, RateExpr):
            if isinstance(rxn.param, MassAction):
                yield rxn.param(variables)
            else:
                raise ValueError("Not mass-action rate in reaction %d" % idx_r)
        else:
            rate = 1
            for substance_key, coeff in rxn.reac.items():
                s_idx = rsys.as_substance_index(substance_key)
                rate *= conc[s_idx]**coeff
            yield rate*rxn.param
