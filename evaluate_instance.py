#!/usr/bin/env python

import json
import os

import argparse
import sys
import uuid

# TODO remove these once they have been encapsulated
from skd_domains.skd_pddl_domain import SkdPDDLDomain
from skd_domains.skd_ppddl_domain import SkdPPDDLDomain
from skd_domains.skd_spddl_domain import SkdSPDDLDomain

# from generate_instance import ProbConfig, main as encode_json
from beluga_lib.beluga_problem import BelugaProblemDecoder
import generate_instance as bgi
from evaluation.evaluators import ProbabilisticEvaluator, DeterministicEvaluator
from evaluation.planner_examples import RandomProbabilisticPlanner, RandomDeterministicPlanner
from evaluation.planner_examples import FixedPlanDeterministicPlanner
from evaluation.planner_examples import LazyAstarDeterministicPlanner, LazyAstarProbabilisticPlanner

def build_planner(args):
    if args.det_plan_file is not None:
        planner = FixedPlanDeterministicPlanner(args.det_plan_file)
    elif args.probabilistic_evaluation:
        if args.planner == 'random':
            planner = RandomProbabilisticPlanner()
        elif args.planner == 'lazy_astar':
            planner = LazyAstarProbabilisticPlanner()
    else:
        if args.planner == 'random':
            planner = RandomDeterministicPlanner(max_steps=args.max_simulation_steps)
        elif args.planner == 'lazy_astar':
            planner = LazyAstarDeterministicPlanner()
    return planner


if __name__ == "__main__":

    # ========================================================================
    # Handle command line arguments
    # ========================================================================

    parser = argparse.ArgumentParser(
        description="Beluga problem and planner evaluation tester",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-i",
        "--input",
        dest="input_problem",
        help="The problem to be tackled; if left empty, a new instance will be generated",
        default=None,
        type=str,
        required=False,
    )

    # Parse the instance generation parameters
    bgi._setup_argument_parser(parser)

    # # Specific parameters for this script
    # parser.add_argument(
    #     "-n",
    #     "--numeric",
    #     dest="numeric",
    #     help="numeric encoding, otherwise classic encoding",
    #     action="store_true",
    # )

    parser.add_argument(
        "-ms",
        "--max_steps",
        dest="max_simulation_steps",
        help="maximum number of steps within which the goal should be reached",
        default=50,
        type=int,
        required=False,
    )

    parser.add_argument(
        "-ns",
        "--num_samples",
        dest="num_samples",
        help="number of samples for the evaluation. This parameter has no effect in case of a deterministic evaluation",
        default=1,
        type=int,
        required=False,
    )

    parser.add_argument(
        "-tl",
        "--time-limit",
        dest="time_limit",
        help="time limit for the evaluation",
        default=None,
        type=int,
        required=False,
    )


    parser.add_argument(
        "-pln",
        "--planner",
        dest="planner",
        choices=('random', 'lazy_astar'),
        help="the planner to be used for the test",
        default='random',
        required=False,
    )

    parser.add_argument(
        "--prebuilt-plan",
        dest="det_plan_file",
        type=argparse.FileType('r'),
        help="When this opton is used, the evaluator will process a single, pre-built plan in JSON format. Using this option: 1) overrides plan construction; 2) requires to specify and input plan; and 3) is incompatible with probabilistic evaluation",
        default=None,
        required=False,
    )

    parser.add_argument(
        "-ppe",
        "--probabilistic-evaluation",
        dest="probabilistic_evaluation",
        help="enable probabilistic evaluation; this is automtically enable in case a probabilistic instance is generated",
        action='store_true',
        required=False,
    )

    parser.add_argument(
        "--alpha",
        dest="alpha",
        help="configure the alpha value for the score function",
        default=0.1,
        type=float,
        required=False,
    )

    # Parse command line arguments
    args = parser.parse_args()

    # Process argument to obtain the problem generator parameters
    gen_params = bgi._process_arguments(args)

    # Determine whether probabilistic evaluation should be automtically enabled
    if args.input_problem is None and gen_params['pconfig'] is not None:
        args.probabilistic_evaluation = True

    # Determine the consistency of the input options
    if args.det_plan_file is not None:
        if args.probabilistic_evaluation:
            sys.stderr.write(f'The `prebuilt-plan` option is incompatible with the probabilistic evaluation')
        if args.input_problem is None:
            sys.stderr.write(f'When using the `prebuilt-plan` option, an input problem must be specified')

    # # Build directories for the temporary files, if needed
    # if gen_params['problem_folder'] is None:
    #     gen_params['problem_folder'] = "__tmp_out_" + uuid.uuid4().hex + "__"
    #     # os.makedirs(gen_params['problem_folder'])
    # if not os.path.exists(gen_params['problem_folder']):
    #     os.makedirs(gen_params['problem_folder'])

    # ========================================================================
    # Generate a problem instance
    # ========================================================================

    # Shortcut to the problem folder
    problem_folder = gen_params['problem_folder']

    if args.input_problem is None:
        # Start the generation process
        _, problem_name, inst = bgi.main(problem_folder,
                                         gen_params['problem_name'],
                                         gen_params['config'],
                                         pconfig=gen_params['pconfig'],
                                         return_instance=True,
                                         no_show=True)
    else:
        problem_name = os.path.basename(args.input_problem)
        with open(args.input_problem) as fp:
            inst = json.load(fp, cls=BelugaProblemDecoder)

    # Determine whether the information for a probabilistic evaluation is present
    if args.probabilistic_evaluation:
        if any(f.scheduled_arrival is None for f in inst.flights):
            raise Exception('Flight arrivals times are needed for a probabilistic evaluation\n')

    # ========================================================================
    # Build and setup the planner
    # ========================================================================

    planner = build_planner(args)

    # ========================================================================
    # Build and setup the evaluator
    # ========================================================================

    if args.probabilistic_evaluation:
        evaluator = ProbabilisticEvaluator(prb=inst,
                              problem_name=problem_name,
                              problem_folder=problem_folder,
                              max_steps=args.max_simulation_steps,
                              nsamples=args.num_samples,
                              time_limit=args.time_limit,
                              planner=planner,
                              seed=gen_params['config'].seed,
                              alpha=args.alpha)
    else:
        evaluator = DeterministicEvaluator(prb=inst,
                              problem_name=problem_name,
                              problem_folder=problem_folder,
                              max_steps=args.max_simulation_steps, # TODO change this
                              time_limit=args.time_limit,
                              planner=planner,
                              alpha=args.alpha)

    # Setup the evaluator
    evaluator.setup()

    # Start the evaluation
    outcome = evaluator.evaluate()

    # If no output folder was specified, print the outcome
    if problem_folder is None:
        sys.stdout.write(outcome.to_json_str(indent=4) + '\n')

