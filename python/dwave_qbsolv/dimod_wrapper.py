import dimod

from dwave_qbsolv.qbsolv_binding import run_qbsolv, ENERGY_IMPACT, SOLUTION_DIVERSITY

__all__ = ['QBSolv', 'ENERGY_IMPACT', 'SOLUTION_DIVERSITY']


class QBSolv(dimod.core.sampler.Sampler):
    """Wraps the qbsolv C package for python.

    Examples:
        This example uses the tabu search algorithm to solve a small Ising problem.

        >>> h = {0: -1, 1: 1, 2: -1}
        >>> J = {(0, 1): -1, (1, 2): -1}
        >>> response = QBSolv().sample_ising(h, J)
        >>> list(response.samples())
        '[{0: 1, 1: 1, 2: 1}]'
        >>> list(response.energies())
        '[1.0]'
    """
    properties = None
    parameters = None

    def __init__(self):
        self.properties = {}
        self.parameters = {'num_repeats': [],  'seed': [],  'algorithm': [],
                           'verbosity': [],  'timeout': [],  'solver_limit': [],  'solver': [],
                           'target': [],  'find_max': [],  'sample_kwargs': []}

    @dimod.decorators.bqm_index_labels
    def sample(self, bqm, num_repeats=50, seed=None, algorithm=None,
               verbosity=-1, timeout=2592000, solver_limit=None, solver=None,
               target=None, find_max=False, **sample_kwargs):
        """Sample low-energy states defined by a QUBO using qbsolv.

        Note:
            The qbsolv library being shared by all instances of this class is
            non-reentrant and not thread safe. The GIL should not be released
            by this method until that is resolved.

        Note:
            The default build of this library doesn't have the dw library.
            To use solver='dw' this module must be built from source with
            that library.

        The parameter `solver` given to this method has several valid forms:

            - String 'tabu' (default): sub problems are called via an internal call to tabu.
            - String 'dw': sub problems are given to the dw library.
            - Instance of a dimod sampler. The `sample_qubo` method is invoked.
            - Callable that has the signature (qubo: dict, current_best: dict)
              and returns a result list/dictionary with the new solution.

        Args:
            Q (dict): A dictionary defining the QUBO. Should be of the form
                {(u, v): bias} where u, v are variables and bias is numeric.
            num_repeats (int, optional): Determines the number of times to
                repeat the main loop in qbsolv after determining a better
                sample. Default 50.
            seed (int, optional): Random seed. Default generated by random module.
            algorithm (int, optional): Algorithm to use. Default is
                ENERGY_IMPACT. Algorithm numbers can be imported from the module
                under the names ENERGY_IMPACT and SOLUTION_DIVERSITY.
            verbosity (int, optional): Prints more detail about qbsolv's internal
                process as this number increases.
            timeout (float, optional): Number of seconds before routine halts. Default is 2592000.
            solver: Sampling method for qbsolv to use; see method description.
            solver_limit (int, optional): Maximum number of variables in a sub problem.
            target (float, optional): If given, qbsolv halts when
                a state with this energy value or better is discoverd. Default is None.
            find_max (bool, optional): Switches from searching for minimization to
                maximization. Default is False (minimization).

        Returns:
            :obj:`Response`

        Examples:
            This example uses the tabu search algorithm to solve a small QUBO.

            >>> Q = {(0, 0): 1, (1, 1): 1, (0, 1): 1}
            >>> response = QBSolv().sample_qubo(Q)
            >>> list(response.samples())
            '[{0: 0, 1: 0}]'
            >>> list(response.energies())
            '[0.0]'

        """
        if not isinstance(num_repeats, int) or num_repeats <= 0:
            raise ValueError("num_repeats must be a positive integer")

        # pose the QUBO to qbsolv
        Q, offset = bqm.to_qubo()
        samples, energies, counts = run_qbsolv(Q=Q, num_repeats=num_repeats, seed=seed, algorithm=algorithm,
                                               verbosity=verbosity, timeout=timeout, solver_limit=solver_limit,
                                               solver=solver, target=target, find_max=find_max, sample_kwargs=sample_kwargs)

        if hasattr(dimod.Response, 'from_dicts'):
            # dimod<=0.6.x
            response = dimod.Response.from_dicts(samples, {'energy': energies, 'num_occurrences': counts}, dimod.BINARY)
            response.change_vartype(bqm.vartype, {'energy': [offset] * len(energies)})
        else:
            # dimod>=0.7.x
            response = dimod.Response.from_samples(samples, {'energy': energies, 'num_occurrences': counts}, {}, dimod.BINARY)
            response.change_vartype(bqm.vartype, energy_offset=offset)

        return response
