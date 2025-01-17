import copy
import random

from aeon.synthesis.synthesis import se_safe

from aeon.automatic.individual import Individual
from aeon.automatic.utils.utils import treattype
from aeon.automatic.utils.tree_utils import annotate_tree, random_subtree, replace_tree

# Chooses a specific hole that is going to be mutated
def regular_mutation(depth, individual, hole_types):
    
    # Randomly choose the hole
    index_hole = random.choice(range(len(individual.synthesized)))

    # Obtain the hole and context from the individual
    hole = individual.synthesized[index_hole].copy()
    context = individual.contexts[index_hole].copy()

    ## If not annotated, annotate the height to ensure the maximum tree depth
    annotate_tree(hole)

    # Choose the subtree that is getting replaced
    parent, subtree = random_subtree(hole)

    # Synthesize an expression for the mutation
    T = treattype(hole_types[index_hole], parent, subtree)
    mutation = se_safe(context, T, depth - subtree.height)
    
    # Create the offspring by replacing with mutation
    offspring = replace_tree(hole, parent, subtree, mutation) 

    # Update the offspring height, depth and size
    annotate_tree(offspring)

    # Obtain a copy of the Individual contents
    contexts = [ctx.copy() for ctx in individual.contexts]
    synthesized = [expr.copy() for expr in individual.synthesized]
    synthesized[index_hole] = offspring

    return Individual(contexts, synthesized)