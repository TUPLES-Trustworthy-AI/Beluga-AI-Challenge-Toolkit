#!/usr/bin/env python

import json
import os
from beluga_lib.beluga_problem import BelugaProblem, BelugaProblemDecoder, BelugaProblemEncoder
from beluga_lib.problem_state import BelugaProblemState
from encoder.pddl_encoding import DomainEncoding, encode
from encoder.pddl_encoding.variant import Variant
import sys

# import argparse
# import sys
# import uuid

# # TODO remove these once they have been encapsulated
# from skd_domains.skd_pddl_domain import SkdPDDLDomain
# from skd_domains.skd_ppddl_domain import SkdPPDDLDomain
# from skd_domains.skd_spddl_domain import SkdSPDDLDomain

# # from generate_instance import ProbConfig, main as encode_json
# import generate_instance as bgi
# from evaluation.evaluators import ProbabilisticEvaluator
# from evaluation.planner_examples import RandomProbabilisticPlanner

def generate_pddl(
        beluga_problem: BelugaProblem,
        state : BelugaProblemState = None,
        classic : bool = True,
        probabilistic : bool = False
    ):

    variant = Variant()
    variant.classic = classic
    variant.probabilistic = probabilistic

    domain_encoding = DomainEncoding(variant, beluga_problem)
    # domain_str = domain_encoding.domain.to_pddl("beluga")

    problem_name = 'Internal Beluga Problem Instance'
    pddl_problem = encode(
        problem_name,
        beluga_problem,
        domain_encoding.domain,
        variant,
        state
    )
    problem_str = pddl_problem.to_pddl(problem_name)

    # return domain_str, problem_str
    return problem_str

if __name__ == "__main__":

    # ========================================================================
    # Read the problem
    # ========================================================================

    prb_file = sys.argv[1]
    with open(prb_file) as fp:
        prb = json.load(fp, cls=BelugaProblemDecoder)

    print(prb_file)

    # prb_file = os.path.join('problem_and_state_test', 'problem.json')

    # print('=' * 78)
    # print('PROBLEM')
    # print(json.dumps(prb, cls=BelugaProblemEncoder, indent=4))

    state_folder = sys.argv[2]
    for state_file in os.listdir(state_folder):
        if not state_file.startswith('ba_state'):
            continue

        print(state_file)

        state_path = '/'.join([state_folder, state_file])

        # ========================================================================
        # Read the state
        # ========================================================================

        # state_file = os.path.join('problem_and_state_test', 'state0.json')
        with open(state_path) as fp:
            state_json = json.load(fp)
            state = BelugaProblemState.from_json_obj(state_json, prb)

        # print('=' * 78)
        # print('STATE')
        # print(json.dumps(state.to_json_obj(), indent=4))


        # ========================================================================
        # Trigger PDDL generation
        # ========================================================================

        try:
            problem_str = generate_pddl(beluga_problem=prb,
                                        state=state,
                                        classic=True,
                                        probabilistic=False)
        except:
            print("skip: " + state_file)
            continue

        # print('=' * 78)
        # print('PDDL PROBLEM')
        out_folder = sys.argv[3]
        prb_name = state_file.replace('.json', '')
        with open('/'.join([out_folder, prb_name + '.pddl']), 'w') as fp:
            fp.write(problem_str)
