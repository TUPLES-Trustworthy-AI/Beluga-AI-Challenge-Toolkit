# EXTENDED Version

This branch contains an extended version of the compeition problem definition.
The JSON econding now allows trailers and hangars to hold an initial jig.

```
"trailers_beluga": [
    {
        "name": "BT1",
        "jig": null
    },
    ...
],
"trailers_factory": [
    {
        "name": "FT1",
        "jig": null
    },
    ...
],
"hangars": [
    {
        "name": "Hangar1",
        "jig": null
    },
    ...
],
```

`null` indicated that the trailer/hangar is initially empty. To refer to a jig placed in the trailer or hanger its name is used e.g.

```
{
    "name": "BT1",
    "jig": "jig003"
}
```        

# Beluga Competition Toolkit

The competition toolkit is a set of tools which help generate and simulate problems in different formalisms (PDDL, RL, pure json, etc.).
The scripts also serve as examples on how to use the competition API for your own scripts. The following list provides a high level view
of the provided scripts, which are detailed in the subsequent sections of the Readme file:

- [Problem generation](#problem-generator): the `generate_instance.py` script allows a user to generate a JSON file representing a specific Beluga problem instance based on configuration variables passed to the script as arguments ;
- [PDDL encoding](#pddl-encoding): the JSON files generated with the previous script can be then passed to the `json2PDDL.py`
  (resp. `encode_instances.py`) script to encode one (resp. multiple) PDDL instances, in either classical or numeric PDDL flavors ;
- [Scikit-decide domains](#scikit-decide-domain-tester): once PDDL files have been generated with the previous script, they can be passed
  to scikit-decide domains, where some of them include noise action effects for probabilistic reasoning (see details in the linked section) ;
  those domains can be used to call grounded search solvers (e.g. A\* in deterministic settings, LAO\* or LRTDP in probabilistic settings)
  or simulation-based solvers (e.g. MCTS, RL), as exemplified in the `generate_simulate_test.py` script ;
- [Gymnasium environments](#gymnasium-environment-tester): the previous scikit-decide domains can also be automatically casted to Gymnasium
  environments by specializing the `BelugaGymCompatibleDomain` class whose aim is to define tensor-based observation and action spaces for use
  with deep reinforcement learning algorithms; while we provide a simple observation and space encodings in an example specialized class in
  the `generate_solve_rllib_test.py` script, we strongly advise our RL friends to implement their own specialized class for better learning
  and generalization capabilities ;
- [Evaluator](#evaluator): we finally provide the `evaluate_instance.py` script where users can evaluate their solutions by using the same
  protocol as the one employed by the official competition evaluation and a similar API (though not implemented via a web service, which will instead be required for the final submission)

In this file you will also find information about the uncertainty model used in the probabilistic challenge and on the distribution that was used to obtain all official benchmarks for scalability challenges in the competition.

## Problem Generator

The problem generator generates a random Beluga instance as a JSON file.

With the script

```sh
    generate_instance.py [-h] [-s SEED] [-or OCCUPANCY_RATE_RACKS] [-t JIG_T_DIST] [-f NUM_FLIGHTS] [-us {rack_space_general,outgoing_flight_not_sat,schedule_clashes}] [-v] [-o OUT] [-on OUT_NAME] [-pp] [-pm {arrivals,ppddl}] [-pw PROBABILISTIC_WINDOW]
```

you can generate one instance based on a default configuration which allows
to specify a number of parameters.

For a list of possible parameters and descriptions of them call

```sh
    generate_instance.py -h
```

results it the following description:

- `-h`, `--help` : show this help message and exit
- `-s` SEED, `--seed` SEED: seed for the random generator
- `-or` OCCUPANCY_RATE_RACKS, `--occupancy-rate-racks` OCCUPANCY_RATE_RACKS
  fraction of rack space that is initially occupied
- `-t` JIG_T_DIST, `--jig-type-distribution` JIG_T_DIST
  distribution of jigs types: (0) uniform, (1) small jigs preferred, (2) large jigs preferred (default: 1)
- `-f` NUM_FLIGHTS, `--num-flights` NUM_FLIGHTS
  number of incoming and outgoing Beluga flights
- `-us` [rack_space_general,outgoing_flight_not_sat,schedule_clashes ...], `--unsolvable` [rack_space_general,outgoing_flight_not_sat,schedule_clashes ...]
  scenario based on which the generator tries to generate an unsolvable instance
- `-v`, `--verbose` print debug output
- `-o` OUT, `--out` OUT output folder for the problem, if no folder is given, the problem is printed onto stdout
- `-on` OUT_NAME, `--out-name` OUT_NAME
  name for the problem, if no name is defined, a name based on the number of jigs, jig types, racks, the exact occupancy rate, the number of flights, the seed
  and potentially the unsolvability scenarios is generated
- `-pp`, `--probabilistic` Enables the probabilistic model, triggering the generation of probabilistic instances (default: False)
- `-pm {arrivals,ppddl}`, `--probabilistic-model {arrivals,ppddl}`
  Controls the type of probabilistic model, if the `-pp` option is enabled. If the `arrivals` options is used (the default), then the instance will contain only arrival times and will be suitable for a more realistic uncertainty semantic where flights are subject to stochastic delay; if the `ppddl` option is used, the instance will include information on uncertainty, specified in terms of probabilities of transition between abstract states. Every abstract state is identified by the sequence of a configurable number of the last flights (default: arrivals)
- `-pw PROBABILISTIC_WINDOW`, `--probabilistic-window PROBABILISTIC_WINDOW`
  Length of the sequence of flights used as the abstract state in the 'ppddl' probabilistic model. This parameter is ignored unless 'ppddl' probabilistic mode is enabled (default: 1)

The file `configuration/default_configuration.py` defines
the values of the remaining parameters of the generator.
They are described in more detail below.
In the competition these parameters are fixed, and we only consider instances
with varying occupancy rate, jig type distribution and number of flights.

When no unsolvability scenario is specified, then the generator tries to
generate a solvable instance, however the generator does **not ensure solvability**.
The individual unsolvability scenarios are described below.

To generate a whole range of instances the script

```sh
    generate_instances.py [-h] -c CONFIG_FILE [-y] -o OUTPUT_FOLDER
```

can be used. The `CONFIG_FILE` specifies the occupancy rate, jig type 
distribution and number of flights in the format: 

```csv
saturation,jig_type_dist,n_flights
80.0,0.0,49.0
20.0,0.0,142.0
...
```
where the `saturation`, `jig_type_dist` and `n_flights` refer to the 
parameters `--occupancy-rate-racks`, `--jig-type-distribution` and 
`--num-flights` respectively.

The parameters for the provided set of training instances can be found in the [benchmarks repository](https://github.com/TUPLES-Trustworthy-AI/Beluga-AI-Challenge-Benchmarks).

### Fixed Configuration

In addition to the instance generator can be configured with the following parameters. 
These also include distributions from which we draw a samples 
during instance generation. `configurations/default_configuration.py`
contains the parameters and distributions we consider for the competition.

#### Jigs

- We use a fix set of 5 jig types ranging from 4 to 32 units of length.

- `distribution_initial_jig_state`: Used to determine whether a jig initially
  on the racks is loaded or empty. Here we select 50/50 between loaded or
  empty.

#### Racks

- The rack size is sampled uniformly between 20 and 40
- The number of racks depends on the number of flights and ranges between 1 and 20.

#### Flights

- The storage capacity of the Beluga is fixed to 40.
- `max_delivery_buffer`: maximal number of flights a jig waits before it is
  scheduled in a production line. For less than 50 flights it is
   `num_flights * 0.5` for more than 50 flights it is 25.
- `distribution_delivery_buffer`: Used to sample how many flights a
  jig waits before it is scheduled in the production line.
  Must be less or equal to `max_delivery_buffer`.
  We use a truncated normal distribution with center `0.25 * max_delivery_buffer`, 
  a standard deviation of `0.5 * max_delivery_buffer`
  a lower bound of `1` and an upper bound of `max_delivery_buffer`.

- `distribution_next_production_line`: Used to determine which production line
  is scheduled next. The distribution depends on the number of jigs
  that have been delivered to a production line since the last delivery to any
  production line.
  We sample uniformly form a list of production lines, where the number of
  occurrences for each production line corresponds to how many jigs have been
  scheduled since this line has been chosen last.

#### Trailers & Hangars

The number of trailers on the Beluga and on the factory side are sampled
uniformly between 1 and 3. The same holds for the hangars.

#### Production Lines

The number of trailers on the Beluga and on the factory side are sampled
uniformly between 1 and 3.
During the instance generation the parts are scheduled randomly between the
production lines. To counteract an uneven distribution over the production lines,
lines where fewer parts have been scheduled are preferred.

### Unsolvability Scenario

In case an unsolvable instance is needed the following scenarios are
supported:

- `RACK_SPACE_GENERAL`: Incoming flights carry the maximal number of jigs it is 
possible to fit in the Beluga, regardless of whether the racks have sufficient 
space to accommodate them. The outgoing flights are limited to at most one jig. 
This eventually results in more jigs on site than can fit on the racks and trailers. 
Depending on the number of flights, this strategy might not lead to an unsolvable instance.

- `OUTGOING_FLIGHT_NOT_SAT`: A random outgoing flight requires more jigs of a 
certain type than the number of jigs of that type that are on site, 
causing infeasibility.

- `SCHEDULE_CLASHES`: This scenario focuses on building instances with schedule 
clashes. A clash occurs for two loaded jigs J1 J2, if J2 arrives on a later flight 
than J1 but J2 needs to be delivered to  a production line before J1. To build 
those instances, we modify the generator of the production schedule, by filling 
production schedules greedily to consume jigs in reverse order of their arrival.  
This is a more advanced version of the `OUTGOING_FLIGHT_NOT_SAT` scenario. 
However, it does not guarantee unsolvability.

## PDDL Encoding

We provide a **classical** as well as a **numeric** PDDL encoding.

In the classical encoding the rack and jig sizes as well as the free space in each
rack are encoded by individual `numXX` objects.
The predicate `fit(a-b,b,a)` is then used to determine whether a jig still fits into
a rack.
For the numeric encoding however the rack and jig sizes are defined by functions
and the _fit_ check is done by a numeric comparison.

Except for these differences the classical and numeric encoding are the same.

To encode one instance you can use the script

    json2PDDL.py [-h] [-o PROBLEM_OUT] -i INSTANCE [-n]

It takes one JSON instance description and encodes it per default as
a classic PDDL problem or with `-n` using the numeric encoding.
A matching domain file is automatically generated.

To encode multiple instances use

    encode_instances.py [-h] [-n] -i I -o O [-y]

It encodes all instances and generates matching domain files.

## Scikit-decide Domain Tester

The toolkit includes a script for testing the three scikit-decide domains developed for the competition; these can be used by the competitors to assist the development of their own solution, they are employed by the (trivial) example planners included in the toolkit, and are used as the basis for the evaluation scripts.

The three domains are built around the `plado` module and are respectively:

- `SkdPDDLDomain`: a deterministic problem domain that can rely on either the classic or the numeric PDDL encodings used in the competition
- `SkdSPDDLDomain`: a probabilistic domain suitable for use in Reinforcement Learning solutions
- `SkdPPDDLDomain`: a probabilistic domain compatible with the abstract probabilistic model and with the coresponding PPDDL encoding

The testing script generates a problem instance and then triggers a simulation process, where a valid action are sampled at random at every step.

The usage is as follows:

```sh
usage: generate_simulate_test.py [-h] [-s SEED] [-njt NUM_JIG_TYPES] [-or OCCUPANCY_RATE_RACKS] [-r NUM_RACKS] [-msr MAX_SIZE_RACKS]
                                 [-f NUM_FLIGHTS] [-sb SIZE_BELUGA] [-bt NUM_BELUGA_TRAILERS] [-ft NUM_FACTORY_TRAILERS] [-hs NUM_HANGARS]
                                 [-p NUM_PRODUCTION_LINES] [-us {rack_space_general,outgoing_flight_not_sat,schedule_clashes}] [-v]
                                 [-o OUT] [-on OUT_NAME] [-pp] [-pm {arrivals,ppddl}] [-pw PROBABILISTIC_WINDOW] [-n]
                                 [-ms MAX_SIMULATION_STEPS]
```

The configuration parameters include those used by the problem generator, plus:

- `-n`
  numeric encoding, otherwise classic encoding (default: False)
- `-ms MAX_SIMULATION_STEPS`
  maximum number of simulation steps unless the goal is reached before (default: None)

## Gymnasium Environment Tester

The toolkit provides a way to cast each of the 3 above scikit-decide Beluga domains to
a gymnasium environment to be used by deep reinforcement learning approaches. This can
be done in 2 steps:

1. Specialize the `BelugaGymCompatibleDomain` class defined in the `skd_gym_domain.py`
   script to your tensor representation needs ;
2. Pass your specialized domain class to the `BelugaGymEnv` class defined in the same
   script; this will be your gym environment.

The `generate_solve_rllib_test.py` script gives an example of such a specialized
gym-compatible domain class that can make each of the original domain classes (i.e.
`SkdPDDLDomain`, `SkdSPDDLDomain` or `SkdPPDDLDomain`) use state and action tensors.
The script further shows how to pass an instance of this gym-compatible domain class
to the `BelugaGymEnv` class, and how to call RLlib's PPO algorithm on this gym
environment class. The script can be used as follows:

```sh
usage: generate_solve_rllib_test.py [-h] [-s SEED] [-njt NUM_JIG_TYPES] [-or OCCUPANCY_RATE_RACKS] [-r NUM_RACKS] [-msr MAX_SIZE_RACKS]
                                    [-f NUM_FLIGHTS] [-sb SIZE_BELUGA] [-bt NUM_BELUGA_TRAILERS] [-ft NUM_FACTORY_TRAILERS] [-hs NUM_HANGARS]
                                    [-p NUM_PRODUCTION_LINES] [-us {rack_space_general,outgoing_flight_not_sat,schedule_clashes}] [-v]
                                    [-o OUT] [-on OUT_NAME] [-pp] [-pm {arrivals,ppddl}] [-pw PROBABILISTIC_WINDOW] [-n]
                                    [-ms MAX_SIMULATION_STEPS]
```

The configuration parameters are the same as the ones of the scikit-decide domain tester.

## Evaluator

The toolkit includes a template for an evaluation script relying on the same protocol employed for the official competition. This can be useful both for testing the API of the solutions developed by the competitor, and for computing the official KPIs.

In particular, this evaluation script is designed to test solutions complying with the API in `evaluation/planner_api.py`, and provides support for naive example implementations (based on random action sampling and the Lazy A* solver from scikit-decide). The code for these examples can be found in `evaluation/planner_examples.py` and can be used as a starting point for the competitors' code.

The script can be used or modified to handle new solution approaches as follows:

- Competitors can modify the `build_planner` function in `evaluate_instance.py` to add support for their own approach
- For the deterministic track, it is also possible to use the script to evaluate a pre-built plan, in JSON format, by using the `--prebuilt-plan` command line option; this approach is not available for the probabilistic track, for which the goal is building a policy rather than a single plan

We stress that this script should be considered just a template. The official evaluation will rely on an implementation based on web services. A default wrapper will be made available for solution approaches based on the API from `evaluation/planner_api.py`.

The evaluation script can be used as follows:

```sh
usage: evaluate_instance.py [-h] [-i INPUT_PROBLEM] [-s SEED] [-or OCCUPANCY_RATE_RACKS] [-t JIG_T_DIST] [-f NUM_FLIGHTS]
                            [-us {rack_space_general,outgoing_flight_not_sat,schedule_clashes}] [-v] [-o OUT] [-on OUT_NAME] [-pp] [-pm {arrivals,ppddl}]
                            [-ms MAX_SIMULATION_STEPS] [-ns NUM_SAMPLES] [-tl TIME_LIMIT] [-pln {random,lazy_astar}] [--prebuilt-plan DET_PLAN_FILE] [-ppe]
```

The script can be used to evaluate a solution on an existing instance (by specifying the `--input` parameter) or on an instance generated on the fly. The parameters include those used by the generator (which are ignored in case `--input` is used), plus:

- `-ms MAX_SIMULATION_STEPS`, `--max_steps MAX_SIMULATION_STEPS`
  maximum number of steps (per jig) within which the goal should be reached. The number is specified pe jig, so as to naturally scale with the instance size.
  The default value of 20 is generous, meaning that it should be hit only by plans making a lot of unnecessary swaps. (default: 20)
- `-ns NUM_SAMPLES`, `--num_samples NUM_SAMPLES`
  number of samples for the evaluation. This parameter has no effect in case of a deterministic evaluation (default: 1) -tl TIME_LIMIT, --time-limit TIME_LIMIT
  time limit for the evaluation (default: None)
- `tl TIME_LIMIT`, `--time-limit TIME_LIMIT`
  time limit for the evaluation. This applies to the time for building the plan in the deterministic case, and to the time for running _all_ simulations
  in the proabilistic case. (default: None)
- `-pln {random,lazy_astar}`, `--planner {random,lazy_astar}`
  the planner to be used for the test (default: random)
- `-ppe`, `--probabilistic-evaluation`
  enable probabilistic evaluation; this is automtically enable in case a probabilistic instance is generated (default: False)
- `--prebuilt-plan DET_PLAN_FILE`
  When this opton is used, the evaluator will process a single, pre-built plan in JSON format. Using this option: 1) overrides plan construction; 2)
  requires to specify and input plan; and 3) is incompatible with probabilistic evaluation (default: None)

## Probabilistic Model

The probabilistic problem variants account for the fact that in the real world flights can deviate from their scheduled arrival times. This process is simulated according to a simplified uncertainty model, which works as follows:

- When a problem instance is generated, we assign to each flight a scheduled arrival time
- When a plan is executed, we simulate the delays

For this reason, all tools designed to work with the probabilistic problem require instances generated with the `-pp` flag. In addition, the PPDDL encoder and the related scikit-decide domain require access to the parameters of the abstracted uncertainty model, which are also built at instance generation time, by passing the command line argument `-pm ppddl`.

Scheduled arrival times are generated as follows:

- For each hour in a day:
  - We sample a number of arrivals according to a Poisson distribution
  - We assign arrival times within the considered hour according to a uniform distribution

The rates for the Poisson distribution depend on the hour of the day and have been calibrated based on real world arrival data. Such rates are available in the file `utils/configuration/hourly_rates.json`. The same distribution is employed to generate all benchmark instances in the competition, including the training instances (provided to all competitors), the validation instances (used to compute metrics when a new submission is made), and the test instances (employed to obtain the final competition ranking).

Delays are generated following a discretized continuous distribution, also calibrated on real-world data. Information on the distribution can be found in the file `utils/configuration/delay_distribution.json`. The same distribution is used to simulate all benchmark instances in the competition.

## Benchmark Distributions

All benchmark instances for the scalability challenges are sampled from the same distribution for the problem generator. This also applies to the probabilistic benchmarks, since the same parameters for the uncertainty model are used in all cases.

In detail, we consider the three main problem generator parameters, i.e.:

* The initial occupancy rate of the rackes (i.e. the `-oc` parameter in the generator)
* The jig type distribution (i.e. the `-t` parameter in the generator)
* The number of flights (i.e. the `-f` parameter in the generator)

In effort to improve coverage of the possible parameter combinations, their values are obtained via Latin Hypercube Sampling, considering the following ranges:

* Three possible occupancy values, i.e. 20, 50, and 80
* The three possible jig type distributions, i.e. 0, 1, and 2
* Values in [0, sqrt(200-3)] for the square root of the number of flights in addition to a minimum (which consists of 3 flights)

The process results in an approximately uniform distribution for the occupancy levels and the jig type distribution. The sampled number of flights are in the range [3..200], with a bias in favor of smaller instance, due to the use of a non-linear scale.
